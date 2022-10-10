# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import json

from psycopg2 import IntegrityError
from werkzeug.exceptions import BadRequest

from odoo import http, SUPERUSER_ID, _
from odoo.http import request
from odoo.tools import plaintext2html
from odoo.exceptions import ValidationError, UserError
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.addons.website.controllers.form import WebsiteForm
from odoo.addons.web.controllers.main import Home

from odoo.addons.portal.controllers.portal import CustomerPortal

class WebsiteFormInherit(WebsiteForm):

    def insert_record(self, request, model, values, custom, meta=None):
        model_name = model.sudo().model
        if model_name == 'mail.mail':
            values.update({'reply_to': values.get('email_from'),'email_cc': values.get('email_from')})
        record = request.env[model_name].with_user(SUPERUSER_ID).with_context(mail_create_nosubscribe=True).create(
            values)

        if custom or meta:
            _custom_label = ""  # Title for custom fields
            if model_name == 'mail.mail':
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                newstr = base_url.replace("http://", "")
                a_html_url = '<a href="%s" target="_blank">%s</a>' % (base_url, newstr)
                _custom_label += "%s" % _("Our customer has send an enquiry from our HiiBoss website ")
                _custom_label += " "
                _custom_label += "%s\n___________\n\n" % _(a_html_url)
            _custom_label += "%s\n___________\n\n" % _("Other Information:")  # Title for custom fields
            default_field = model.website_form_default_field_id
            default_field_data = values.get(default_field.name, '')
            custom_content = (default_field_data + "\n\n" if default_field_data else '') \
                             + (_custom_label + custom + "\n\n" if custom else '') \
                             + (self._meta_label + meta if meta else '')

            # If there is a default field configured for this model, use it.
            # If there isn't, put the custom data in a message instead
            if default_field.name:
                if default_field.ttype == 'html' or model_name == 'mail.mail':
                    custom_content = nl2br(custom_content)
                record.update({default_field.name: custom_content})
            else:
                values = {
                    'body': nl2br(custom_content),
                    'model': model_name,
                    'message_type': 'comment',
                    'res_id': record.id,
                }
                mail_id = request.env['mail.message'].with_user(SUPERUSER_ID).create(values)

        return record.id

class InheritAccount(CustomerPortal):

    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "city", "country_id", "code_phone"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name", "code_phone"]
    
# class HomeInherit(Home):
#     @http.route()
#     def web_login(self, redirect=None, **kw):
#         check = request.session.uid
#         if check:
#             return request.redirect('/')
#
#         return super(HomeInherit, self).web_login()
