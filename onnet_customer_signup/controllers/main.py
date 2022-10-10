# -*- coding: utf-8 -*-
import datetime

from requests import request

from odoo import http, fields, _, Command, SUPERUSER_ID
from odoo.http import request
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.account.controllers import portal
from collections import OrderedDict

import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from werkzeug.urls import url_encode, url_decode, iri_to_uri

db_monodb = http.db_monodb

from dateutil.relativedelta import relativedelta
import logging
from datetime import timedelta
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from odoo.addons.payment.controllers.portal import PaymentPortal
from odoo.exceptions import UserError, ValidationError
from odoo.addons.portal.controllers.portal import CustomerPortal
_logger = logging.getLogger(__name__)

# product_template = request.env['product.template'].sudo()
# users_industry = request.env['users.industry'].sudo()
# product_pricelist = request.env['product.pricelist'].sudo()
# config_parameter = request.env['ir.config_parameter'].sudo()
# res_users = request.env['res.users'].sudo()
# res_partner = request.env['res.partner'].sudo()
# super_admin = request.env['res.users'].sudo().browse(SUPERUSER_ID)
# product_product = request.env['product.product'].sudo()
# product_template = request.env['product.template'].with_user(super_admin)


class PaymentPortalInherit(PaymentPortal):
    def _create_transaction(
            self, payment_option_id, reference_prefix, amount, currency_id, partner_id, flow,
            tokenization_requested, landing_route, is_validation=False, invoice_id=None,
            custom_create_values=None, **kwargs
    ):
        # Prepare create values
        if flow in ['redirect', 'direct']:  # Direct payment or payment with redirection
            acquirer_sudo = request.env['payment.acquirer'].sudo().browse(payment_option_id)
            token_id = None
            tokenization_required_or_requested = acquirer_sudo._is_tokenization_required(
                provider=acquirer_sudo.provider, **kwargs
            ) or tokenization_requested
            tokenize = True
        elif flow == 'token':  # Payment by token
            token = request.env['payment.token'].browse(payment_option_id)
            acquirer_sudo = token.acquirer_id.sudo()
            token_id = payment_option_id
            tokenize = False
        else:
            raise UserError(
                _("The payment should either be direct, with redirection, or made by a token.")
            )

        if invoice_id:
            if custom_create_values is None:
                custom_create_values = {}
            custom_create_values['invoice_ids'] = [Command.set([int(invoice_id)])]

        reference = request.env['payment.transaction']._compute_reference(
            acquirer_sudo.provider,
            prefix=reference_prefix,
            **(custom_create_values or {}),
            **kwargs
        )
        if is_validation:  # Acquirers determine the amount and currency in validation operations
            amount = acquirer_sudo._get_validation_amount()
            currency_id = acquirer_sudo._get_validation_currency().id

        # Create the transaction
        tx_sudo = request.env['payment.transaction'].sudo().create({
            'acquirer_id': acquirer_sudo.id,
            'reference': reference,
            'amount': amount,
            'currency_id': currency_id,
            'partner_id': partner_id,
            'token_id': token_id,
            'operation': f'online_{flow}' if not is_validation else 'validation',
            'tokenize': tokenize,
            'landing_route': landing_route,
            **(custom_create_values or {}),
        })  # In sudo mode to allow writing on callback fields

        if flow == 'token':
            tx_sudo._send_payment_request()  # Payments by token process transactions immediately
        else:
            tx_sudo._log_sent_message()

        # Monitor the transaction to make it available in the portal
        PaymentPostProcessing.monitor_transactions(tx_sudo)

        return tx_sudo


