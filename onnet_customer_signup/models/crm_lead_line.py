# -*- coding: utf-8 -*-

from odoo import api, fields, models, api

class ModelLeadLine(models.Model):
    _name = "crm.lead.lines"
    _description = "Crm Lead Line Management"

    lead_id = fields.Many2one('crm.lead', string='Lead Reference', required=True, ondelete='cascade', index=True,copy=False)
    name = fields.Text(string='Description', required=True)
