# -*- coding: utf-8 -*-

from odoo import api, fields, models, api

class InheritCrmLead(models.Model):
    _inherit = 'crm.lead'

    lead_line = fields.One2many('crm.lead.lines', 'lead_id', string='Order Lines', copy=True, auto_join=True)

