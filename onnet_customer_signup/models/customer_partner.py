# -*- coding: utf-8 -*-

from odoo import api, fields, models, api

class CustomerPartner(models.Model):
    _inherit = 'res.partner'

    code_phone = fields.Char('Name Code Country')
