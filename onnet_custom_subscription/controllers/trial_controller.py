# -*- coding: utf-8 -*-
from builtins import super

from requests import get
import random
from odoo import http, fields
from odoo.http import request
from odoo.addons.sale_subscription.controllers.portal import PaymentPortal
from odoo.addons.sale.controllers.portal import CustomerPortal
from werkzeug.exceptions import Forbidden, NotFound
from odoo.addons.payment import utils as payment_utils
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from datetime import datetime
from odoo.addons.portal.controllers.portal import CustomerPortal


class TrialController(http.Controller):

    @http.route('/plans', type='http', auth='public', website=True, sitemap=True)
    def plans(self, **kw):
        industry_management = request.env['industry.management'].search([])
        count_industry = request.env['industry.management'].search_count([])
        if industry_management:
            max_industry = max(industry_management)
        else: max_industry = 0
        annually_id = int(request.env['ir.config_parameter'].sudo().get_param(
                'onnet_custom_subscription.annually_product_pricelist'))
        month_id = int(request.env['ir.config_parameter'].sudo().get_param(
            'onnet_custom_subscription.month_product_pricelist'))
        annually = request.env['product.pricelist'].search([('id', '=', annually_id)]).item_ids
        # Text website
        plans_title = request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.plans_title')
        plans_title_content = request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.plans_title_content')
        text = "0.0%"

        if annually:
            text_discount = max(annually)
            if text_discount.compute_price in ['percentage', 'formula']:
                s = text_discount.price.find('%')
                text = text_discount.price[0: s + 1]
                text = text.replace(" ", "")
        values ={
            'industry_management': industry_management,
            'text_discount': text,
            'month_id': month_id,
            'plans_title': plans_title,
            'plans_title_content': plans_title_content,
            'count_industry': count_industry,
            'max_industry': max_industry
        }
        return request.render('onnet_custom_subscription.website_plans', values)

    @http.route('/email-user', type='http', auth='public', website=True, sitemap=True)
    def index_email(self, **kw):
        id_login = request.session.uid
        record = request.env['res.users'].sudo().search([('id', '=', int(id_login))])
        record.send_email_done()
        return request.redirect('/invite-your-colleagues')

    @http.route('/show-description', type='json', auth='public', website=True, sitemap=True)
    def show_description(self, **kw):
        id_industry = kw.get('id_industry')
        if id_industry:
            industry_management = request.env['industry.management'].search([('id', '=', int(id_industry))]).description

            values = {
                'html': request.env.ref('onnet_custom_subscription.view_description')._render({
                    'industry': industry_management
                },)
            }
            return values
        else:
            values = {
                'html': ''
            }

            return values

    @http.route('/show-plans', type='json', auth='public', website=True, sitemap=True)
    def show_plans(self, **kw):
        id_industry = kw.get('id_industry')
        pricelist_selected = kw.get('price_list')
        if id_industry:
            subscription = request.env['product.template'].sudo().search([('industry', '=', int(id_industry))])
            text_popular = request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.text_popular')

            annually_id = int(
                request.env['ir.config_parameter'].sudo().get_param(
                    'onnet_custom_subscription.annually_product_pricelist'))
            month_id = int(
                request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.month_product_pricelist'))
            annually = request.env['product.pricelist'].search([('id', '=', annually_id)])
            month = request.env['product.pricelist'].search([('id', '=', month_id)])
            for item in annually.item_ids:
                test = item
            if pricelist_selected == False:
                price_list = month
                text_pricelist = 'month'
            else:
                price_list = annually
                text_pricelist = 'year'
            form_contact_us = str(
                request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.contact_us_form'))
            values = {
                'html': request.env.ref('onnet_custom_subscription.view_plans_website')._render({
                    'subscription_plans': subscription,
                    'text_popular': text_popular,
                    'pricelist': price_list,
                    'text_pricelist': text_pricelist,
                    'id_insdustry': int(id_industry),
                    'form_contact_us': form_contact_us
                },),
                'id_insdustry': int(id_industry)
            }
            return values
        else:
            values = {
                'html': ''
            }

            return values

    @http.route('/active-token', type='json', auth='public', website=True, sitemap=True)
    def active_token(self, id_sub):
        sale_record = request.env['sale.subscription'].sudo().search([('id', '=', int(id_sub))])
        sale_record.sale_prepare(expiration=fields.Datetime.now() + relativedelta(days=1))
        sale_record._send_email_active()

    @http.route('/plans_remove', type='http', auth='public', website=True, sitemap=True)
    def index(self, **kw):
        subscription = request.env['product.template'].sudo().search([])
        industry_management = request.env['industry.management'].search([])
        return request.render('onnet_custom_subscription.website_index_plans', {
            'subscription_plans': subscription,
            'industry_management': industry_management
    })

    @http.route('/active-instance', type='http', auth='public', website=True, sitemap=True)
    def index_active(self, *args, **kw):
        """ Create Instance.
              :param int subscription_id
              :param int partner_id
              :param string token
              :return render view layout
        """
        sale_sub_id = kw.get('sale_id')
        partner_id = kw.get('part_id')
        token = kw.get('token')

        if sale_sub_id and partner_id and token:
            subscription_record = request.env['sale.subscription'].sudo().search([('id', '=', int(sale_sub_id))])
            today = fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if subscription_record.sale_expiration:
                end_date = subscription_record.sale_expiration.strftime('%Y-%m-%d %H:%M:%S')
            else:
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

                email_support = request.env['ir.config_parameter'].sudo().get_param(
                    'onnet_custom_subscription.email_support')
                value = {
                    'email_support': email_support,
                    'base_url': base_url
                }
                return request.render('onnet_custom_subscription.expired_version_views', value)
            #check end date and today, delete token and end date
            if today == end_date or today > end_date:
                subscription_record.write({'token': '', 'sale_expiration': '', 'sale_url': ''})
            else:
                partner = request.env['res.partner'].sudo().search([('id', '=', int(partner_id))])

                request.session['invite_partner'] = partner_id
                request.session['subscription_domain'] = subscription_record.id
                check_pass = request.env['res.users'].sudo().search([('partner_id', '=', partner.id)])

                subscription_record.write({'token': '', 'sale_expiration': '', 'sale_url': ''})

                if check_pass.signup_valid == True:
                    return request.redirect(str(check_pass.signup_url + '&redirect=invite-your-colleagues') or "")
                else:
                    base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    return request.redirect(str(base_url + '/web/login?redirect=invite-your-colleagues') or "")

    @http.route('/firework',  type='http', auth='public', website=True, sitemap=False)
    def firework(self, **kw):
        if kw.get('product_id') and kw.get('industry_id'):
            plans_id = int(kw.get('product_id'))
            industry_id = int(kw.get('industry_id'))
            request.session['data_buy'] = None
            if not plans_id:
                return request.redirect('/plans/')
            name_plans = request.env['product.template'].sudo().search([('id', '=',  plans_id)]).name
            name_industry = request.env['industry.management'].sudo().search([('id', '=',  industry_id)]).industry_name
            return request.render('onnet_custom_subscription.website_index_firework', {
                'name_plans': name_plans,
                'name_industry': name_industry
            })
        else:
            return request.render('onnet_custom_subscription.website_index_firework')

    @http.route('/create-instance', type='http', auth='public', website=True, sitemap=False)
    def fireworksend(self, **kw):
        try:
            subscription_order_id = request.session.get('subscription_order')
            record_subscription = request.env['sale.subscription'].sudo().search([('id', '=', subscription_order_id)])
            trial_template = int(
                request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.trial_template'))
            if record_subscription.template_id.id == int(trial_template):
                record_subscription._send_email_active()
            return request.redirect('/welcome')
        except:
            raise ValidationError


class OrderInherit(CustomerPortal):
    @http.route(['/my/orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        parent_order = super(OrderInherit, self).portal_order_page(order_id, report_type=report_type, access_token=access_token, message=message, download=download, **kw)
        text = parent_order.qcontext
        check = self.check_recurring(order_id)
        text.update({'check_recurring': check})
        return parent_order

    def check_recurring(self, order_id):
        record = request.env['sale.order'].sudo().search([('id', '=', order_id)])
        check = True
        for index in record.order_line.product_id:
            if index.is_recurring == False and index.is_add_ons == True:
                check = False
                break
        return check
