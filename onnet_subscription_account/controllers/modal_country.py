# -*- coding: utf-8 -*-
from werkzeug.exceptions import Forbidden
import logging
import pprint

import odoo
import werkzeug
from odoo import http, fields, _
from dateutil.relativedelta import relativedelta
from odoo.http import request
from datetime import datetime, timedelta
# from odoo.addons.portal.controllers.portal import get_records_pager, pager as portal_pager
import uuid
from markupsafe import Markup



_logger = logging.getLogger(__name__)

class InheritStripePayment(odoo.addons.payment_stripe.controllers.main.StripeController):
    @http.route('/payment/stripe/checkout_return', type='http', auth='public', csrf=False)
    def stripe_return_from_checkout(self, **data):
        # res = super(InheritStripePayment, self).stripe_return_from_checkout(self, **data)
        """ Process the data returned by Stripe after redirection for checkout.

                :param dict data: The GET params appended to the URL in `_stripe_create_checkout_session`
                """
        # Retrieve the tx and acquirer based on the tx reference included in the return url
        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_feedback_data(
            'stripe', data
        )
        acquirer_sudo = tx_sudo.acquirer_id

        # Fetch the PaymentIntent, Charge and PaymentMethod objects from Stripe
        payment_intent = acquirer_sudo._stripe_make_request(
            f'payment_intents/{tx_sudo.stripe_payment_intent}', method='GET'
        )

        _logger.info("received payment_intents response:\n%s", pprint.pformat(payment_intent))
        self._include_payment_intent_in_feedback_data(payment_intent, data)

        # Handle the feedback data crafted with Stripe API objects
        request.env['payment.transaction'].sudo()._handle_feedback_data('stripe', data)

        # Redirect the user to the status page
        if payment_intent.get('status') == 'requires_payment_method':
            request.session['data_buy'] = None
            return request.redirect('/shop/address')
        elif payment_intent.get('status') == 'succeeded':
            return request.redirect('/payment/status')


