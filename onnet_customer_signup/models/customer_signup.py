# -*- coding: utf-8 -*-

from odoo import api, fields, models, api
# -*- coding: utf-8 -*-
import base64
import logging
import re
from io import BytesIO

import babel
import babel.dates
from markupsafe import Markup as M, escape
from PIL import Image
from lxml import etree, html

from odoo import api, fields, models, _, _lt
from odoo.tools import posix_to_ldml, float_utils, format_date, format_duration, pycompat
from odoo.tools.mail import safe_attrs
from odoo.tools.misc import get_lang, babel_locale_parse

_logger = logging.getLogger(__name__)

class CustomerSignup(models.Model):
    _name = "customer.signup"
    _description = "Customer signup"

    name = fields.Char()

class ContactInherit(models.AbstractModel):
    _inherit = 'ir.qweb.field.contact'

    @api.model
    def value_to_html(self, value, options):
        if not value:
            return ''

        opf = options.get('fields') or ["name", "address", "phone", "mobile", "email"]
        sep = options.get('separator')
        template_options = options.get('template_options', {})
        if sep:
            opsep = escape(sep)
        elif template_options.get('no_tag_br'):
            # escaped joiners will auto-escape joined params
            opsep = escape(', ')
        else:
            opsep = M('<br/>')

        value = value.sudo().with_context(show_address=True)
        name_get = value.name_get()[0][1]
        # Avoid having something like:
        # name_get = 'Foo\n  \n' -> This is a res.partner with a name and no address
        # That would return markup('<br/>') as address. But there is no address set.
        if any(elem.strip() for elem in name_get.split("\n")[1:]):
            address = opsep.join(name_get.split("\n")[1:]).strip()
        else:
            address = ''
        val = {
            'name': name_get.split("\n")[0],
            'address': address,
            'phone': value.phone,
            'mobile': value.mobile,
            'city': value.city,
            'country_id': value.country_id.display_name,
            'website': value.website,
            'email': value.email,
            'vat': value.vat,
            'vat_label': value.country_id.vat_label or _('VAT'),
            'fields': opf,
            'object': value,
            'options': options,
            'code_phone': value.code_phone
        }
        return self.env['ir.qweb']._render('base.contact', val, **template_options)