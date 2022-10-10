# -*- coding: utf-8 -*-
from odoo import api, fields, models

class InheritUSer(models.Model):
    _inherit = 'res.users'

    instance_url = fields.Char(string='Instance')