class ModalAccountInherit(odoo.addons.sale_subscription.controllers.portal.SaleSubscription):

    @http.route(
        ['/my/subscription/<int:subscription_id>',
         '/my/subscription/<int:subscription_id>/<string:access_token>'],
        type='http', methods=['GET'], auth='public', website=True
    )
    def subscription(self, subscription_id, access_token='', message='', message_class='', **kw):
        res = super(ModalAccountInherit, self).subscription(subscription_id, access_token, message, message_class, **kw)
        values = res.qcontext
        countries = request.env['res.country'].sudo().search([])
        langs = request.env['res.lang'].sudo().search([])
        exp_date = values['account'].recurring_next_date.strftime('%B %d, %Y')
        order_line_grade = request.env['sale.order'].sudo().search(
            [('state', '=', 'sale'), ('origin', '=', values['account'].code)], limit=1)
        month_id = int(
            request.env['ir.config_parameter'].sudo().get_param(
                'onnet_custom_subscription.month_product_pricelist'))
        admin_info = request.env.ref('base.partner_admin').sudo()
        list_price = request.env['product.pricelist'].sudo().search([('id', '=', month_id)])

        record_sale = values.get('account').get_product_subscription(status_action='upgrade')
        quantity_plans = values.get('account').get_users(sale_select=1)
        check = True
        for index in values.get('account').recurring_invoice_line_ids:
            if index.product_id.is_recurring == False and index.product_id.is_add_ons == True:
                check = False
                break
        today = datetime.today().strftime('%Y-%m-%d')
        #check extension date
        if str(today) >= str(values.get('account').extension_date):
            check_extension_date = True
        else:
            check_extension_date = False
        # check upgrade/dowgrade
        if str(today) >= str(values.get('account').date_upgrade):
            check_upgrade = True
        else:
            check_upgrade = False
        list_id_industry = values.get('account').industry_management_id.id
        amount_next_invoice = values.get('account').get_amount_recurring()
        max_number_user = request.env['ir.config_parameter'].sudo().get_param(
            'onnet_custom_subscription.max_number_user')
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        data = {
            'base_url': base_url,
            'countries': countries,
            'langs': langs,
            'exp_date': exp_date,
            'pricelist_default': list_price.id,
            'admin_info': admin_info,
            'check_trial': check,
            'quantity_plans': quantity_plans,
            'list_id_industry': list_id_industry,
            'amount_next_invoice': amount_next_invoice,
            'check_extension_date': check_extension_date,
            'max_number_user': max_number_user,
            'check_upgrade': check_upgrade
        }

        if values.get('account').date and str(today) <= str(values.get('account').date):
            data.update({
                'display_edit': False
            })
        else:
            data.update({
                'display_edit': True
            })
        check_login = request.session.uid
        if check_login:
            country_id = request.env['res.users'].browse(check_login).partner_id.country_id.id
            data.update({'country_id': country_id})
        else:
            data.update({'country_id': 999999999})
        if values['account'].stage_category == 'maintenance' or values['account'].stage_category == 'cancel':
            values['display_close'] = False
        else:
            values['display_close'] = True
        values.update(data)
        values.update(record_sale)
        request.session['buy_subscription_id'] = 0
        request.session['buy_industry_id'] = 0
        return http.request.render('sale_subscription.subscription', values)

    @http.route('/buy_pricelist', crsf=False, type='json', auth='public', website=True)
    def get_ajax_pricelist(self, id_sub, stage, id_order, is_pricelist=None):
        if int(id_sub):
            sale_sub = request.env['sale.subscription'].sudo().search(
                [('id', '=', int(id_sub))]).recurring_invoice_line_ids.product_id
        else:
            sale_sub = []
        # get config yeah and month
        annually_id = int(
            request.env['ir.config_parameter'].sudo().get_param(
                'onnet_custom_subscription.annually_product_pricelist'))
        month_id = int(
            request.env['ir.config_parameter'].sudo().get_param(
                'onnet_custom_subscription.month_product_pricelist'))
        list_price = request.env['product.pricelist'].sudo().search([('id', 'in', [month_id, annually_id])])
        selected = month_id
        if is_pricelist:
            selected = int(is_pricelist)
        if int(id_sub) and stage:
            if stage == 'trial' or stage == 'trial_expired':
                values = {
                    'html': request.env.ref('onnet_subscription_account.view_pricelist')._render({
                        'select_price_list': list_price,
                        'selected': selected,
                        'id_sub': id_sub
                    }),
                    'month_id': month_id,
                    'check_active': 1
                }
            else:
                request.session['id_order'] = int(id_order)
                request.session['id_sale_unpaid'] = int(id_sub)
                values = {
                    'check_active': 2
                }
        return values

    @http.route('/add-addons', crsf=False, type='json', auth='public', website=True)
    def get_addons(self, data, is_pricelist):
        list_id_addons = request.env['product.template'].sudo().search([('is_trial', '=', False), ('is_add_ons', '=', True)])
        addons = request.env['product.product'].sudo().search([('product_tmpl_id', '=', list_id_addons.mapped('id'))])
        list_addons = []
        if 'list_addons' in data.keys() and data.get('list_addons') != '':
            list_addons = [int(numeric_string) for numeric_string in data.get('list_addons').split(',')]
        if int(is_pricelist):
            list_price = request.env['product.pricelist'].sudo().search([('id', '=', int(is_pricelist))])

        values = {
            'html': request.env.ref('onnet_subscription_account.view_addons_buy')._render({
                'add_ons': addons,
                'list_addons': list_addons,
                'pricelist': list_price,
            }),
        }
        return values

    @http.route('/data/5', csrf=False, type='json', auth='public', website=True)
    def get_ajax_order(self, id_sub, is_pricelist, list_addons, quantity):
        if int(id_sub):
            sale_sub = request.env['sale.subscription'].sudo().search(
                [('id', '=', int(id_sub))]).recurring_invoice_line_ids.product_id
        else:
            sale_sub = []

        list_addons_ids = []
        list_product_ids = []
        #add subscription in first list
        product_list = request.env['product.product'].sudo().search(
            [('is_subscription_plans', '=', True), ('id', 'in', sale_sub.mapped('id'))])
        quantity_user_old = product_list.quantity_user
        list_product_ids.append(product_list.id)
        if list_addons:
            list_addons_ids = list_addons.split(',')
            list_addons_ids = [int(numeric_string) for numeric_string in list_addons_ids]
            list_product_ids.extend(list_addons_ids)
        list_product_record = request.env['product.product'].sudo().search([('id', 'in', list_addons_ids)])
        #conver list id to string
        mystring = ",".join([str(char) for char in list_product_ids])
        if int(is_pricelist):
            list_price = request.env['product.pricelist'].sudo().search([('id', '=', int(is_pricelist))])
        if int(id_sub):
            values = {
                'html': request.env.ref('onnet_subscription_account.order_view_plans')._render({
                    'product_sale_subscription': product_list,
                    'quantity_user_old': quantity_user_old,
                    'quantity_plans_select': int(quantity),
                    'list_product': list_product_record,
                    'pricelist': list_price,

                }),
                'list_ids': mystring
            }
        return values

    @http.route('/data/6', csrf=False, type='json', auth='public', website=True)
    def get_ajax_andress(self, id_sub, total=None, product_id=None, type=None, quantity=None, credit=None, price_new_one_user=None):
        if int(id_sub):
            account = request.env['sale.subscription'].sudo().search([('id', '=', int(id_sub))])

        countries = request.env['res.country'].sudo().search([])
        langs = request.env['res.lang'].sudo().search([])
        partner_info = request.env.user.partner_id
        country_id = partner_info.country_id['id']
        states = request.env['res.country.state'].search(
            [('country_id', '=', country_id)])
        user_login = request.session.uid
        if user_login == None:
            check_login = False
        else:
            check_login = True
        values = {
            'html': request.env.ref('onnet_subscription_account.andress_order_sub')._render({
                'account': account,
                'countries': countries,
                'states': states,
                'langs': langs,
                'product_id': product_id,
                'price_new_one_user': price_new_one_user,
                'quantity': quantity,
                'type': type,
                'credit': credit,
                'total': total,
                'partner_id': account.partner_id.id,
                'check_login': check_login
            })
        }

        return values

    @http.route('/data/7', csrf=False, type='json', auth='public', website=True)
    def get_ajax_order_view(self, id_sub, data_info, is_pricelist, list_product, quantity_select_plans):
        list_product_session = []
        if list_product:
            list_product_session = list_product.split(',')
            list_product_session = [int(numeric_string) for numeric_string in list_product_session]
        if int(id_sub):
            account = request.env['sale.subscription'].sudo().search([('id', '=', int(id_sub))])
            id_partner_sub = int(account.partner_id.id)
            # Set Stage
            draft_id = request.env['ir.config_parameter'].sudo().get_param(
                'onnet_custom_subscription.sale_subscription_draft')
            draft_order = request.env['sale.subscription.stage'].sudo().search([('id', '=', int(draft_id))])
        if data_info:
            code_country = "+" + data_info.get('code_phone')
            data_partner = {
                'name': data_info.get('name'),
                'email': data_info.get('email'),
                'phone': data_info.get('phone'),
                'code_phone': code_country,
                'company_name': data_info.get('company'),
                'country_id': int(data_info.get('country')),
                'lang': data_info.get('lang'),
            }

        # partner id
        partner_id = self._save_edit_partner(data_partner, id_partner_sub)
        annually_template = int(
            request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.annually_template'))
        month_template = int(
            request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.month_template'))
        # get config yeah and month
        annually_id = int(
            request.env['ir.config_parameter'].sudo().get_param(
                'onnet_custom_subscription.annually_product_pricelist'))
        month_id = int(
            request.env['ir.config_parameter'].sudo().get_param(
                'onnet_custom_subscription.month_product_pricelist'))
        if int(is_pricelist) == annually_id:
            pricelist_id = annually_id
            pricelist_template = annually_template
            recurring_next_date = fields.Datetime.now() + relativedelta(years=1)
        elif int(is_pricelist) == month_id:
            pricelist_id = month_id
            pricelist_template = month_template
            recurring_next_date = fields.Datetime.now() + relativedelta(months=1)

        account.delete_item_line()
        account.add_data_line(list_product_session, pricelist_id, pricelist_template, recurring_next_date, int(quantity_select_plans))
        data_order = account.order_id.add_data_line(list_product_session, pricelist_id, int(quantity_select_plans))
        sale_orders = {
            'origin': account.code,
            'user_id': 2,
            'partner_id': account.partner_id.id,
            'date_order': fields.Datetime.now(),
            'order_line': data_order,
            'pricelist_id': account.pricelist_id.id,
            'invoice_status': 'no',
            'access_token': str(uuid.uuid4())
        }

        order = request.env['sale.order'].sudo().create(sale_orders)
        account.sudo().write({'order_id': order.id, 'extension_date': ''})

        account.save_recurring_next_invoice()
        account.unlink_users_industry()
        record_user = request.env['number.industry'].sudo().search(
            [('industry_management', '=', account.industry_management_id.id), ('res_partner','=', account.partner_id.id)])
        record_user.update_quantity()
        account.set_unpail()

        request.session['id_order'] = int(order.id)

    @http.route('/plans/payment', csrf=False, type='http', auth='public', website=True)
    def customer_payment_order(self, **kw):
        if request.session.get('id_order'):
            order_id = request.session.get('id_order')
        else:
            return request.redirect('/my/home/')
        if order_id:
            order = request.env['sale.order'].sudo().search([('id', '=', int(order_id))])
            if request.session.get('id_sale_unpaid'):
                request.session['session_subscription_redirect'] = int(request.session.get('id_sale_unpaid'))
                request.session['sale_order_id'] = order_id
                request.session['active_firework'] = 1
        render_values = {
            'partner_id': order.partner_id.id,
            'website_sale_order': order,
            'order': order,
            'currency': order.currency_id,
            'amount': order.amount_total,
            'total_price': order.amount_total,
            'access_token': order.access_token,
            'transaction_route': f'/shop/payment/transaction/{order.id}',
            'landing_route': '/shop/payment/validate',
        }
        acquirers_sudo = request.env['payment.acquirer'].sudo().search([('state', 'in', ['enabled', 'test'])])
        render_values.update({
            'acquirers': acquirers_sudo,
            'tokens': request.env['payment.token'].search(
                [('acquirer_id', 'in', acquirers_sudo.ids)])
        })

        return http.request.render('onnet_subscription_account.payment', render_values)

    # function save change partner
    def _save_edit_partner(self, data_chage, partner_id):
        partner_model = request.env['res.partner']
        if partner_id:
            partner_model.browse(partner_id).sudo().write(data_chage)
        return partner_id

    # function save change product template
    def _save_change_sale_subscription(self, data_change, id_sale):
        subscriptions_model = request.env['sale.subscription']
        if id_sale:
            subscriptions_model.browse(id_sale).sudo().write(data_change)

    # function save change product template
    def _save_change_sale_order(self, data_chage, id_order):
        subscriptions_model = request.env['sale.order']
        if id_order:
            subscriptions_model.browse(id_order).sudo().write(data_chage)

    # Change Sale Subscription Line
    def _save_change_sale_line(self, sale_id_line, product_list):
        line_model = request.env['sale.subscription.line']
        for id_line in sale_id_line:
            for id_product in product_list:
                if int(id_line.product_id) == int(id_product.id):
                    if id_product.quantity_user:
                        line_model.browse(int(id_line)).sudo().write({
                            'name': id_product.name,
                            'product_id': id_product.id,
                            'quantity': id_product.quantity_user,
                            'price_unit': id_product.list_price,
                            'uom_id': 1
                        })
                    else:
                        line_model.browse(int(id_line)).sudo().write({
                            'name': id_product.name,
                            'product_id': id_product.id,
                            'quantity': 1,
                            'price_unit': id_product.list_price,
                            'uom_id': 1
                        })
                    break

    def _handling_order_line(self, order_line_id, product_list_order):
        #  created sale order
        model_order_line = request.env['sale.order.line']
        for id_line in order_line_id:
            for id_product in product_list_order:
                if int(id_line.product_id) == int(id_product.id):
                    if id_product.quantity_user:
                        model_order_line.browse(int(id_line)).sudo().write({
                            'product_id': id_product.id,
                            'name': id_product.name,
                            'product_uom_qty': id_product.quantity_user,
                            'price_unit': id_product.list_price,
                        })
                    else:
                        model_order_line.browse(int(id_line)).sudo().write({
                            'product_id': id_product.id,
                            'name': id_product.name,
                            'product_uom_qty': 1,
                            'price_unit': id_product.list_price,
                        })
                    break

    """
    Upgrade/downgrade
    """
    @http.route('/action-upgrade', crsf=False, type='json', auth='public', website=True)
    def action_upgrade(self, order_id, type, list_id_industry):
        record_sale = request.env['sale.subscription'].sudo().search([('id', '=', int(order_id))])
        list_id = [int(numeric_string) for numeric_string in list_id_industry.split(',')]
        list_sale = record_sale.get_product_subscription(status_action=type, industry_list_id=list_id)
        list_sale.update({'type': type})
        values = {
            'html': request.env.ref('onnet_subscription_account.view_upgrade')._render(list_sale)
        }
        return values

    @http.route('/status-subscription', crsf=False, type='json', auth='public', website=True)
    def update_plans(self, data):
        record_sale = request.env['sale.subscription'].sudo().search([('id', '=', int(data.get('order_id')))])
        list_id_industry = data.get('list_id_industry')
        list_id = [int(numeric_string) for numeric_string in list_id_industry.split(',')]
        list_sale = record_sale.get_product_subscription(status_action=data.get('type'),  industry_list_id=list_id)
        values = {
            'html': request.env.ref('onnet_subscription_account.template_subscription_select')._render(list_sale),
            'check': list_sale.get('check')
        }
        return values

    @http.route('/status-users', crsf=False, type='json', auth='public', website=True)
    def update_users(self, data):
        record_sale = request.env['sale.subscription'].sudo().search([('id', '=', int(data.get('order_id')))])
        if data.get('id_sale_select'):
            quantity_min = record_sale.get_users(data.get('id_sale_select'))
        else:
            quantity_min = 0
        if data.get('type') == 'downgrade':
            quantity_max = quantity_min
            quantity = request.env['product.template'].sudo().search(
                [('id', '=', int(data.get('id_sale_select')))]).quantity_user
        else:
            quantity_max = request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.max_number_user')
            quantity = quantity_min

        values = {
            'html': request.env.ref('onnet_subscription_account.template_users_select')._render({
                'quantity_min': quantity_min,
                'quantity_max': quantity_max,
                'quantity': quantity
            }),
        }
        return values

    @http.route('/show-add-ons', crsf=False, type='json', auth='public', website=True)
    def update_addons(self, data):
        sale_id = data.get('sale_id')
        record_sale = request.env['sale.subscription'].sudo().search([('id', '=', int(sale_id))])
        list_addons = []
        pricelist = record_sale.pricelist_id
        if 'list_addons' in data.keys() and data.get('list_addons') != '':
            list_addons = [int(numeric_string) for numeric_string in data.get('list_addons').split(',')]

        if data.get('type') == 'downgrade':
            list_addons = record_sale.id_addons_sale_subscription()
            list_addons_filter = record_sale.filter_addons(data.get('type'))
            mang = ""
            for index in list_addons:
                mang += str(index) + ','
            mang = mang.rstrip(',')
        else:
            list_addons_filter = record_sale.filter_addons()

        values = {
            'html': request.env.ref('onnet_subscription_account.view_addons_upgrade')._render({
                'add_ons': list_addons_filter,
                'list_addons': list_addons,
                'pricelist': pricelist
            })
        }

        if data.get('type') == 'downgrade':
            values.update({
                'list_addons': mang
            })
        return values

    @http.route('/show-bill', crsf=False, type='json', auth='public', website=True)
    def update_bill(self, data):
        sale_id = data.get('sale_id')
        product_subscription = data.get('product_subscription')
        type = data.get('type')
        quanty = int(data.get('quanty'))
        list_addons = data.get('list_addons')

        record_sale = request.env['sale.subscription'].sudo().search([('id', '=', int(sale_id))])
        products_plan = request.env['product.template'].sudo().search([('id', '=', int(product_subscription))])
        pricelist = record_sale.pricelist_id
        if bool(list_addons.strip()):
            list_addons_ids = [int(numeric_string) for numeric_string in list_addons.split(',')]
        else:
            list_addons_ids = []
        if len(list_addons_ids):
            product_addons = request.env['product.product'].sudo().search([('id', 'in', list_addons_ids)])
        else:
            product_addons = []
        value = record_sale.price_subscription(quanty, products_plan, type)
        value.update({
            'list_addons': product_addons,
            'pricelist': pricelist
        })
        values = {
            'html': request.env.ref('onnet_subscription_account.order_view_upgrade')._render(value),
            'price_update': value.get('remaining_plans_days_price')

        }
        return values

    @http.route('/show-confirm-info', crsf=False, type='json', auth='public', website=True)
    def update_partner(self, id_sale):
        if int(id_sale):
            account = request.env['sale.subscription'].sudo().search([('id', '=', int(id_sale))])

        countries = request.env['res.country'].sudo().search([])
        langs = request.env['res.lang'].sudo().search([])
        partner_info = request.env.user.partner_id
        country_id = partner_info.country_id['id']
        states = request.env['res.country.state'].search(
            [('country_id', '=', country_id)])

        user_login = request.session.uid
        if user_login == None:
            check_login = False
        else:
            check_login = True
        values = {
            'html': request.env.ref('onnet_subscription_account.andress_order_sub')._render({
                'account': account,
                'countries': countries,
                'states': states,
                'langs': langs,
                'check_login': check_login
            })
        }
        return values

    @http.route('/create-order', crsf=False, type='json', auth='public', website=True)
    def create_order(self, data):
        if data:
            data_partner = data.get('data_partner')
            sale_id = data.get('order_id')
            list_addons_id = data.get('list_addons_buy')
            price_update_plans = data.get('price_update_plans')
            product_plans_selected = data.get('product_id')
            quanty_selected = data.get('quanty')

            record_sale = request.env['sale.subscription'].sudo().search([('id', '=', int(sale_id))])
            record_plans = request.env['product.template'].sudo().search([('id', '=', int(product_plans_selected))])
            product_new = request.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', int(record_plans.id))], limit=1)
            if bool(list_addons_id.strip()):
                list_addons_ids = [int(numeric_string) for numeric_string in list_addons_id.split(',')]
            else:
                list_addons_ids = []
            product_addons = request.env['product.product'].sudo().search([('id', 'in', list_addons_ids)])

            # fomrmat name
            lang = request.env['res.lang'].sudo().search([('code', '=', record_sale.partner_invoice_id.lang)])
            format_date = request.env['ir.qweb.field.date'].with_context(lang=lang).value_to_html

            name = record_plans.name + _(" Invoicing period") + ": %s - %s" % (
                format_date(fields.Date.from_string(datetime.today()), {}), format_date(fields.Date.from_string(record_sale.recurring_next_date), {}))
            value = record_sale.price_subscription(quanty_selected, record_plans, data.get('type'))
            if data['type'] == 'upgrade':
                # get id product credit refund of order
                credit_name = _("Credit Invoicing period") + ": %s - %s" % (format_date(fields.Date.from_string(datetime.today()), {}),format_date(fields.Date.from_string(record_sale.recurring_next_date), {}))
                credit_id = int(request.env['ir.config_parameter'].sudo().get_param(
                    'onnet_custom_subscription.user_product_subscription'))
                product_credit = request.env['product.product'].sudo().search(
                    [('product_tmpl_id', '=', int(credit_id))], limit=1)

                order_lines = [(0, 0, {
                    'product_id': product_new.id,
                    'name': name,
                    'product_uom_qty': quanty_selected,
                    'price_unit': value.get('selected_plans_days_price')/value.get('quantity'),
                    'subscription_id': int(sale_id),
                }), (0, 0, {
                    'product_id': product_credit.id,
                    'name': credit_name,
                    'product_uom_qty': 1,
                    'price_unit': float(price_update_plans) * -1,
                    'subscription_id': int(sale_id),
                })]
                note_order = 'upsell'
                request.session['active_upgrade'] = 1
            else:
                note_order = 'renew'
                order_lines = [(0, 0, {
                    'product_id': record_plans.id,
                    'name': name,
                    'product_uom_qty': quanty_selected,
                    'price_unit': value.get('pricelist_plans'),
                    'subscription_id': int(sale_id),
                })]

            for line in product_addons:
                price_pro = line.list_price
                if line.is_recurring == True:
                    pricelist_plan_addon = line.product_tmpl_id._get_combination_info(False, int(line.id or 0), 1,
                                                                      request.env['product.pricelist'].browse(
                                                                          int(record_sale.pricelist_id.id)))
                    price_pro = pricelist_plan_addon['list_price']

                order_lines.append((0, 0, {
                    'product_id': line.id,
                    'name': line.name,
                    'product_uom_qty': 1,
                    'price_unit': price_pro,
                }))
            self._checkout_update_partner_save(data_partner)
            sale_orders = {
                'origin': record_sale.code,
                'user_id': 2,
                'partner_id': record_sale.partner_id.id,
                'pricelist_id': record_sale.pricelist_id.id,
                'date_order': fields.Datetime.now(),
                'order_line': order_lines,
                'invoice_status': 'no',
                'subscription_management': note_order,
                'access_token': str(uuid.uuid4())
            }
            #  created sale order
            order_new = request.env['sale.order'].sudo().create(sale_orders)
            request.session['session_subscription_redirect'] = int(sale_id)
            request.session['sale_order_id'] = order_new.id
            request.session['active_firework'] = 1
            if order_new:
                request.session['id_order'] = order_new.id
                values = {
                    'check': True,
                    'order_id': order_new.id,
                    'type': data['type'],
                    # 'messeger': msg
                }
                if data.get('type') == 'downgrade':
                    template_id = request.env.ref('onnet_customer_signup.sale_subscription_to_downgrading').id
                    self._send_email(template_id, record_sale, 'downgrade')
            else:
                values = {
                    'check': False
                }
        return values

    @http.route('/downgrade-plans', crsf=False, type='json', auth='public', website=True)
    def downgrade_order(self, data):
        if data:
            data_partner = data.get('data_partner')
            sale_id = data.get('order_id')
            list_addons_id = data.get('list_addons_buy')
            product_plans_selected = data.get('product_id')
            quanty_selected = data.get('quanty')

            record_sale = request.env['sale.subscription'].sudo().search([('id', '=', int(sale_id))])
            record_plans = request.env['product.template'].sudo().search([('id', '=', int(product_plans_selected))])
            product_id = request.env['product.product'].sudo().search([('product_tmpl_id', '=', int(product_plans_selected))], limit=1)

            add_addon_line_ids = []
            pricelist_plan_addon = record_plans._get_combination_info(False, int(product_id or 0), 1,
                                                                              record_sale.pricelist_id)
            add_addon_line_ids.append((0, 0, {
                'name': product_id.name,
                'product_id': product_id.id,
                'quantity': int(quanty_selected),
                'price_unit': pricelist_plan_addon['price'],
                'uom_id': product_id.uom_id.id,
            }))
            line_ids = []
            if list_addons_id:
                line_ids = list_addons_id.split(',')
                line_ids = [int(numeric_string) for numeric_string in line_ids]

            product_addon = request.env['product.product'].sudo().search([('id', 'in', line_ids)])
            for item in product_addon:
                pricelist_plan_addon = item.product_tmpl_id._get_combination_info(False, int(item.id or 0), 1,
                                                                                  record_sale.pricelist_id)
                price_pro = pricelist_plan_addon['price']
                add_addon_line_ids.append((0, 0, {
                    'name': item.name,
                    'product_id': item.id,
                    'quantity': 1,
                    'price_unit': price_pro,
                    'uom_id': item.uom_id.id,
                }))
            self._checkout_update_partner_save(data_partner)
            # get list addon recurring old in order
            plan_old = ''
            list_ids_old =[]
            for index in record_sale.recurring_invoice_line_ids:
                test = index.product_id.id not in line_ids
                if test and index.product_id.is_subscription_plans == True:
                    plan_old = index.product_id.name
                if test and index.product_id.is_recurring == True:
                    list_ids_old.append(index.product_id.id)
                if index.product_id.is_add_ons == True and index.product_id.is_recurring == False:
                    add_addon_line_ids.append((0, 0, {
                        'name': index.product_id.name,
                        'product_id': index.product_id.id,
                        'quantity': 1,
                        'price_unit': index.product_id.list_price,
                        'uom_id': index.product_id.uom_id.id,
                    }))
            record_sale.delete_recurring_invoice_line_ids()
            record_sale.replace_plans_lines(add_addon_line_ids)
            record_sale.write(
                {'date': record_sale.recurring_next_date})
        # send email dowgrade
        template_id = request.env.ref('onnet_customer_signup.sale_subscription_to_downgrading').id
        self._send_email(template_id, record_sale, 'downgrade', plan_old, list_ids_old)
        values = {
            'html': request.env.ref('onnet_subscription_account.view_done')._render({
            })
        }
        return values

    @http.route(['/my/subscription/<int:account_id>/cancel'], type='http', methods=["POST"], auth="public",
                website=True)
    def cancel_account(self, account_id, token=None, **kw):
        account = request.env['sale.subscription'].sudo().browse(account_id)
        cancel_reason = request.env['sale.subscription.close.reason'].browse(int(kw.get('close_reason_id')))
        account.close_reason_id = cancel_reason
        if kw.get('closing_text'):
            account.message_post(body=_('Cancel text: %s', kw.get('closing_text')))
        if kw.get('is_extra_maintenance') == 'extend':
            extend_id = int(request.env['ir.config_parameter'].sudo().get_param(
                'onnet_custom_subscription.user_product_extend'))

            product_pro = request.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', int(extend_id))], limit=1)
            product_pro_price = product_pro.list_price
            exp_date = fields.Date.from_string(account.recurring_next_date)
            exp_date_cancel = fields.Date.from_string(account.recurring_next_date + relativedelta(months=1))
            format_date = request.env['ir.qweb.field.date'].with_context().value_to_html
            name = product_pro.name + _(" Invoicing period") + ": %s - %s" % (
                format_date(exp_date, {}), format_date(exp_date_cancel, {}))
            order_lines = [(0, 0, {
                'product_id': product_pro.id,
                'name': name,
                'product_uom_qty': 1,
                'price_unit': product_pro_price,
                'subscription_id': int(account_id),
            })]
            sale_orders = {
                'origin': account.code,
                'user_id': 2,
                'partner_id': account.partner_id.id,
                'pricelist_id': account.pricelist_id.id,
                'date_order': fields.Datetime.now(),
                'validity_date': exp_date_cancel,
                'order_line': order_lines,
                'amount_total': product_pro_price,
                'subscription_management': 'extend',
                'access_token': str(uuid.uuid4())
            }
            # created sale order
            order_new = request.env['sale.order'].sudo().create(sale_orders)
            # update Expiration day in subscription order
            request.session['session_subscription_redirect'] = account.id
            request.session['id_order'] = order_new.id
            request.session['active_firework'] = 1
            request.session['active_extra_maintenance'] = 1
            url = '/plans/payment'
            return request.redirect(url)
        else:
            self.set_cancel(account)
            url = '/my/subscription/%s/%s ' % (account_id, token)
            template_id = request.env.ref('onnet_customer_signup.sale_subscription_to_canceling').id
            self._send_email(template_id, account, 'cancel')
            return request.redirect('/my/subscription/%s/%s ' % (account_id, token))
        return request.redirect(url)

    def set_cancel(self, account):
        today = fields.Date.from_string(datetime.today())
        stage = request.env['sale.subscription.stage'].sudo().search(
            [('category', '=', 'cancel'), ('sequence', '>=', account.stage_id.sequence)], limit=1)
        if not stage:
            stage = request.env['sale.subscription.stage'].search([('category', '=', 'cancel')], limit=1)
        values = {'stage_id': stage.id, 'to_renew': False}
        if account.recurring_rule_boundary == 'unlimited' or not account.date or today < account.date:
            values['date'] = account.recurring_next_date
        account.write(values)
        return True

    def _send_email(self, template_id, subsctiption, type, plan_old=None, list_ids_old=None):
        template = request.env['mail.template'].sudo().browse(template_id)
        if template:
            receipt_list = subsctiption.partner_id.email
            body = template.body_html
            Addon_old = ''
            if type == 'cancel':
                order = request.env['sale.order'].sudo().search(
                    [('id', '=', subsctiption.order_id.id)], limit=1)
            else:
                order = request.env['sale.order'].sudo().search(
                    [('state', '=', 'draft'), ('origin', '=', subsctiption.code)], limit=1)
                if list_ids_old:
                    AddOnOlds = request.env['product.product'].sudo().search([('id', 'in', list_ids_old)])
                    for item in AddOnOlds:
                        Addon_old += ','+ item.name
                    if Addon_old !='':
                        Addon_old = _("You have also selected to end the add-on Integration with ") + "%s on %s" % (Addon_old, subsctiption.recurring_next_date.strftime('%B %d, %Y'))

            ProductName = (subsctiption.recurring_invoice_line_ids)[0].name
            row = subsctiption.detail_order_html(subsctiption).get('row')
            body = body.replace("--code--", str(subsctiption.code) or "")
            body = body.replace("--row--", row or "")
            body = body.replace("--name--", str(subsctiption.partner_id.name) or "")
            body = body.replace("--ProductName--", str(ProductName) or "")
            body = body.replace("--today--", str(datetime.today().strftime('%B %d, %Y')) or "")
            body = body.replace("--date--", str(datetime.today().strftime('%B %d, %Y')) or "")
            body = body.replace("--next_date--", str(subsctiption.recurring_next_date.strftime('%B %d, %Y')) or "")
            body = body.replace("--subtotal--", str("{:,.2f}".format(subsctiption.recurring_total)) or "")
            body = body.replace("--taxes--", str("{:,.2f}".format(subsctiption.recurring_tax)) or "")
            body = body.replace("--amount--", str("{:,.2f}".format(subsctiption.recurring_total_incl)) or "")
            body = body.replace("--currency--", str(subsctiption.currency_id.name) or "")
            logo = _("/logo.png?company=") + "%s" % (request.env.user.company_id.id)
            body = body.replace("--logo--", logo)
            body = body.replace("--ProductNameOld--", str(plan_old) or "")
            body = body.replace("--AddOnOld--", str(Addon_old) or "")

            body = body.replace('--company_name--', str(request.env.user.company_id.name))
            body = body.replace('--company_street--', str(request.env.user.company_id.street))
            body = body.replace('--company_email--', str(request.env.user.company_id.email))
            body = body.replace('--company_phone--', str(request.env.user.company_id.phone))
            body = body.replace('--company_website--', str(request.env.user.company_id.website))
            body = body.replace('--base_url--',
                                str(request.env['ir.config_parameter'].sudo().get_param('web.base.url')))

            mail_values = {
                'subject': template.subject,
                'body_html': body,
                'email_to': receipt_list
            }
            request.env['mail.mail'].sudo().create(mail_values).send()

    def _checkout_update_partner_save(self, data):
        if request.env.user.partner_id.id:
            partner_id = int(request.env.user.partner_id.id)
            mode = ('edit', 'billing')
        code_phone = "+" + data['code_country']
        post = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'code_phone': code_phone,
            'company_name': data['company'],
            'country_id': int(data['country']),
            'zip': data['reg_zipcode'],
            'street': data['reg_street'],
            'lang': data['lang'],
        }
        all_values = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'code_phone': code_phone,
            'company_name': data['company'],
            'country_id': int(data['country']),
            'zip': data['reg_zipcode'],
            'street': data['reg_street'],
            'lang': data['lang'],
            'submitted': '1',
            'partner_id': partner_id,
            'callback': '',
            'field_required': 'phone,name'
        }
        if data['reg_state'] != '':
            post.update({
                'state_id': int(data['reg_state'])
            })
            all_values.update({
                'state_id': int(data['reg_state'])
            })
        # update info partner
        self._checkout_form_save(mode, post, all_values)

    def _checkout_form_save(self, mode, checkout, all_values):
        Partner = request.env['res.partner']
        if mode[0] == 'new':
            partner_id = Partner.sudo().with_context(tracking_disable=True).create(checkout).id
        elif mode[0] == 'edit':
            partner_id = int(all_values.get('partner_id', 0))
            if partner_id:
                Partner.browse(partner_id).sudo().write(checkout)
        return partner_id