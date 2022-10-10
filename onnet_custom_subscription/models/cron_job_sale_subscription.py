# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import random
import datetime
# from turtle import update
from re import sub

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, exceptions, _
from odoo.http import request
import os
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
import datetime
import traceback

from ast import literal_eval
from collections import Counter
from dateutil.relativedelta import relativedelta
from markupsafe import Markup
from uuid import uuid4

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_repr, float_round

# from odoo.odoo.addons.test_impex.tests.test_load import values

_logger = logging.getLogger(__name__)

class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    token = fields.Char("Access Token", required=True)
    sale_expiration = fields.Datetime(copy=False)
    sale_valid = fields.Boolean(compute='_compute_sale_valid', string='Sale Token is Valid')
    sale_url = fields.Char(string='Signup URL')
    date_unpail = fields.Date(string='Date Unpail')
    extension_date = fields.Date(string='Extension date')
    date_upgrade = fields.Date(string='Upgrade/Downgrade Date')

    def get_today(self):
        return fields.Date.from_string(datetime.today())

    @api.depends('token', 'sale_expiration')
    def _compute_sale_valid(self):
        dt = datetime.datetime.now() + timedelta(days=1)
        for sale, sale_sudo in zip(self, self.sudo()):
            sale.sale_valid = bool(sale_sudo.token) and \
                              (not sale_sudo.sale_expiration or dt <= sale_sudo.sale_expiration)

    @api.model
    def create(self, vals):
        # render code by random
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        token = ''.join(random.SystemRandom().choice(chars) for _ in range(20))
        # update sale_subscription
        vals.update({'token': token, 'term_of_sale_subscription': 1})
        sub = super(SaleSubscription, self).create(vals)

        return sub

    @api.model
    def _sale_retrieve(self, token, check_validity=False, raise_exception=False):
        """ find the partner corresponding to a token, and possibly check its validity
            :param token: the token to resolve
            :param check_validity: if True, also check validity
            :param raise_exception: if True, raise exception instead of returning False
            :return: partner (browse record) or False (if raise_exception is False)
        """
        sale = self.search([('token', '=', token)], limit=1)
        if not sale:
            if raise_exception:
                raise exceptions.UserError(_("Sale token '%s' is not valid", token))
            return False
        if check_validity and not self.sale_valid:
            if raise_exception:
                raise exceptions.UserError(_("Sale token '%s' is no longer valid", token))
            return False
        return sale

    def sale_prepare(self, expiration=False):
        """ generate a new token for the partners with the given validity, if necessary
            :param expiration: the expiration datetime of the token (string, optional)
        """
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        token_random = ''.join(random.SystemRandom().choice(chars) for _ in range(20))
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for sale in self:
            if expiration or not sale.sale_valid:
                token = token_random
                while self._sale_retrieve(token):
                    token = token_random
                sale.write({
                    'token': token,
                    'sale_expiration': expiration,
                    'sale_url': str(base_url + '/active-instance?sale_id=' + str(sale.id) + '&part_id=' + str(
                        sale.partner_id.id) + '&token=' + str(token))
                })
        return True

    def get_current_date(self):
        """
        Get recurring date
        :return: date
        """
        template = request.env['ir.config_parameter'].sudo()
        annually_template = int(template.get_param('onnet_custom_subscription.annually_template'))
        if self.template_id.id == annually_template:
            recurring_next_date = fields.Datetime.now() + relativedelta(years=1)
        else:
            recurring_next_date = fields.Datetime.now() + relativedelta(months=1)

        return recurring_next_date

    def _change_status_trial_expired(self):
        """Automatic change the stage when it expires"""
        today = datetime.date.today()
        list_sub = self.env['sale.subscription'].sudo().search(
            [('stage_category', '=', 'trial'), ('recurring_next_date', '=', today)])
        id_trial_expired = int(request.env['ir.config_parameter'].sudo().get_param(
            'onnet_custom_subscription.sale_subscription_trial_expired'))
        if not id_trial_expired:
            raise exceptions.ValidationError(_('You need to select Expired Trial in settings'))
        else:
            days = int(request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.extension_date'))
            days_trial = today + timedelta(days=days)
            for record in list_sub:
                record.sudo().write({'stage_category': 'trial_expired', 'stage_id': id_trial_expired, 'extension_date': days_trial})

    def send_active_email_token(self):
        """Send Email reset link instance"""
        email_context = self.env.context.copy()

        # update context
        email_context.update({
        })

        template = self.env.ref('onnet_custom_subscription.email_active_token')
        template.with_context(email_context).sudo().send_mail(self.id)
        return True

    def get_subscription_information(self):
        sub_users_count = 0
        allowed_modules = []
        package_name = ''
        for line in self.recurring_invoice_line_ids:
            if line.product_id.product_tmpl_id.is_subscription_plans:
                sub_users_count += line.quantity
                allowed_modules.extend(line.product_id.mapped('tab_module.modules.technical_name'))
                package_name = line.product_id.name
        sub_data = {
            'allowed_active_users': int(sub_users_count),
            'allowed_modules': allowed_modules,
            'expiration_date': self.recurring_next_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
            'subscription_code': self.code,
            'subscription_stage': self.stage_id.category,
            'package_name': package_name
        }
        return sub_data

    def _cron_send_email(self):
        """
        Automatic Send Email
        Send email to notify customers when the payment due date is coming after 1 3 5 7 days
        """
        current_date = datetime.date.today()
        list_sub = self.env['sale.subscription'].sudo().search([('stage_category', '=', 'progress')])
        template_id = self.env.ref('onnet_custom_subscription.email_dunning_payment_views_template').id
        for item in list_sub:
            end_date = fields.Date.from_string(item.recurring_next_date)
            day_payment = (end_date - current_date).days
            if day_payment in [1, 3, 5, 7]:
                self._cron_send(template_id, item.partner_id.email, item.partner_id.name, item)
            elif day_payment == 0:
                template_id = self.env.ref('onnet_customer_signup.sale_subscription_to_renewal').id
                self._cron_send_mail(template_id, item.partner_id.email, item.partner_id.name, item)

    def _cron_send(self, template_id, email_tos, name, item):
        template = self.env['mail.template'].sudo().browse(template_id)
        email_tox = email_tos
        body = template.body_html
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        body = body.replace("--name--", str(name) or "")
        body = body.replace("--email--", str(email_tox) or "")
        body = body.replace("--link--", str(base_url + '/my/subscription/' + str(item.id) + '/' + str(item.uuid)) or "")
        body = body.replace("--code--", str(item.code) or "")
        body = body.replace("--recurring_price--", str(item.recurring_total) or "")
        body = body.replace("--next_billing_date--", str(item.recurring_next_date) or "")

        body = body.replace('--company_name--', str(request.env.user.company_id.name))
        body = body.replace('--company_street--', str(request.env.user.company_id.street))
        body = body.replace('--company_email--', str(request.env.user.company_id.email))
        body = body.replace('--company_phone--', str(request.env.user.company_id.phone))
        body = body.replace('--company_website--', str(request.env.user.company_id.website))
        body = body.replace('--base_url--', str(request.env['ir.config_parameter'].sudo().get_param('web.base.url')))
        logo = _("/logo.png?company=") + "%s" % (request.env.user.company_id.id)
        body = body.replace("--logo--", logo)

        mail_values = {
            'subject': template.subject,
            'body_html': body,
            'email_to': email_tox
        }
        self.env['mail.mail'].sudo().create(mail_values).send()

    def _cron_send_mail(self, template_id, email_tos, name, item):
        template = self.env['mail.template'].sudo().browse(template_id)
        email_tox = email_tos
        body = template.body_html
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        ProductName = (item.recurring_invoice_line_ids)[0].name
        row = self.detail_order_html(item).get('row')
        body = body.replace("--row--", row or "")
        body = body.replace("--name--", str(name) or "")
        body = body.replace("--ProductName--", str(ProductName) or "")
        body = body.replace("--email--", str(email_tox) or "")
        body = body.replace("--subtotal--", str("{:,.2f}".format(item.recurring_total)) or "")
        body = body.replace("--taxes--", str("{:,.2f}".format(item.recurring_tax)) or "")
        body = body.replace("--amount--", str("{:,.2f}".format(item.recurring_total_incl)) or "")
        body = body.replace("--currency--", str(item.currency_id.name) or "")
        body = body.replace("--link--", str(base_url + '/my/subscription/' + str(item.id) + '/' + str(item.uuid)) or "")
        body = body.replace("--code--", str(item.code) or "")
        body = body.replace("--recurring_price--", str(item.recurring_total) or "")
        body = body.replace("--next_billing_date--", str(item.recurring_next_date) or "")

        body = body.replace('--company_name--', str(request.env.user.company_id.name))
        body = body.replace('--company_street--', str(request.env.user.company_id.street))
        body = body.replace('--company_email--', str(request.env.user.company_id.email))
        body = body.replace('--company_phone--', str(request.env.user.company_id.phone))
        body = body.replace('--company_website--', str(request.env.user.company_id.website))
        body = body.replace('--base_url--', str(request.env['ir.config_parameter'].sudo().get_param('web.base.url')))
        logo = _("/logo.png?company=") + "%s" % (request.env.user.company_id.id)
        body = body.replace("--logo--", logo)

        mail_values = {
            'subject': template.subject,
            'body_html': body,
            'email_to': email_tox
        }
        self.env['mail.mail'].sudo().create(mail_values).send()

    def detail_order_html(self, item):
        texts = ''
        texts += Markup('<tr><td colspan="5" style="background: #E0FFFF;">Recurring</td></tr>')
        check = True
        i = 1
        total_next_bill = 0
        for index in item.recurring_invoice_line_ids:
            if (index.product_id.is_recurring == True and index.product_id.is_add_ons == True and index.product_id.is_trial == False) or index.product_id.is_subscription_plans == True:
                texts += Markup('<tr style="text-align:center;">') + Markup('<td style="padding:10px;">') \
                         + str(i) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str(index.name) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str(index.quantity) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str("{:,.2f}".format(index.price_unit)) + ' ' + str(index.currency_id.name) + Markup(
                    '</td>') + Markup('<td style="padding:10px;">') \
                         + str("{:,.2f}".format(index.price_subtotal)) + ' ' + str(index.currency_id.name) + Markup(
                    '</td></tr>')
                total_next_bill += index.price_subtotal
                i += 1
            if index.product_id.is_recurring == False and index.product_id.is_add_ons == True:
                check = False
                break

        if check == False:
            texts += Markup('<tr><td colspan="5" style="background: #E9D7FE;color:#7D4DFC;font-weight:600;">One-off</td></tr>')
            for index in item.recurring_invoice_line_ids:
                if index.product_id.is_recurring == False and index.product_id.is_add_ons == True:
                    texts += Markup('<tr style="text-align:center;">') + Markup('<td style="padding:10px;">') \
                             + str(i) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                             + str(index.name) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                             + str(index.quantity) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                             + str("{:,.2f}".format(index.price_unit)) + ' ' + str(index.currency_id.name) + Markup(
                        '</td>') + Markup('<td style="padding:10px;">') \
                             + str("{:,.2f}".format(index.price_subtotal)) + ' ' + str(index.currency_id.name) + Markup(
                        '</td></tr>')
                i += 1
        values ={
            'total': total_next_bill,
            'row': texts
        }
        return values

    def _cron_auto_change_status_sub(self):
        """
        consider closing the sale subscription when it's due
            Cancel
            maintenance
            trial_expired
        """
        today = fields.Datetime.now().strftime('%Y-%m-%d')
        # list order subscription cancel (Non-renewing) to closed
        list_sub_cancel = self.env['sale.subscription'].sudo().search([('stage_category', '=', 'cancel'), '|', ('recurring_next_date', '<=', today), ('date', '<=', today)])
        stage_closed = int(
            request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.sale_subscription_closed'))
        for item in list_sub_cancel:
            order_non_renewing = self.env['sale.order'].search([('order_line.subscription_id', 'in', item.ids)])
            for item_order in order_non_renewing:
                if item_order.state == 'draft':
                    item_order.browse(item_order.id).sudo().write({
                        'state': 'cancel'
                    })
            item.browse(item.id).sudo().write({
                'stage_category': 'closed',
                'stage_id': stage_closed
            })

        # list order subscription maintenance to closed
        list_sub_maintenance = self.env['sale.subscription'].sudo().search(
            [('stage_category', '=', 'maintenance'),  '|', ('recurring_next_date', '<=', today), ('date', '<=', today)])
        for item in list_sub_maintenance:
            order_maintenances = self.env['sale.order'].search([('order_line.subscription_id', 'in', item.ids)])
            for item_order in order_maintenances:
                if item_order.state == 'draft':
                    item_order.browse(item_order.id).sudo().write({
                        'state': 'cancel'
                    })
            item.browse(item.id).sudo().write({
                'stage_category': 'closed',
                'stage_id': stage_closed
            })
        # update order subscription trial to trial expired
        stage_trial_expired = int(request.env['ir.config_parameter'].sudo().get_param(
            'onnet_custom_subscription.sale_subscription_trial_expired'))
        list_sub_trial = self.env['sale.subscription'].sudo().search(
            [('stage_category', '=', 'trial'), ('recurring_next_date', '<=', today)])
        for item2 in list_sub_trial:
            # trial order
            order_trials = self.env['sale.order'].sudo().search([('id', '=', item2.order_id.id)], limit=1)
            if order_trials.state == 'draft':
                item2.order_id.browse(item2.order_id.id).sudo().write({
                    'state': 'cancel'
                })
            item2.browse(item2.id).sudo().write({
                'stage_category': 'trial_expired',
                'stage_id': stage_trial_expired
            })

    def change_item(self, item, sale_order):
        # update order subscription Next Invoice 'upsell'
        list_order_line_new = self.get_list_order_new(sale_order, item.id)
        list_order_line_old = self.get_list_order_new(item.order_id, item.id)
        # Change item first list
        list_order_line_old[0] = list_order_line_new[0]
        # Delete sale subscription line item
        self.delete_sale_line(item)
        # update sale subscription line item
        item.browse(item.id).sudo().write({
            'recurring_invoice_line_ids': list_order_line_old
        })

    def get_list_order_new(self, new_order, id_sale):
        sale_line_item_new = []
        for line in new_order.order_line:
            sale_line_item_new.append((0, 0, {
                'name': line.name,
                'product_id': line.product_id.id,
                'analytic_account_id': int(id_sale),
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
                'uom_id': 1
            }))
        return sale_line_item_new

    def delete_sale_line(self, sale_sub):
        """
        Delete sale subscription line of sale subscription
        """
        if sale_sub:
            for link in sale_sub.recurring_invoice_line_ids:
                link.unlink()

    def delete_recurring_invoice_line_ids(self):
        """
        Delete sale subscription line of sale subscription
        """
        for link in self.recurring_invoice_line_ids:
            link.unlink()

    def get_price_plans(self):
        """
        Get price subscription plans
        """
        for index in self.recurring_invoice_line_ids:
            if index.product_id.is_subscription_plans == True:
                price = index.price_subtotal
            else:
                break
        return price

    def get_name_plans(self):
        """
        Get name subscription plans
        """
        for index in self.recurring_invoice_line_ids:
            if index.product_id.is_subscription_plans == True:
                record = index
            else:
                break
        return record

    def get_list_industry(self):
        """
        Get industry subscription plans
        """
        for index in self.recurring_invoice_line_ids.product_id:
            if index.is_subscription_plans == True:
                record = index.industry.ids
            else:
                break
        return ",".join([str(element) for element in record])

    def get_product_subscription(self, status_action=False, industry_list_id=False):
        """
        Handler Upgrade/Downgrade
        param: status_action (upgrade/downgrade)
        param: industry_list_id list industry

        return dict
        """
        for index in self.recurring_invoice_line_ids.product_id.product_tmpl_id:
            if index.is_subscription_plans == True:
                record_now = index
            else:
                break

        industry_list = self.env['industry.management'].sudo().search([('id', 'in', industry_list_id)])

        domain_upgrade = [('id', '!=', record_now.id), ('list_price', '>', record_now.list_price),
                          ('is_subscription_plans', '=', True) , ('industry', '=', industry_list.mapped('id'))]
        domain_downgrade = [('id', '!=', record_now.id), ('list_price', '<', record_now.list_price),
                            ('is_subscription_plans', '=', True) , ('industry', '=', industry_list.mapped('id'))]
        if status_action == 'upgrade':
            status = 'upgrade'
            product_list = self.env['product.template'].sudo().search(domain_upgrade)
        elif status_action == 'downgrade':
            status = 'downgrade'
            product_list = self.env['product.template'].sudo().search(domain_downgrade)
        else:
            pass

        if product_list and status == 'upgrade':
            values = {
                'list_product': product_list,
                'status': 'upgrade',
                'check': True
            }
        elif not product_list and status == 'upgrade':
            values = {
                'status': 'upgrade',
                'check': False
            }
        if product_list and status == 'downgrade':
            values = {
                'list_product': product_list,
                'status': 'downgrade',
                'check': True
            }
        elif not product_list and status == 'downgrade':
            values = {
                'status': 'downgrade',
                'check': False
            }
        return values

    def get_users(self, sale_select):
        """Get max user"""
        sale_record = self.env['product.template'].sudo().search([('id', '=', int(sale_select))]).quantity_user

        for index in self.recurring_invoice_line_ids:
            if index.product_id.is_subscription_plans == True:
                record_now = index.quantity
            else:
                break

        return max(int(sale_record), int(record_now))

    def id_addons_sale_subscription(self):
        """
        Filter Add-ons sale subscription
        """
        list_ids = []
        for index in self.recurring_invoice_line_ids.product_id:
            if index.is_add_ons == True:
                list_ids.append(index.id)
            else:
                continue
        return list_ids

    def id_addons_not_recurring_sale_subscription(self):
        """
        Filter Add-ons sale subscription
        """
        list_ids = []
        for index in self.recurring_invoice_line_ids.product_id:
            if index.is_add_ons == True and index.is_recurring == True:
                list_ids.append(index.id)
            else:
                continue
        return list_ids

    def filter_addons(self, type=None):
        """
        Filter Add-ons
        """

        if type == 'downgrade':
            list_addons_old = self.id_addons_sale_subscription()
            list_addons_filter = self.env['product.product'].sudo().search(
                [('id', 'in', list_addons_old), ('is_recurring', '=', True), ('is_trial', '=', False)])
        else:
            list_addons_recurring = self.id_addons_not_recurring_sale_subscription()
            list_addons_filter = self.env['product.product'].sudo().search(
                [('id', 'not in', list_addons_recurring), ('is_add_ons', '=', True), ('is_trial', '=', False)])
        return list_addons_filter

    def get_days(self):
        """
        Get the date from today to a certain time
       """
        # today = fields.Date.from_string(datetime.today())
        today = fields.Date.from_string(fields.Date.today())
        recurring_date = fields.Date.from_string(self.recurring_next_date)
        if recurring_date > today:
            return (recurring_date - today).days
        else:
            return 0

    def get_days_between_start_and_end(self):
        """
        Get day year or month
        """
        recurring_date = fields.Date.from_string(self.recurring_next_date)
        start_date = fields.Date.from_string(self.date_start)
        return (recurring_date - start_date).days

    def price_subscription(self, quantity, record_plans, type):
        """
        'quantity': quanty selected
        'record_plans': product record
        'type': type [upgrade, downgrade]
        """
        price_plans_selected = record_plans.get_price_with_price_list(self.pricelist_id, quantity)
        today = fields.Date.from_string(fields.Date.today())

        monthly_billing_period = int(
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.monthly_billing_period'))
        yearly_billing_period = int(
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.yearly_billing_period'))

        annually_template = int(
            request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.annually_template'))
        # days_year = self.get_days_between_start_and_end()
        remaining_days = self.get_days()

        if self.template_id.id == annually_template:
            days_year = yearly_billing_period
        else:
            days_year = monthly_billing_period
        # price in 1 day of order
        price_days_invoice_line = self.get_price_plans() / days_year
        price_days_plans_selected = (price_plans_selected * int(quantity)) / days_year
        # price total not use yet
        remaining_plans_days_price = remaining_days * price_days_invoice_line
        # price total new order
        selected_plans_days_price = remaining_days * price_days_plans_selected
        values = {
            'quantity': int(quantity),
            'type': type,
            'today': today.strftime('%B %d, %Y'),
            'price_list_id': self.pricelist_id,
            'next_billing_date': self.recurring_next_date.strftime('%B %d, %Y'),
            'product_plans': record_plans,
            'selected_plans_days_price': selected_plans_days_price,
            'plans_old': self.get_name_plans(),
            'remaining_plans_days_price': remaining_plans_days_price,
            'pricelist_plans': price_plans_selected,
        }
        if type == 'upgrade':
            total_price = round(selected_plans_days_price - remaining_plans_days_price, 3)
            msg = _("Upgrade - Invoicing period from") + ": %s - %s" % (
            today.strftime('%B %d,%Y'), self.recurring_next_date.strftime('%B %d, %Y'))
            values.update({
                'msg': msg,
            })
        else:
            msg = _("Downgrade - Invoicing for next billing period from") + ": %s " % (
                self.recurring_next_date.strftime('%B %d, %Y'))
            values.update({
                'msg': msg,
            })
        return values

    def replace_plans_lines(self, data_subscription=False):
        """ data subscription plans product
        'name': product name
        'product_id': product record
        'quantity': product quanty
        'price_unit': product price apply price list
        'uom_id': uom id product
        """
        self.sudo().write({'recurring_invoice_line_ids': data_subscription })

    def add_plans_lines(self, data_subscription=False):
        """ data subscription plans product
        'name': product name
        'product_id': product record
        'quantity': product quanty
        'price_unit': product price apply price list
        'uom_id': uom id product
        """
        for index in self.recurring_invoice_line_ids:
            if index.product_id.is_subscription_plans == True:
                index.sudo().write(data_subscription)
            else:
                break

    def delete_items_lines(self, id_plans=False):
        """
        'id_plans': id product plans product product
        """
        for index in self.recurring_invoice_line_ids:
            if index.product_id.is_subscription_plans == True and index.product_id.id != int(id_plans):
                index.unlink()

    def add_addons_lines(self, data_addons=False):
        """ data addons product
        'name': product name
        'product_id': product record
        'quantity': product quanty
        'price_unit': product price apply price list
        'uom_id': uom id product
        """
        return self.sudo().write({
            'recurring_invoice_line_ids': data_addons
        })

    def get_amount_recurring(self):
        """
        Get amount add-ons recurring
        """
        amount = 0
        for index in self.recurring_invoice_line_ids:
            if index.product_id.is_recurring == True or index.product_id.is_subscription_plans == True:
                amount += index.price_subtotal

        return round(amount,2)

    def send_activation_email(self):
        try:
            """ create signup token for each user, and send their signup url by email """
            if self.env.context.get('install_mode', False):
                return
            self._send_email_active()
            for user in self.partner_id.user_ids:
                msg_body = _("Active instance email sent for email <%s>", user.email)
                self.message_post(body=msg_body)
        except Exception as e:
            _logger.info(str(e))

    def unlink_users_industry(self):
        """
        Delete users.industry
        """
        try:
            for index in self:
                index.env['users.industry'].sudo().search([('sale_subscription', '=', index.id)]).unlink()
        except Exception as e:
            _logger.info(str(e))

    def _send_email_active(self):
        """ Create send email.
           :param record partner_id
           :param int subscription_order_id
        """
        #email template
        email_id_trial = request.env.ref('onnet_custom_subscription.patient_card_email_active_trial_template').id
        email_id_buy = request.env.ref('onnet_custom_subscription.patient_card_email_active_template').id
        days = int(request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.extension_date'))
        # get config
        trial_template = int(request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.trial_template'))
        if self.template_id.id == int(trial_template):
            days = int(request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.trial_period'))
            email_subjects = 'Get started with your %s days trial now!' % str(days)
            template_id = email_id_trial
        else:
            email_subjects = 'Thank you for your successful new subscription and welcome onboard!'
            template_id = email_id_buy

        template = request.env['mail.template'].sudo().browse(template_id)
        partner = self.partner_id
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        email_from = 'VIVE Software'

        if template:
            receipt_list = partner.email
            email_subject = email_subjects
            body = template.body_html
            body = body.replace("--name--", str(partner.name) or "")
            body = body.replace("--email--", str(partner.email) or "")
            body = body.replace("--url_object--",  str(base_url + '/active-instance?sale_id=' + str(self.id) + '&part_id=' + str(partner.id) + '&token=' + str(self.token)) or "")

            logo = _("/logo.png?company=") + "%s" % (request.env.user.company_id.id)
            body = body.replace("--logo--", logo)
            body = body.replace('--company_name--', str(request.env.user.company_id.name))
            body = body.replace('--company_street--', str(request.env.user.company_id.street))
            body = body.replace('--company_email--', str(request.env.user.company_id.email))
            body = body.replace('--company_phone--', str(request.env.user.company_id.phone))
            body = body.replace('--company_website--', str(request.env.user.company_id.website))


            mail_values = {
                'subject': email_subject,
                'body_html': body,
                'email_from': email_from,
                'email_to': receipt_list
            }

            request.env['mail.mail'].sudo().create(mail_values).send()
            self.sale_prepare(expiration=fields.Datetime.now() + relativedelta(days=1))
