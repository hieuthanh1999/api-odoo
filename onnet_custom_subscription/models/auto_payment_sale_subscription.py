# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import datetime
import traceback
import uuid

from datetime import date

from ast import literal_eval
from collections import Counter
from re import sub

from dateutil.relativedelta import relativedelta
from docutils.nodes import line
from markupsafe import Markup
from uuid import uuid4

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import format_date, is_html_empty
from odoo.tools.float_utils import float_is_zero

_logger = logging.getLogger(__name__)

INTERVAL_FACTOR = {
    'daily': 30.0,
    'weekly': 30.0 / 7.0,
    'monthly': 1.0,
    'yearly': 1.0 / 12.0,
}

PERIODS = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    curring_invoice_total = fields.Float("Recurring Next Invoice")
    term_of_sale_subscription = fields.Integer("Term of Sale Subscription")
    id_email_sucess = fields.Many2one('account.move')
    is_automatic_payment = fields.Boolean(string='Automatic Payment', default=False)

    def save_recurring_next_invoice(self):
        """
        Save the curring_invoice_total field
        """
        for index in self:
            index.sudo().write({'curring_invoice_total': index.get_amount_recurring()})

    def remove_automatic(self):
        """
        Review this sale subscription has automatic payment turned off
        """
        self.sudo().write({'is_automatic_payment': False})

    def create_invoice_vive_software(self):
        """
        Process the sales subscription invoice and email the invoice to the customer.
        :returns: invoice
        """
        Invoice = self.env['account.move'].sudo().with_context(move_type='out_invoice')
        invoice_record = self.sudo().with_context(lang=self.partner_id.lang)
        if self.term_of_sale_subscription == 2:
            invoice_values = invoice_record._prepare_invoice()
        else:
            invoice_values = invoice_record._prepare_invoice_vive()
        new_invoice = Invoice.sudo().create(invoice_values)

        new_invoice.sudo().message_post_with_view(
            'mail.message_origin_link',
            values={'self': new_invoice, 'origin': self},
            subtype_id=self.env.ref('mail.mt_note').id)

        if new_invoice.state != 'posted':
            new_invoice.sudo()._post(False)
        #send email invoice
        self.sudo().write({'id_email_sucess': new_invoice.id})
        new_invoice.sudo().write({'sale_subscription_id': self.id})
        return new_invoice

    def start_subscription(self):
        """
        Override Function start and send invoice on start
        :returns: sale_subscription
        """
        sup = super(SaleSubscription, self).start_subscription()
        self.create_invoice_vive_software()
        return sup

    def _prepare_invoice_vive(self):
        """
        Note that the company of the environment will be the one for which the invoice will be created.

        :returns: invoice
        :rtype: dict
        """
        invoice = self._prepare_invoice_data()
        invoice['invoice_line_ids'] = self._prepare_invoice_lines_vive(invoice['fiscal_position_id'])
        return invoice

    def _prepare_invoice_lines_vive(self, fiscal_position):
        """
        Override Function start and send invoice on start
        :returns: sale_subscription
        """
        self.ensure_one()
        revenue_date_start = self.recurring_next_date
        revenue_date_stop = revenue_date_start + relativedelta(
            **{PERIODS[self.recurring_rule_type]: self.recurring_interval}) - relativedelta(days=1)
        return [(0, 0, self._prepare_invoice_line(line, fiscal_position, revenue_date_start, revenue_date_stop)) for
                line in self.recurring_invoice_line_ids]

    @api.model
    def _cron_recurring_create_invoice(self):
        """
        Override the automatic function of sale subscription
        :returns: function automatic
        """
        return self._recurring_create_invoice(automatic=False)

    def generate_recurring_invoice(self):
        res = self._recurring_create_invoices()
        if res:
            return self.action_subscription_invoice()
        else:
            raise UserError("You already have generated an invoice for each period.")

    def automatic_cancelled(self):
        """
        Automatic Cancellled when it's due
        :returns: True
        """
        today_date = datetime.date.today()
        subscriptions = self.search([('stage_category', '=', 'draft')])
        for index in subscriptions:
            end_date = fields.Date.from_string(index.date_unpail)
            day_payment = (today_date - end_date).days
            if day_payment in [0]:
                index.set_cancelled()

        return True

    def set_cancelled(self):
        """
        Set cancelled for sale subscription
        """
        cancelled_id = int(
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.sale_subscription_cancelled'))
        cancelled_stage = self.env['sale.subscription.stage'].sudo().search([('id', '=', cancelled_id)])
        self.sudo().write({'stage_id': cancelled_stage})

    @api.model
    def _automatic_payment(self):
        """Automatic payment when it expires"""
        current_date = datetime.date.today()
        if len(self) > 0:
            subscriptions = self
        else:
            domain = [('recurring_next_date', '=', current_date), ('stage_category', '=', 'progress')]
            domain_dunning = [('stage_category', '=', 'dunning')]
            subscriptions = self.search(domain)
            subscriptions_dunning = self.search(domain_dunning)
        if subscriptions:
            for item in subscriptions:
                end_date = fields.Date.from_string(item.recurring_next_date)
                day_payment = (current_date - end_date).days
                """Check if the expiration of the sale subscription has reached today?"""
                if day_payment in [0]:
                    return item._recurring_create_invoice(automatic=True)
        """if the first payment is not successful"""
        if subscriptions_dunning:
            for item in subscriptions_dunning:
                end_date = fields.Date.from_string(item.recurring_next_date)
                day_payment = (current_date - end_date).days
                """sale subscription will be paid automatically in the next 2, 4 days"""
                if day_payment in [2, 4]:
                    return item._recurring_create_invoice(automatic=True)
                """
                After 6 days of unsuccessful previous payments, the sale subscription will change 
                    to the unpaid status and now we can pay it manually.
                :return: status unpail
                """
                if day_payment in [6]:
                    email_context = self.env.context.copy()
                    email_context.update({
                        'payment_token': item.payment_token_id and item.payment_token_id.name,
                        'renewed': False,
                        'email_to': item.partner_id.email,
                        'code': item.code,
                        'currency': item.pricelist_id.currency_id.name
                    })
                    template = self.env.ref('sale_subscription.email_payment_close')
                    id_email_close = template.with_context(email_context).send_mail(item.id)
                    self.env['mail.mail'].sudo().search([('id', '=', id_email_close)]).send()
                    item.set_automatic()
                    item._create_invoice()
                    return item.set_unpail()

    def _create_invoice(self, automatic=False):
        """
        For non-website payments such as: momo.....
        The function's job is to generate an invoice and a sale order
            for the sale subscription, which will also send an email
        :return: invoice
        """
        auto_commit = self.env.context.get('auto_commit', True)
        cr = self.env.cr
        if len(self) > 0:
            subscription = self
        else:
            pass
        if subscription:
            sub_data = subscription.read(fields=['id', 'company_id'])
            for company_id in set(data['company_id'][0] for data in sub_data):
                sub_ids = [s['id'] for s in sub_data if s['company_id'][0] == company_id]
                subs = self.with_company(company_id).with_context(company_id=company_id).browse(sub_ids)
                Invoice = self.env['account.move'].with_context(move_type='out_invoice',
                                                                company_id=company_id).with_company(company_id)
                # invoice only
                try:
                    # We don't allow to create invoice past the end date of the contract.
                    # The subscription must be renewed in that case
                    invoice_values = subscription.with_context(
                        lang=subscription.partner_id.lang)._prepare_invoice()
                    new_invoice = Invoice.create(invoice_values)
                    order_list = subscription.get_list_order()
                    sale_orders = {
                        'origin': subscription.code,
                        'user_id': 2,
                        'partner_id': subscription.partner_id.id,
                        'date_order': fields.Datetime.now(),
                        'order_line': order_list,
                        'pricelist_id': subscription.pricelist_id.id,
                        'invoice_status': 'no',
                        'access_token': str(uuid.uuid4())
                    }
                    order = self.env['sale.order'].sudo().create(sale_orders)
                    subscription.sudo().write({'order_id': order.id})
                    subscription.set_term_of_sale_subscription()
                    if new_invoice.state != 'posted':
                        new_invoice.sudo()._post(False)
                    subscription.sudo().write({'id_email_sucess': new_invoice.id})
                except Exception:
                    if automatic and auto_commit:
                        cr.rollback()
                        _logger.exception('Fail to create recurring invoice for subscription %s',
                                          subscription.code)
                    else:
                        raise

        return Invoice

    def _create_order(self):
        auto_commit = self.env.context.get('auto_commit', True)
        cr = self.env.cr
        invoices = self.env['account.move']
        current_date = datetime.date.today()
        if len(self) > 0:
            subscription = self
        else:
            pass
        if subscription:
            pass

    def create_invoice_subscription(self, tx):
        sub_data = self.sudo().read(fields=['id', 'company_id'])
        for company_id in set(data['company_id'][0] for data in sub_data):
            Invoice = self.env['account.move'].sudo().with_context(move_type='out_invoice')
            invoice_values = self.sudo().with_context(
                lang=self.partner_id.lang)._prepare_invoice()
            new_invoice = Invoice.sudo().create(invoice_values)

            new_invoice.sudo().message_post_with_view(
                'mail.message_origin_link',
                values={'self': new_invoice, 'origin': self},
                subtype_id=self.env.ref('mail.mt_note').id)

            if new_invoice.state != 'posted':
                new_invoice.sudo()._post(False)
            new_invoice.sudo().write({'payment_state': 'in_payment'})
            id_emai_succes = self.sudo().send_success_mail(tx, new_invoice)
            self.env['mail.mail'].sudo().search([('id', '=', id_emai_succes)]).send()

    def get_list_order(self):
        """
        Function used to return sales subscription data containing subscription plans and add-ons
        :return: dict
        """
        value = []
        for index in self.recurring_invoice_line_ids:
            if index.product_id.product_tmpl_id.is_recurring == True or\
                    (index.product_id.product_tmpl_id.is_subscription_plans == True and index.product_id.product_tmpl_id.is_recurring == False):
                value.append((0, 0, {
                    'product_id': index.product_id.id,
                    'name': index.name,
                    'product_uom_qty': index.quantity,
                    'price_unit': index.price_unit,
                }))
        return value

    def invoice_new(self):
        """
        Delete Add-ons for one-off
        :return: sale subscription
        """
        for index in self.recurring_invoice_line_ids:
            if index.product_id.is_add_ons == True and index.product_id.is_recurring == False:
                index.unlink()
        return self

    def _prepare_invoice_lines(self, fiscal_position):
        """
        Override _prepare_invoice_lines of sale subscription
        :return: dict
        """
        self.ensure_one()
        revenue_date_start = self.recurring_next_date
        revenue_date_stop = revenue_date_start + relativedelta(
            **{PERIODS[self.recurring_rule_type]: self.recurring_interval}) - relativedelta(days=1)
        return [(0, 0, self._prepare_invoice_line(line, fiscal_position, revenue_date_start, revenue_date_stop)) for
                line in self.recurring_invoice_line_ids if (
                            line.product_id.is_add_ons == True and line.product_id.is_recurring == True) or line.product_id.is_subscription_plans == True]

    def _recurring_create_invoice(self, automatic=False):
        """
          Main function of automatic payment:
            handle:
                Check the payment token is valid or not.
                If valid. Make payments and create invoices and send email notification of successful payment,
                    and the state will change to active for cycle 2.
                If the payment fails. status will change to unpaid and an email will be sent so the customer can change the card
        :return: invoice
        """
        auto_commit = self.env.context.get('auto_commit', True)
        cr = self.env.cr
        invoices = self.env['account.move']
        current_date = datetime.date.today()
        if len(self) > 0:
            subscription = self
        else:
            pass
        if subscription:
            sub_data = subscription.read(fields=['id', 'company_id'])
            for company_id in set(data['company_id'][0] for data in sub_data):
                sub_ids = [s['id'] for s in sub_data if s['company_id'][0] == company_id]
                Invoice = self.env['account.move'].with_context(move_type='out_invoice',
                                                                company_id=company_id).with_company(company_id)
                if automatic and auto_commit:
                    cr.commit()

                # payment + invoice (only by cron)
                if subscription.template_id.payment_mode == 'success_payment' and subscription.recurring_total and automatic:
                    try:
                        payment_token = subscription.payment_token_id
                        tx = None
                        if payment_token:
                            invoice_values = subscription.with_context(
                                lang=subscription.partner_id.lang)._prepare_invoice()
                            new_invoice = Invoice.create(invoice_values)
                            if subscription.analytic_account_id or subscription.tag_ids:
                                for line in new_invoice.invoice_line_ids:
                                    if subscription.analytic_account_id:
                                        line.analytic_account_id = subscription.analytic_account_id
                                    if subscription.tag_ids:
                                        line.analytic_tag_ids = subscription.tag_ids
                            new_invoice.message_post_with_view(
                                'mail.message_origin_link',
                                values={'self': new_invoice, 'origin': subscription},
                                subtype_id=self.env.ref('mail.mt_note').id)
                            tx = subscription._do_payment(payment_token, new_invoice)[0]
                            # commit change as soon as we try the payment so we have a trace somewhere
                            if auto_commit:
                                cr.commit()
                            if tx.renewal_allowed:
                                msg_body = _(
                                    'Automatic payment succeeded. Payment reference: <a href=# data-oe-model=payment.transaction data-oe-id=%d>%s</a>; Amount: %s. Invoice <a href=# data-oe-model=account.move data-oe-id=%d>View Invoice</a>.') % (
                                               tx.id, tx.reference, tx.amount, new_invoice.id)
                                subscription.message_post(body=msg_body)
                                # success_payment
                                if new_invoice.state != 'posted':
                                    new_invoice._post(False)
                                new_invoice.sudo().write({'payment_state': 'in_payment'})

                                id_emai_succes = subscription.sudo().send_success_mail(tx, new_invoice)
                                self.env['mail.mail'].sudo().search([('id', '=', id_emai_succes)]).send()
                                subscription.set_active()
                                subscription.set_term_of_sale_subscription()
                                if auto_commit:
                                    cr.commit()
                            else:
                                _logger.error('Fail to create recurring invoice for subscription %s', subscription.code)
                                if auto_commit:
                                    cr.rollback()
                                # Check that the invoice still exists before unlinking. It might already have been deleted by `reconcile_pending_transaction`.
                                new_invoice.exists().unlink()
                        if not payment_token:
                            subscription.send_reminder_to_set_payment()

                        if tx is None or not tx.renewal_allowed:
                            amount = subscription.get_amount_recurring()
                            auto_close_limit = 6
                            date_close = (
                                    subscription.recurring_next_date +
                                    relativedelta(days=auto_close_limit)
                            )
                            close_subscription = current_date >= date_close
                            email_context = self.env.context.copy()
                            email_context.update({
                                'payment_token': subscription.payment_token_id and subscription.payment_token_id.name,
                                'renewed': False,
                                'total_amount': amount,
                                'email_to': subscription.partner_id.email,
                                'code': subscription.code,
                                'currency': subscription.pricelist_id.currency_id.name,
                                'date_end': subscription.date,
                                'date_close': date_close,
                                'auto_close_limit': auto_close_limit
                            })
                            if close_subscription:
                                template = self.env.ref('sale_subscription.email_payment_close')
                                id_email_close = template.with_context(email_context).send_mail(subscription.id)
                                self.env['mail.mail'].sudo().search([('id', '=', id_email_close)]).send()
                                _logger.debug(
                                    "Sending Subscription Closure Mail to %s for subscription %s and closing subscription",
                                    subscription.partner_id.email, subscription.id)
                                msg_body = _(
                                    'Automatic payment failed after multiple attempts. Subscription closed automatically.')
                                subscription.message_post(body=msg_body)
                                subscription.set_unpail()
                            else:
                                subscription.set_dunning()
                                template = self.env.ref('sale_subscription.email_payment_reminder')
                                msg_body = _('Automatic payment failed. Subscription set to "To Dunning".')
                                if (datetime.date.today() - subscription.recurring_next_date).days in [0, 2, 4]:
                                    id_email_failed = template.with_context(email_context).send_mail(subscription.id)
                                    self.env['mail.mail'].sudo().search([('id', '=', id_email_failed)]).send()
                                    _logger.debug(
                                        "Sending Payment Failure Mail to %s for subscription %s and setting subscription to pending",
                                        subscription.partner_id.email, subscription.id)
                                    msg_body += _(' E-mail sent to customer.')
                                subscription.message_post(body=msg_body)
                        if auto_commit:
                            cr.commit()
                    except Exception:
                        if auto_commit:
                            cr.rollback()
                        # we assume that the payment is run only once a day
                        traceback_message = traceback.format_exc()
                        _logger.error(traceback_message)
                        last_tx = self.env['payment.transaction'].search([('reference', 'like', 'SUBSCRIPTION-%s-%s' % (
                        subscription.id, datetime.date.today().strftime('%y%m%d')))], limit=1)
                        error_message = "Error during renewal of subscription %s (%s)" % (subscription.code,
                                                                                          'Payment recorded: %s' % last_tx.reference if last_tx and last_tx.state == 'done' else 'No payment recorded.')
                        _logger.error(error_message)

        return invoices

    def minus_the_trial_fee(self):
        """
        Calculate the total cost of one-off add-ons
        :return: Float
        """
        sum = 0.0
        for index in self.recurring_invoice_line_ids:
            if index.product_id.is_add_ons == True and index.product_id.is_recurring == False:
                sum += index.price_subtotal
        return sum

    def set_dunning(self):
        """
        Change the state to dunning
        """
        dunning_id = int(
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.sale_subscription_dunning'))
        dunning_stage = self.env['sale.subscription.stage'].sudo().search([('id', '=', dunning_id)])
        self.sudo().write({'stage_id': int(dunning_stage), 'check_confirm_payment': False})

    def set_active(self):
        """
        Change the status to active and consider after 1 day we can upgrade/downgrade
        """
        active_id = int(
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.sale_subscription_progress'))
        active_stage = self.env['sale.subscription.stage'].sudo().search([('id', '=', active_id)])
        self.sudo().write({'stage_id': int(active_stage), 'date_upgrade': fields.Datetime.now() + relativedelta(days=1), 'check_confirm_payment': True})

    def set_term_of_sale_subscription(self):
        """
        Marked as period 2 and nth cycles
        """
        self.sudo().write({'term_of_sale_subscription': 2})

    def send_reminder_to_set_payment(self):
        """Send Email reset link instance"""
        template = self.env.ref('onnet_custom_subscription.email_set_payment')
        template.sudo().send_mail(self.id)

    def send_active_succes_payment(self):
        """Send Email reset link instance"""
        template = self.env.ref('sale_subscription.mail_template_subscription_invoice')
        template.sudo().send_mail(self.id)

        return True

    def set_automatic(self):
        """
        mark as automatic payment
        """
        self.sudo().write({'is_automatic_payment': True})

    def set_unpail(self):
        """
        Change the status to unpail and The deadline to close the sale subscription is after 1 month
        """
        draft_id = int(
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.sale_subscription_draft'))
        draft_stage = self.env['sale.subscription.stage'].sudo().search([('id', '=', draft_id)])
        current_date = datetime.date.today() + relativedelta(months=1)
        self.sudo().write({'stage_id': draft_stage, 'date_unpail': current_date})

    def delete_order_line(self):
        """
        delete add-ons belonging to one-off
        """
        for index in self.recurring_invoice_line_ids:
            if index.product_id.is_add_ons == True and index.product_id.is_recurring == False:
                index.unlink()
        return self

    def delete_addons_line(self):
        """
        delete sale subscription line
        """
        for index in self.recurring_invoice_line_ids:
            index.unlink()
        return self