class Plans(http.Controller):

    @http.route('/check-industry-plans', auth='public', type='json', website=True)
    def check_industry(self, industry, plan, pricelist_id, trial):
        try:
            value = {}
            if request.env.user.id == request.env.ref('base.public_user').id:
                value.update({
                    'check': 1
                })
            else:
                check_user = request.env['users.industry'].sudo().check_industry_in_res_partner(int(industry), request.env.user.id)
                if check_user == False:
                    value.update({
                        'check': 1
                    })
                else:
                    value.update({
                        'check': 2
                    })

            return value
        except:
            return request.redirect('/')

    @http.route('/pricing-plans', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def customer_pricing_plans(self, **kw):
        """ When you click buy, the url will point to this router:
           :param industry_id: <int> id model Industry Management
           :param plans_id: <int> id model Product Template
           :param pricelist_id: <int> id model PriceList
        """
        try:
            if kw.get('data'):
                request.session['data_buy'] = kw.get('data')
                return True
            else:
                return False
        except:
            return request.redirect('/')

    @http.route('/shop/add-ons', type='http', auth='public', website=True, csrf=False)
    def index_addons(self, **kw):
        try:
            data = request.session['data_buy']
            values = self.step_addons(data)
            if data == None:
                return request.redirect('/plans/')
            else:
                if data.get('action') == 'back':
                    values.update({'num_users': data.get('num_users')})
                    values['product_order'] = data.get('list_addons')

                return http.request.render('onnet_customer_signup.layout', values)
        except:
            return request.redirect('/')

    def step_addons(self, data, back=None):
        try:
            if data:
                industry_id = int(data.get('industry'))
                plans_id = int(data.get('plans'))
                pricelist_id = int(data.get('pricelist_id'))
                action = data.get('action')

                trial = 2
                pricelist = request.env['product.pricelist'].sudo().browse(pricelist_id)
                plan_template = request.env['product.template'].sudo().search([('id', '=', plans_id)])
                addons = request.env['product.template'].sudo().search([('is_trial', '=', False), ('is_add_ons', '=', True)])

                if data.get('trial') and int(data.get('trial')) == 1:
                    trial = data.get('trial')
                    addons = request.env['product.template'].sudo().search([('is_trial', '=', True), ('is_add_ons', '=', True)])
                max_number_user = request.env['ir.config_parameter'].sudo().get_param(
                    'onnet_custom_subscription.max_number_user')
                values = {
                    'content_layout': 'add-ons',
                    'industry_id': industry_id,
                    'pricelist': pricelist,
                    'product': plan_template,
                    'trial': int(trial),
                    'add_ons': addons,
                    'max_number_user': max_number_user,
                    'action': action,
                }
                if data.get('num_users'):
                    values.update({'num_users': data.get('num_users')})
                if data.get('list_addons'):
                    values.update({'product_order': data.get('list_addons')})
                else:
                    values.update({'product_order': []})
                check_login = request.session.uid
                if check_login:
                    country_id = request.env['res.users'].browse(check_login).partner_id.country_id.id
                    values.update({'country_id': country_id})
                else:
                    values.update({'country_id': 999999999})

                return values
        except:
            return request.redirect('/')

    # get - peicelist - plan
    @http.route('/plans/get-pricelist-plan', csrf=False, type='json', auth='public', website=True)
    def detail_sale_order(self, data):
        try:
            trial = data['trial']
            product_id = data['product_id']
            msg = ''
            if data['numUser'] == '':
                numUser = 0
            else:
                numUser = int(data['numUser'])

            pricelist = request.env['product.pricelist'].browse(int(data['pricelist_id']))
            max_number_user = int(
                request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.max_number_user'))
            if numUser >= max_number_user:
                msg = _("The maximum number of users is ") + " %s" % (max_number_user)
                numUser = max_number_user

            if product_id:
                products_plan = request.env['product.template'].sudo().search([('id', '=', product_id)], limit=1)
                if products_plan.quantity_user >= numUser:
                    numUser = products_plan.quantity_user
                    msg = _("The minimum number of users is ") + " %s" % (numUser)
                product_pro_price = products_plan.list_price * numUser
                price_plans_selected = products_plan.get_price_with_price_list(pricelist, 1)
                if price_plans_selected:
                    product_pro_price = price_plans_selected * numUser
            if trial == '1':
                product_pro_price = 0
            values = {
                'total_price': product_pro_price,
                'numUser': numUser,
                'trial': int(trial),
                'msg': msg,
            }
            return values
        except:
            return request.redirect('/')

    @http.route('/plans/show-add-on', csrf=False, type='json', auth='public', website=True)
    def show_addon_template_ajax(self, data):
        try:
            data_addons = self.get_addons(data, step='addons')
            pricelist = request.env['product.pricelist'].browse(int(data['pricelist']))
            data_addons.update({
                'pricelist': pricelist,
            })
            if data_addons:
                values = {
                    'html': request.env.ref('onnet_customer_signup.view_addons_summary')._render(data_addons)
                }
            return values
        except:
            return request.redirect('/')

    def get_addons(self, data, step=None):
        try:
            addons_recurring = request.env['product.template'].sudo().search(
                [('is_recurring', '=', True), ('is_add_ons', '=', True), ('id', 'in', data.get('list_addons'))])
            addons = request.env['product.template'].sudo().search(
                [('is_recurring', '=', False), ('is_add_ons', '=', True), ('id', 'in', data.get('list_addons'))])
            values = {}

            if addons or addons_recurring:
                if step == 'addons':
                    values.update({
                        'addons_recurring': addons_recurring,
                        'add_ons': addons,
                        'trial': int(data.get('trial')),
                    })
                if step == 'address':
                    values.update({
                        'addons_recurring': addons_recurring,
                        'addons_no_recurring': addons,
                        'trial': int(data.get('trial')),

                    })

            return values
        except:
            return request.redirect('/')

    @http.route('/view-address', csrf=False, type='json', auth='public', website=True)
    def click_view(self, **kw):
        try:
            data = request.session['data_buy']
            if kw and data:
                list_addons = kw.get('data').get('list_addons')
                if list_addons:
                    line_ids = [int(numeric_string) for numeric_string in list_addons.split(',')]
                    kw.get('data')['list_addons'] = line_ids
                else:
                    kw.get('data')['list_addons'] = []
                merge_data = dict(data, **(kw.get('data')))
                request.session['data_buy'] = merge_data
                return True
            else:
                return False
        except:
            return request.redirect('/')

    @http.route('/shop/address', csrf=False, type='http', auth='public', website=True)
    def index_adress(self, **kw):
        try:
            data = request.session.get('data_buy')
            if data.get('partner_id') != 4 and data.get('subscription_id') and data.get('order_id') and data.get('action') == 'back':
                values = self.step_addons(data)
                # render template summer
                data_addons = self.get_addons(data, step='address')
                values.update(data_addons)

                partner_id = data.get('partner_id')
                subscription_id = data.get('subscription_id')
                order_id = data.get('order_id')

                sale_subcription = request.env['sale.subscription'].sudo().browse(subscription_id)
                sale_order = request.env['sale.order'].sudo().browse(order_id)
                partner_info = request.env['res.partner'].sudo().browse(partner_id)

                country_id = partner_info.country_id['id']
                states = request.env['res.country.state'].search([('country_id', '=', country_id)])

                countries = request.env['res.country'].sudo().search([])

                langs = request.env['res.lang'].sudo().search([])
                setting_domain = request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.config_domain')
                domain = sale_subcription.website.replace('.hiiboss.com', '')

                user_login = request.session.uid
                if user_login == None:
                    check_login = False
                    check_state = False
                else:
                    state = request.env['res.users'].sudo().search([('id', '=', user_login)]).partner_id.state_id
                    check_login = True
                    if state:
                        check_state = True
                    else:
                        check_state = False
                values.update({
                        'content_layout': 'address',
                        'trial': int(data.get('trial')),
                        'num_users': int(data.get('num_users')),
                        'countries': countries,
                        'states': states,
                        'langs': langs,
                        'checkout': partner_info,
                        'partner_id': partner_id,
                        'setting_domain': setting_domain,
                        'domain': domain,
                        'check_login': check_login,
                        'country_id': country_id,
                        'check_state': check_state
                })
                return http.request.render('onnet_customer_signup.layout', values)
            else:
                values = self.step_addons(data)
                # render template summer
                data_addons = self.get_addons(data, step='address')
                values.update(data_addons)

                countries = request.env['res.country'].sudo().search([])

                langs = request.env['res.lang'].sudo().search([])

                if request.env.user.partner_id.id:
                    partner_id = int(request.env.user.partner_id.id)
                    partner_info = request.env.user.partner_id
                    country_id = partner_info.country_id['id']
                    states = request.env['res.country.state'].search([('country_id', '=', country_id)])
                else:
                    partner_id = int(-1)
                    partner_info = []
                    states = request.env['res.country.state'].sudo().search([])
                setting_domain = request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.config_domain')
                domain = ""


                user_login = request.session.uid
                if user_login == None:
                    check_login = False
                    check_state = False
                else:
                    state = request.env['res.users'].sudo().search([('id', '=', user_login)]).partner_id.state_id
                    check_login = True
                    if state:
                        check_state = True
                    else:
                        check_state = False

                values.update({
                        'content_layout': 'address',
                        'trial': int(data.get('trial')),
                        'num_users': int(data.get('num_users')),
                        'countries': countries,
                        'states': states,
                        'langs': langs,
                        'checkout': partner_info,
                        'partner_id': partner_id,
                        'setting_domain': setting_domain,
                        'domain': domain,
                        'check_login': check_login,
                        'check_state': check_state,
                        'country_id': country_id
                })

                return http.request.render('onnet_customer_signup.layout', values)
        except:
            return request.redirect('/')

    @http.route('/view-payment', csrf=False, type='json', auth='public', website=True)
    def click_view_payment(self, data):
        try:
            data_session = request.session['data_buy']
            trial = int(data_session.get('trial'))
            reg_name = data.get('reg_name')
            reg_email = data.get('reg_email')
            reg_phone = data.get('reg_phone')
            reg_company_name = data.get('reg_company_name')
            reg_country = int(data.get('reg_country'))
            reg_language_id = data.get('reg_language_id')
            reg_domain = data.get('reg_domain')
            product_order = data_session.get('list_addons')
            product_id = int(data_session.get('plans'))
            number_user = int(data_session.get('num_users'))
            reg_industry = int(data_session.get('industry'))
            code_country = data.get('code_country')
            reg_state = data.get('reg_state')
            zipcode = data.get('zipcode')
            reg_street = data.get('reg_street')
            order_id = None
            pricelist_id = int(data_session.get('pricelist_id'))

            pricelist = request.env['product.pricelist'].browse(pricelist_id)

            # phone_new = reg_phone.lstrip("+" + code_country)
            code_country = "+" + code_country

            if data and data.get('check_back') == 'new':
                # Payment

                #Check if the client already exists
                if request.env.user.partner_id.id:
                    partner_id = int(request.env.user.partner_id.id)
                    mode = ('edit', 'billing')
                if partner_id == 4:
                    mode = ('new', 'billing')

                post = {
                    'email': reg_email,
                    'code_phone': code_country,
                    'phone': reg_phone,
                    'country_id': reg_country,
                    'zip': zipcode,
                    'street': reg_street,
                    'lang': reg_language_id,
                }
                all_values = {
                    'email': reg_email,
                    'phone': reg_phone,
                    'code_phone': code_country,
                    'country_id': reg_country,
                    'zip': zipcode,
                    'street': reg_street,
                    'lang': reg_language_id,
                    'website': reg_domain,
                    'submitted': '1',
                    'partner_id': partner_id,
                    'callback': '',
                    'field_required': 'phone,name'
                }

                user_login = request.session.uid
                if user_login == None:
                    post.update({
                        'name': reg_name,
                        'company_name': reg_company_name,
                    })
                    all_values.update({
                        'name': reg_name,
                        'company_name': reg_phone,
                    })
                else:
                    pass

                if reg_state and reg_state != '':
                    post.update({
                        'state_id': int(reg_state)
                    })
                    all_values.update({
                        'state_id': int(reg_state)
                    })
                line_ids = product_order
                # create sale order
                order_lines = []
                invoice_lines = []
                # Stage
                trial_id = int(
                    request.env['ir.config_parameter'].sudo().get_param(
                        'onnet_custom_subscription.sale_subscription_trial'))
                draft_id = int(
                    request.env['ir.config_parameter'].sudo().get_param(
                        'onnet_custom_subscription.sale_subscription_draft'))
                if int(trial) == 1:
                    id_stage = trial_id
                else:
                    id_stage = draft_id
                products_plan = request.env['product.template'].sudo().search([('id', '=', product_id)])
                request.session['buy_subscription_id'] = product_id
                request.session['buy_industry_id'] = reg_industry
                if products_plan:
                    product_pro = request.env['product.product'].sudo().search([('product_tmpl_id', '=', products_plan.id)],
                                                                               limit=1)
                    price_plan = product_pro.list_price
                    pricelist_plan = products_plan._get_combination_info(False, int(product_pro.id or 0), int(number_user),
                                                                         pricelist)
                    if int(trial) == 1:
                        price_plan = 0
                    else:
                        if pricelist_plan['list_price']:
                            price_plan = pricelist_plan['list_price']
                    if product_pro:
                        order_lines.append((0, 0, {
                            'product_id': product_pro.id,
                            'name': product_pro.name,
                            'product_uom_qty': int(number_user),
                            'price_unit': price_plan,
                        }))
                        invoice_lines.append((0, 0, {
                            'name': product_pro.name,
                            'product_id': product_pro.id,
                            'quantity': int(number_user),
                            'price_unit': price_plan,
                            'uom_id': product_pro.uom_id.id,
                        }))
                list_products = request.env['product.template'].sudo().search([('id', 'in', line_ids)])
                for line in list_products:
                    product_addon = request.env['product.product'].sudo().search([('product_tmpl_id', '=', line.id)],
                                                                                 limit=1)
                    price_pro = product_addon.list_price
                    if line.is_recurring == True:
                        pricelist_plan_addon = line._get_combination_info(False, int(product_addon.id or 0), 1, pricelist)
                        price_pro = pricelist_plan_addon['list_price']

                    if int(trial) == 1:
                        price_pro = 0
                    if product_addon:
                        order_lines.append((0, 0, {
                            'product_id': product_addon.id,
                            'name': product_addon.name,
                            'product_uom_qty': 1,
                            'price_unit': price_pro,
                        }))
                        invoice_lines.append((0, 0, {
                            'name': product_addon.name,
                            'product_id': product_addon.id,
                            'quantity': 1,
                            'price_unit': price_pro,
                            'uom_id': product_pro.uom_id.id,
                        }))

                partner_id = self._checkout_form_save(mode, post, all_values)
                partner_check = request.env['res.users'].sudo().search([('partner_id', '=', partner_id)])
                partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)])
                if not partner_check:
                    user_new = request.env['res.users'].sudo().with_context(no_reset_password=True).create({
                        'active': True,
                        'login': partner.email,
                        'partner_id': partner.id
                    })
                    partner.signup_prepare(signup_type="reset")
                    user_ids = user_new.id
                else:
                    user_ids = partner_check.id
                request.session['partner_id_session'] = partner_id
                sale_orders = {
                    'user_id': 2,
                    'partner_id': partner_id,
                    'date_order': fields.Datetime.now(),
                    'order_line': order_lines,
                    'pricelist_id': pricelist.id,
                }
                #  id template
                annually_template = int(
                    request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.annually_template'))
                month_template = int(
                    request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.month_template'))
                trial_template = int(
                    request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.trial_template'))
                annually_id = int(
                    request.env['ir.config_parameter'].sudo().get_param(
                        'onnet_custom_subscription.annually_product_pricelist'))
                seting_domain = request.env['ir.config_parameter'].sudo().get_param(
                    'onnet_custom_subscription.config_domain')

                date_start = fields.Datetime.now()
                if pricelist.id == annually_id:
                    recurring_next_date = fields.Datetime.now() + relativedelta(years=1)
                    template_id = annually_template
                else:
                    recurring_next_date = fields.Datetime.now() + relativedelta(months=1)
                    template_id = month_template
                if int(trial) == 1:
                    template_id = trial_template
                    days = int(
                        request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.trial_period'))
                    recurring_next_date = fields.Datetime.now() + relativedelta(days=days)
                #  created sale order
                if order_id:
                    order = request.env['sale.order'].sudo().search([('id', '=', int(order_id))])
                    # delete order line
                    order.delete_item_line()
                    # update order line
                    order.sudo().write({
                        'order_line': order_lines
                    })
                else:
                    order = request.env['sale.order'].sudo().create(sale_orders)

                current_date = fields.Datetime.now() + relativedelta(months=1)
                domain = reg_domain + '.' + seting_domain
                industry_plans = request.env['industry.management'].sudo().search([('id', '=', int(reg_industry))])

                if int(trial) == 1:
                    subscription_order = request.env['sale.subscription'].sudo().create({
                        'name': 'Subscription book',
                        'partner_id': partner_id,
                        'pricelist_id': pricelist.id,
                        'template_id': template_id,
                        'date_start': date_start,
                        'recurring_next_date': recurring_next_date,
                        'stage_id': id_stage,
                        'order_id': '',
                        'website': domain,
                        'user_id': 2,
                        'is_check_trial': False,
                        'recurring_invoice_line_ids': invoice_lines,
                        'term_of_sale_subscription': 1,
                        'industry_management_id': industry_plans.id,
                    })
                    subscription_order.save_recurring_next_invoice()
                    request.session['subscription_order'] = subscription_order.id
                    request.env['users.industry'].sudo().create({
                        'res_user': user_ids,
                        'industry_management': int(reg_industry),
                        'sale_subscription': subscription_order.id,
                        'res_partner': partner_id
                    })
                    id_language = request.env['res.lang'].sudo().search([('code', '=', reg_language_id)])
                    lead_line = self.save_lead_line(int(reg_industry), line_ids, int(product_id))
                    request.env['crm.lead'].sudo().create({
                        'name': reg_name,
                        'contact_name': reg_name,
                        'partner_name': reg_company_name,
                        'email_from': reg_email,
                        'phone': reg_phone,
                        'lang_id': int(id_language),
                        'country_id': int(reg_country),
                        'lead_line': lead_line
                    })
                    values = {
                        'trial': int(trial),
                        'id_plans': product_id
                    }
                    return values
                else:
                    if order_id:
                        request.session['subscription_order'] = order_id
                        # delete subscription line
                        subscription_order = request.env['sale.subscription'].sudo().search(
                            [('order_id', '=', int(order_id))], limit=1)
                        subscription_order.delete_item_line()
                        # update subscription line
                        subscription_order.sudo().write({
                            'recurring_invoice_line_ids': invoice_lines
                        })
                        subscription_order.save_recurring_next_invoice()
                    else:
                        subscription_order = request.env['sale.subscription'].sudo().create({
                            'name': 'Subscription book',
                            'partner_id': partner_id,
                            'pricelist_id': pricelist.id,
                            'template_id': template_id,
                            'date_start': date_start,
                            'recurring_next_date': recurring_next_date,
                            'stage_id': id_stage,
                            'order_id': order.id,
                            'website': domain,
                            'user_id': 2,
                            'is_check_trial': True,
                            'recurring_invoice_line_ids': invoice_lines,
                            'industry_management_id': industry_plans.id,
                            'term_of_sale_subscription': 1,
                            'date_unpail': current_date
                        })
                        subscription_order.save_recurring_next_invoice()
                        request.session['subscription_order'] = subscription_order.id
                    render_values = {
                        'trial': int(trial),
                        'checkout': post,
                        'partner_id': partner_id,
                    }
                    if order:
                        request.session['my_orders_plans'] = order.id
                        request.session['sale_order_id'] = order.id
                        render_values.update({
                            'website_sale_order': order,
                            'order': order,
                            'currency': order.currency_id,
                            'amount': order.amount_total,
                            'partner_id': order.partner_id.id,
                            'total_price': order.amount_total,
                            'access_token': order._portal_ensure_token(),
                            'transaction_route': f'/shop/payment/transaction/{order.id}',
                            'landing_route': '/shop/payment/validate',
                        })
                    acquirers_sudo = request.env['payment.acquirer'].sudo().search([('state', 'in', ['enabled', 'test'])])
                    logged_in = not request.env.user._is_public()
                    tokens = request.env['payment.token'].sudo().search(
                        [('acquirer_id', 'in', acquirers_sudo.ids), ('partner_id', '=', order.partner_id.id)]
                    ) if logged_in else request.env['payment.token']
                    render_values.update({
                        'acquirers': acquirers_sudo,
                        'tokens': tokens
                    })
                    value = {}
                    if trial == 2:
                        data_order = dict({
                            'subscription_id': subscription_order.id,
                            'order_id': order.id,
                            'partner_id': partner_id,
                            'action': 'back'
                        })
                        merge_data = dict(data_session, **data_order)
                        request.session['data_buy'] = merge_data
                        value.update({
                            'trial': trial
                        })
                    else:
                        value.update({
                            'trial': trial,
                        })
                    return value
            else:
                partner_id = data_session.get('partner_id')
                subscription_id = data_session.get('subscription_id')
                order_id = data_session.get('order_id')
                product_order.insert(0, int(product_id))
                sale_subcription = request.env['sale.subscription'].sudo().browse(subscription_id)
                sale_order = request.env['sale.order'].sudo().browse(order_id)

                #Delete sale subscription line addons
                sale_subcription.delete_addons_line()
                # Delete sale order line addons
                sale_order.delete_addons_line()

                product_product = request.env['product.product'].sudo().search([('product_tmpl_id', 'in', product_order)])
                list_product_change = [k.id for k in product_product]

                #add product{sale subscription, add-ons}
                sale_subcription.add_data_line(list_product_change, sale_subcription.pricelist_id.id, sale_subcription.template_id.id, sale_subcription.recurring_next_date, number_user)

                values_order = sale_order.add_data_line(list_product_change, sale_subcription.pricelist_id.id, number_user)

                sale_order.write({'order_line': values_order})
                request.session['my_orders_plans'] = sale_order.id
                # Payment

                data_partner = {
                    'name': reg_name,
                    'email': reg_email,
                    'phone': reg_phone,
                    'code_phone': code_country,
                    'company_name': reg_company_name,
                    'country_id': reg_country,
                    'zip': zipcode,
                    'street': reg_street,
                    'lang': reg_language_id,
                }
                if reg_state and reg_state != '':
                    data_partner.update({
                        'state_id': int(reg_state)
                    })
                request.env['res.partner'].browse(partner_id).sudo().write(data_partner)

                user_update = request.env['res.users'].sudo().search([('partner_id', '=', partner_id)])
                user_update.sudo().with_context(no_reset_password=True).write({
                    'login': reg_email,
                })
                if trial == 1:
                    values = {
                        'trial': int(trial),
                        'id_plans': product_id
                    }
                else:
                    value = {
                        'trial': trial
                    }
                return value
        except:
            return request.redirect('/')

    @http.route('/shop/payment', csrf=False, type='http', auth='public', website=True)
    def customer_payment_order(self, **kw):
        try:
            data = request.session.get('data_buy')
            values = self.step_addons(data)
            # render template summer
            data_addons = self.get_addons(data, step='address')

            values.update(data_addons)
            values.update(data)

            if request.session.get('my_orders_plans'):
                order_id = request.session['my_orders_plans']
            else:
                return request.redirect('/plans/')
            if order_id:
                order = request.env['sale.order'].sudo().search([('id', '=', order_id)])
            values.update({
                'num_users': int(data.get('num_users')),
                'content_layout': 'payment',
                'website_sale_order': order,
                'order': order,
                'currency': order.currency_id,
                'amount': order.amount_total,
                'partner_id': order.partner_id.id,
                'total_price': order.amount_total,
                'access_token': order.access_token,
                'transaction_route': f'/shop/payment/transaction/{order.id}',
                'landing_route': '/shop/payment/validate'
            })
            acquirers_sudo = request.env['payment.acquirer'].sudo().search([('state', 'in', ['enabled', 'test'])])
            values.update({
                'acquirers': acquirers_sudo,
                'tokens': request.env['payment.token'].search(
                    [('acquirer_id', 'in', acquirers_sudo.ids)])
            })
            return http.request.render('onnet_customer_signup.layout', values)
        except:
            return request.redirect('/')

    # get - province
    @http.route('/plans/get-province', csrf=False, type='json', auth='public', website=True)
    def get_province(self, country_id):
        try:
            states = request.env['res.country.state'].search([('country_id', '=', int(country_id))])
            if states:
                values = {
                    'html': request.env.ref('onnet_customer_signup.province')._render({
                        'states': states,
                        'checkout': request.env.user.partner_id
                    })
                }
            else:
                values = {
                    'html': ''
                }
            return values
        except:
            return request.redirect('/')

    # check domain
    @http.route('/check-domain', csrf=False, type='json', auth='public', website=True)
    def ajax_check_domain(self, domain):
        try:
            check = True
            seting_domain = request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.config_domain')
            if domain:
                domain = domain + '.' + seting_domain
                domain_exist = request.env['sale.subscription'].sudo().search([('website', '=', domain)])
                if domain_exist:
                    check = False
            values = {
                'check': check
            }

            return values
        except:
            return request.redirect('/')
        # check user

    @http.route('/check-user', csrf=False, type='json', auth='public', website=True)
    def ajax_check_user(self, email=None, partner_id=None):
        try:
            check = False
            if email:
                user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
                user_curent = request.env['res.partner'].sudo().search(
                    [('email', '=', email)], limit=1)
                if user or user_curent:
                    check = True
                    user_curent = request.env['res.partner'].sudo().search(
                        [('email', '=', email), ('id', '=', partner_id)], limit=1)
                    if user_curent:
                        check = False
            values = {
                'check': check
            }
            return values
        except:
            return request.redirect('/')

    def _checkout_form_save(self, mode, checkout, all_values):
        Partner = request.env['res.partner']
        if mode[0] == 'new':
            partner_id = Partner.sudo().with_context(tracking_disable=True).create(checkout).id
        elif mode[0] == 'edit':
            partner_id = int(all_values.get('partner_id', 0))
            if partner_id:
                Partner.browse(partner_id).sudo().write(checkout)
        return partner_id

    def save_lead_line(self, id_industry, list_addons_id, subscription_id):
        lead_line = []
        industry = request.env['industry.management'].search([('id', '=', id_industry)])
        lead_line.append((0, 0, {
            'name': 'Industry:' + ' ' + industry.industry_name
        }))
        subscription = request.env['product.template'].sudo().search([('id', '=', subscription_id)])
        lead_line.append((0, 0, {
            'name': 'Subscription Plans:' + ' ' + subscription.name
        }))
        for product_line in list_addons_id:
            item = request.env['product.template'].sudo().search([('id', '=', int(product_line))])
            lead_line.append((0, 0, {
                'name': 'Add-on:' + ' ' + item.name
            }))
        return lead_line

class OrderSubcriptionData(PaymentPostProcessing):

    @http.route('/payment/status/poll', type='json', auth='public')
    def poll_status(self):
        """ Fetch the transactions to display on the status page and finalize their post-processing.
              :return: The post-processing values of the transactions
              :rtype: dict
              """
        # Retrieve recent user's transactions from the session
        limit_date = fields.Datetime.now() - timedelta(days=1)
        monitored_txs = request.env['payment.transaction'].sudo().search([
            ('id', 'in', self.get_monitored_transaction_ids()),
            ('last_state_change', '>=', limit_date)
        ])
        if not monitored_txs:  # The transaction was not correctly created
            return {
                'success': False,
                'error': 'no_tx_found',
            }

        # Build the list of display values with the display message and post-processing values
        display_values_list = []
        for tx in monitored_txs:
            display_message = None
            # get stage config
            ir_config = request.env['ir.config_parameter'].sudo()
            subscription_state = request.env['sale.subscription.stage'].sudo()
            subscription_sudo = request.env['sale.subscription'].sudo()

            progress_id = int(ir_config.get_param('onnet_custom_subscription.sale_subscription_progress'))
            maitenance_id = int(ir_config.get_param(
                'onnet_custom_subscription.sale_subscription_maintain'))
            maitenance_order = subscription_state.search([('id', '=', maitenance_id)])

            subscription_order_active = subscription_sudo.search([('code', '=', tx.sale_order_ids.origin)])
            subscription_order = subscription_sudo.search([('order_id', '=', tx.sale_order_ids.id)])
            if tx.state == 'pending':
                display_message = tx.acquirer_id.pending_msg
            elif tx.state == 'done':
                if subscription_order:
                    for index in subscription_order:
                        if not index.is_check_trial == True:
                            index.order_id._send_order_confirmation_mail()
                            # delete line
                            index.set_active()
                            request.session['id_order'] = None
                            if index.partner_id.payment_token_ids:
                                index.write({
                                    'payment_token_id': index.partner_id.payment_token_ids[0],
                                    'date_unpail': '', 'is_check_trial': True})
                            else:
                                index.write({'date_unpail': '', 'is_check_trial': True})
                            if int(index.id):
                                self._send_active(index)
                                sale_order = index.order_id
                                sale_order.change_sale()

                                request.session['active_firework'] = 1
                                request.session['session_subscription_redirect'] = index.id
                                request.session['sale_order_id'] = index.id
                            request.session['total_price'] = 0
                            display_message = tx.acquirer_id.done_msg
                        else:
                            if index.is_automatic_payment == False:
                                index._send_email_active()
                            else:
                                super_admin = request.env['res.users'].sudo().browse(SUPERUSER_ID)
                                index.id_email_sucess.sudo().write({'payment_state': 'in_payment'})
                                index.sudo().write({'recurring_next_date': index.get_current_date(), 'date': index.get_current_date()})
                                id_emai_succes = index.with_user(super_admin).send_success_mail(tx, index.id_email_sucess)
                                request.env['mail.mail'].sudo().search([('id', '=', id_emai_succes)]).send()

                                index.remove_automatic()

                # cancel order payment success
                if tx.sale_order_ids.subscription_management == 'extend':
                    subscription_order_active.write(
                        {'recurring_next_date': subscription_order_active.recurring_next_date + relativedelta(months=1),
                         'date': subscription_order_active.recurring_next_date + relativedelta(months=1),
                         'stage_id': int(maitenance_order.id),
                         'to_renew': False, 'is_extra_maintenance': True})
                    #  send email cancel use extend subsciption success
                    template_id = request.env.ref('onnet_customer_signup.sale_subscription_to_maintenance').id
                    self._send_email_upgrade(template_id, subscription_order_active, 'cancel-extend')
                # upgrade order payment success
                elif tx.sale_order_ids.subscription_management == 'upsell':
                    record_order = tx.sale_order_ids
                    product_new_plans = record_order.get_sale_subscription_order_line()
                    quanty_new = record_order.get_quantity_plans()
                    price_plans_selected = product_new_plans.product_tmpl_id.get_price_with_price_list(
                        record_order.pricelist_id, quanty_new)
                    list_addon_id = record_order.get_addons_order_line()
                    recurring_invoice_line_plans = {
                        'name': product_new_plans.name,
                        'product_id': product_new_plans.id,
                        'quantity': quanty_new,
                        'price_unit': price_plans_selected,
                        'uom_id': product_new_plans.uom_id.id,
                    }
                    recurring_invoice_line_ids = []
                    product_addon = request.env['product.product'].sudo().search([('id', 'in', list_addon_id)])
                    for item in product_addon:
                        price_pro = item.list_price
                        if item.product_tmpl_id.is_recurring == True:
                            pricelist_plan_addon = item.product_tmpl_id._get_combination_info(False, int(item.id or 0),
                                                                                              1,
                                                                                              record_order.pricelist_id)
                            price_pro = pricelist_plan_addon['price']
                        recurring_invoice_line_ids.append((0, 0, {
                            'name': item.name,
                            'product_id': item.id,
                            'quantity': 1,
                            'price_unit': price_pro,
                            'uom_id': item.uom_id.id,
                        }))
                    subscription_order_active.add_plans_lines(recurring_invoice_line_plans)
                    subscription_order_active.add_addons_lines(recurring_invoice_line_ids)
                    subscription_order_active.write(
                        {'date': subscription_order_active.recurring_next_date})
                else:
                    subscription_order.set_active()
                    if subscription_order.partner_id.payment_token_ids:
                        subscription_order.write({'payment_token_id': subscription_order.partner_id.payment_token_ids[
                                                      0], 'date_unpail': ''})
                    else:
                        subscription_order.write({'date_unpail': ''})
            elif tx.state == 'cancel':
                subscription_order.set_unpail()
                display_message = tx.acquirer_id.cancel_msg
            display_values_list.append({
                'display_message': display_message,
                **tx._get_post_processing_values(),
            })

        # Stop monitoring already post-processed transactions
        post_processed_txs = monitored_txs.filtered('is_post_processed')
        self.remove_transactions(post_processed_txs)

        # Finalize post-processing of transactions before displaying them to the user
        txs_to_post_process = (monitored_txs - post_processed_txs).filtered(
            lambda t: t.state == 'done'
        )
        success, error = True, None
        try:
            txs_to_post_process._finalize_post_processing()
        except psycopg2.OperationalError:  # A collision of accounting sequences occurred
            request.env.cr.rollback()  # Rollback and try later
            success = False
            error = 'tx_process_retry'
        except Exception as e:
            request.env.cr.rollback()
            success = False
            error = str(e)
            _logger.exception(
                "encountered an error while post-processing transactions with ids %s:\n%s",
                ', '.join([str(tx_id) for tx_id in txs_to_post_process.ids]), e
            )
        #  send email upgrade subsciption success
        if tx.sale_order_ids.subscription_management == 'upsell':
            if request.session.get('active_upgrade') == 1:
                template_id = request.env.ref('onnet_customer_signup.sale_subscription_to_upgrading').id
                self._send_email_upgrade(template_id, subscription_order_active, 'upgrade')
        account_invoice = tx.invoice_ids.id
        record = request.env['account.move.line'].sudo().search([('move_id', '=', account_invoice)])
        for index in record:
            index.sudo().write({'subscription_id': subscription_order.id})
            product = index.product_id
            if product.is_subscription_plans == True or (product.is_trial == True and product.is_recurring == True):
                if subscription_order.date_start:
                    name_change = index.name + " " + "Subscription Cycle:" + " " + subscription_order.date_start.strftime(
                        '%B %d, %Y') + " - " + subscription_order.recurring_next_date.strftime('%B %d, %Y')
                    index.sudo().write({'name': name_change})
                else:
                    pass
        return {
            'success': success,
            'error': error,
            'display_values_list': display_values_list,
        }

    def _send_active(self, subsctiption):
        template_id = request.env.ref('onnet_customer_signup.active_sale_subscription_to_trial').id
        template = request.env['mail.template'].sudo().browse(template_id)
        if template:
            receipt_list = subsctiption.partner_id.email
            email_subject = "Upgrade Trial!"
            body = template.body_html
            row = subsctiption.detail_order_html(subsctiption).get('row')
            next_bill = subsctiption.detail_order_html(subsctiption).get('total')
            body = body.replace("--code--", str(subsctiption.code) or "")
            body = body.replace("--name--", str(subsctiption.partner_id.name) or "")
            body = body.replace("--row--", row or "")
            body = body.replace("--date--", str(datetime.today().strftime('%B %d, %Y')) or "")
            body = body.replace("--subtotal--", str("{:,.2f}".format(subsctiption.recurring_total)) or "")
            body = body.replace("--taxes--", str("{:,.2f}".format(subsctiption.recurring_tax)) or "")
            body = body.replace("--amount--", str("{:,.2f}".format(next_bill)) or "")
            body = body.replace("--currency--", str(subsctiption.currency_id.name) or "")

            body = body.replace('--company_name--', str(request.env.user.company_id.name))
            body = body.replace('--company_street--', str(request.env.user.company_id.street))
            body = body.replace('--company_email--', str(request.env.user.company_id.email))
            body = body.replace('--company_phone--', str(request.env.user.company_id.phone))
            body = body.replace('--company_website--', str(request.env.user.company_id.website))
            body = body.replace('--base_url--', str(request.env['ir.config_parameter'].sudo().get_param('web.base.url')))
            logo = _("/logo.png?company=") + "%s" % (request.env.user.company_id.id)
            body = body.replace("--logo--", logo)


            mail_values = {
                'subject': email_subject,
                'body_html': body,
                'email_to': receipt_list
            }

            request.env['mail.mail'].sudo().create(mail_values).send()

    def _send_email_upgrade(self, template_id, subsctiption, type):
        template = request.env['mail.template'].sudo().browse(template_id)
        if template:
            receipt_list = subsctiption.partner_id.email
            body = template.body_html
            #
            if type == 'upgrade':
                order = request.env['sale.order'].sudo().search(
                    [('state', '=', 'sale'), ('origin', '=', subsctiption.code),
                     ('subscription_management', '=', 'upsell')], limit=1)
                invoice = request.env['account.move'].sudo().search(
                    [('invoice_origin', '=', order.name)], limit=1)
            elif type == 'cancel-extend':
                order = request.env['sale.order'].sudo().search(
                    [('state', '=', 'draft'), ('origin', '=', subsctiption.code),
                     ('subscription_management', '=', 'extend')], limit=1)
            else:
                order = request.env['sale.order'].sudo().search(
                    [('state', '=', 'draft'), ('origin', '=', subsctiption.code),
                     ('subscription_management', '=', 'extend')], limit=1)

            if order:
                ProductName = (order.order_line)[0].name
                if type == 'upgrade':
                    row = order.detail_order_html(order).get('row')
                    body = body.replace("--invoice--", str(invoice.name) or "")
                elif type == 'cancel-extend':
                    row = order.detail_order_extend_html(order).get('row')
                else:
                    row = subsctiption.detail_order_html(subsctiption).get('row')

                body = body.replace("--code--", str(order.name) or "")
                body = body.replace("--row--", row or "")
                body = body.replace("--name--", str(subsctiption.partner_id.name) or "")
                body = body.replace("--ProductName--", str(ProductName) or "")

                body = body.replace("--date--", str(subsctiption.recurring_next_date.strftime('%B %d, %Y')) or "")
                body = body.replace("--datestart--", str(datetime.today().strftime('%B %d, %Y')) or "")
                body = body.replace("--dateend--", str(subsctiption.recurring_next_date.strftime('%B %d, %Y')) or "")

                body = body.replace("--subtotal--", str("{:,.2f}".format(order.amount_total)) or "")
                body = body.replace("--taxes--", str("{:,.2f}".format(order.amount_tax)) or "")
                body = body.replace("--amount--", str("{:,.2f}".format(order.amount_total)) or "")
                body = body.replace("--currency--", str(subsctiption.currency_id.name) or "")
                logo = _("/logo.png?company=") + "%s" % (request.env.user.company_id.id)
                body = body.replace("--logo--", logo)

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

class PortalAccount(portal.PortalAccount):
    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):

        values = self._prepare_portal_layout_values()
        AccountInvoice = request.env['account.move']

        domain = self._get_invoices_domain()

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'invoice_date desc'},
            'duedate': {'label': _('Due Date'), 'order': 'invoice_date_due desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'invoices': {'label': _('Invoices'), 'domain': [('move_type', '=', ('out_invoice', 'out_refund'))]}
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        domain += [('state', '!=', 'draft')]
        # count for pager
        invoice_count = AccountInvoice.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/invoices",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=invoice_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        invoices = AccountInvoice.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_invoices_history'] = invoices.ids[:100]

        values.update({
            'date': date_begin,
            'invoices': invoices,
            'page_name': 'invoice',
            'pager': pager,
            'default_url': '/my/invoices',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return http.request.render("account.portal_my_invoices", values)

class WebsiteSaleInherit(WebsiteSale):
    @http.route('/shop/payment/validate', type='http', auth="public", website=True, sitemap=False)
    def shop_payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :
         - UDPATE ME
        """
        if sale_order_id is None:
            order = request.website.sale_get_order()
        else:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            assert order.id == request.session.get('sale_last_order_id')

        if transaction_id:
            tx = request.env['payment.transaction'].sudo().browse(transaction_id)
            assert tx in order.transaction_ids()
        elif order:
            tx = order.get_portal_last_transaction()
        else:
            tx = None

        active_fire = request.session.get('active_firework')
        sale_sub_trial = request.session.get('session_subscription_redirect')
        if not order or (order.amount_total and not tx):
            if active_fire == 1 and sale_sub_trial:
                uuid_token = request.env['sale.subscription'].sudo().search([('id', '=', int(sale_sub_trial))])
                request.session['active_firework'] = 0
                request.session['session_subscription_redirect'] = 0
                return request.redirect('/my/subscription/' + str(sale_sub_trial) + '/' + str(uuid_token.uuid))

        if order and not order.amount_total and not tx:
            order.with_context(send_email=True).action_confirm()
            return request.redirect(order.get_portal_url())

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx and tx.state == 'draft':
            return request.redirect('/plans')

        if not tx:
            return request.redirect('/plans')
        PaymentPostProcessing.remove_transactions(tx)

        if active_fire == 1 and sale_sub_trial:
            uuid_token = request.env['sale.subscription'].sudo().search([('id', '=', int(sale_sub_trial))])
            request.session['active_firework'] = 0
            request.session['session_subscription_redirect'] = 0
            return request.redirect('/my/subscription/' + str(sale_sub_trial) + '/' + str(uuid_token.uuid))

        subscription_buy = request.session.get('buy_subscription_id')
        industry_buy = request.session.get('buy_industry_id')
        active_extra_maintenance = request.session.get('active_extra_maintenance')
        # reset session ve 0
        request.session['active_extra_maintenance'] = 0
        request.session['active_upgrade'] = 0
        if active_extra_maintenance:
            uuid_token = request.env['sale.subscription'].sudo().search([('id', '=', int(sale_sub_trial))])
            return request.redirect('/my/subscription/' + str(sale_sub_trial) + '/' + str(uuid_token.uuid))

        if subscription_buy != 0 and industry_buy != 0:
            request.session['buy_subscription_id'] = 0
            return request.redirect(
                '/firework?product_id=' + str(subscription_buy) + '&industry_id=' + str(industry_buy))

def ensure_db(redirect='/web/database/selector'):
    # This helper should be used in web client auth="none" routes
    # if those routes needs a db to work with.
    # If the heuristics does not find any database, then the users will be
    # redirected to db selector or any url specified by `redirect` argument.
    # If the db is taken out of a query parameter, it will be checked against
    # `http.db_filter()` in order to ensure it's legit and thus avoid db
    # forgering that could lead to xss attacks.
    db = request.params.get('db') and request.params.get('db').strip()

    # Ensure db is legit
    if db and db not in http.db_filter([db]):
        db = None

    if db and not request.session.db:
        # User asked a specific database on a new session.
        # That mean the nodb router has been used to find the route
        # Depending on installed module in the database, the rendering of the page
        # may depend on data injected by the database route dispatcher.
        # Thus, we redirect the user to the same page but with the session cookie set.
        # This will force using the database route dispatcher...
        r = request.httprequest
        url_redirect = werkzeug.urls.url_parse(r.base_url)
        if r.query_string:
            # in P3, request.query_string is bytes, the rest is text, can't mix them
            query_string = iri_to_uri(r.query_string)
            url_redirect = url_redirect.replace(query=query_string)
        request.session.db = db
        abort_and_redirect(url_redirect.to_url())

    # if db not provided, use the session one
    if not db and request.session.db and http.db_filter([request.session.db]):
        db = request.session.db

    # if no database provided and no database in session, use monodb
    if not db:
        db = db_monodb(request.httprequest)

    # if no db can be found til here, send to the database selector
    # the database selector will redirect to database manager if needed
    if not db:
        werkzeug.exceptions.abort(request.redirect(redirect, 303))

    # always switch the session to the computed db
    if db != request.session.db:
        request.session.logout()
        abort_and_redirect(request.httprequest.url)

    request.session.db = db

def abort_and_redirect(url):
    response = request.redirect(url, 302)
    response = http.root.get_response(request.httprequest, response, explicit_session=False)
    werkzeug.exceptions.abort(response)

# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
                          'password', 'confirm_password', 'city', 'country_id', 'lang'}

class CustomerPortalInherit(CustomerPortal):
    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "country_id"]