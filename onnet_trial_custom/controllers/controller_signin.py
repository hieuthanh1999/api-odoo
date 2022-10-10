# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from werkzeug.exceptions import Forbidden, NotFound
from odoo.http import Response
import requests
import json


class SigninController(http.Controller):
    @http.route('/check-status-domain', type='json', auth='none', methods=['POST'], csrf=False)
    def check_domain_done(self, **kw):
        url = kw.get('url_instance')
        id = kw.get('id')
        if id:
            subscription_record = request.env['sale.subscription'].sudo().search([('id', '=', int(id))])
        try:
            if subscription_record.instance_status in ['running', 'pending', 'containercreating']:
                response_url = requests.post(url=url, verify=False)
                if response_url.status_code == 200 and response_url:
                    data = {
                        'check': 1,
                        'url': url,
                        'status': 'done',
                    }
                else:
                    data = {
                        'check': 1,
                        'url': url,
                        'status': 'loading',
                    }
            elif subscription_record.instance_status in ['not_created', 'removed', 'error', 'crashloopbackoff', 'failed']:
                data = {
                    'check': 2
                }
            return data
        except:
            return request.render('onnet_custom_error.500')

    @http.route('/check-status-invite', type='json', auth='none', methods=['POST'], csrf=False)
    def check_domain(self, **kw):
        url = kw.get('url_instance')
        try:
            response_url = requests.post(url=url, verify=False)
            if response_url.status_code == 200 and response_url:
                data = {
                    'url': url,
                    'status': 'done',
                }
            else:
                data = {
                    'url': url,
                    'status': 'loading',
                }
        except:
            return request.render('onnet_custom_error.500')
        return data

    @http.route('/invite-your-colleagues', type='http', auth='user', website=True, sitemap=True)
    def invite_index(self, **kw):
        redirect_domain_id = request.session.get('subscription_domain')
        id_login = request.session.uid
        record = request.env['res.users'].sudo().search([('id', '=', int(id_login))])
        record.send_email_done()
        if redirect_domain_id:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            subscription_record = request.env['sale.subscription'].sudo().search([('id', '=', int(redirect_domain_id))])
            subscription_record.create_vive_software()
            name_website = base_url.split("//")
            image_invite = request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.image_invite')
            return request.render('onnet_trial_custom.invite_views', {
                'redirect_domain': subscription_record,
                'website_plans': base_url,
                'name_website': name_website[1],
                'image_invite': image_invite
            })
        else:
            return request.render('onnet_custom_error.500')

    @http.route('/creating-instance', type='http', auth='user', website=True, sitemap=True, csrf=False, cors='*')
    def done_index(self, **kw):
        redirect_domain_id = request.session.get('subscription_domain')
        if redirect_domain_id:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            subscription_record = request.env['sale.subscription'].sudo().search([('id', '=', int(redirect_domain_id))])
            name_website = base_url.split("//")
            image_done = request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.image_done')
            email_support = request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.email_support')
            return request.render('onnet_trial_custom.done_screen_views', {
                'redirect_domain': subscription_record,
                'website_plans': base_url,
                'name_website': name_website[1],
                'image_done': image_done,
                'email_support': email_support
            })
        else:
            return request.render('onnet_custom_error.500')

    @http.route('/send_email', csrf=False, type='json', auth='public', website=True)
    def send_email(self, arr_key, arr_value):
        template_id = request.env.ref('onnet_trial_custom.patient_card_email_template').id

        template = request.env['mail.template'].sudo().browse(template_id)
        domain_invite = request.session.get('subscription_domain')
        list_data = dict(zip(arr_key, arr_value))
        subscription_record = request.env['sale.subscription'].sudo().search([('id', '=', int(domain_invite))])
        partner_name = request.env['res.partner'].sudo().search([('id', '=', int(subscription_record.partner_id.id))])
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for key in list_data:
            if template:
                receipt_list = list_data[key]
                email_subject = str(partner_name.name) + " " + "from" + " " + str(
                    partner_name.company_name) + " invites you to connect to HiiBoss"

                body = template.body_html
                body = body.replace('--name--', str(key))
                body = body.replace('--email--', str(list_data[key]))
                body = body.replace('--domain--', str(subscription_record.website))
                body = body.replace('--user--', str(partner_name.name))
                body = body.replace('--company_name--', str(request.env.user.company_id.name))
                body = body.replace('--company_street--', str(request.env.user.company_id.street))
                body = body.replace('--company_email--', str(request.env.user.company_id.email))
                body = body.replace('--company_phone--', str(request.env.user.company_id.phone))
                body = body.replace('--company_website--', str(request.env.user.company_id.website))
                body = body.replace('--base_url--', str(base_url))
                logo = _("/logo.png?company=") + "%s" % (request.env.user.company_id.id)
                body = body.replace("--logo--", logo)

                mail_values = {
                    'subject': email_subject,
                    'body_html': body,
                    'email_to': receipt_list
                }
                request.env['mail.mail'].sudo().create(mail_values).send()

    @http.route('/loading-hiiboss/<string:url_hiiboss>', type='http', auth='public', website=True, sitemap=True, csrf=False, cors='*')
    def loading_hiiboss(self, **kw):
        url = kw.get('url_hiiboss')
        sub = request.env['sale.subscription'].sudo().search([('website','=ilike', url)])
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return request.render('onnet_trial_custom.onnet_view_load_hiiboss', {
            'url_hiiboss': url,
            'id': sub.id,
            'base_url': base_url
        })
