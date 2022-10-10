# -*- coding: utf-8 -*-
from odoo import api, fields, models

class InheritSaleSubscriptionStage(models.Model):
    _inherit = 'sale.subscription.stage'

    category = fields.Selection([
        ('draft', 'Unpaid'), ('progress', 'Active'),
        ('trial', 'Trial'), ('cancel', 'Cancel'), ('maintenance', 'Maintenance'),
        ('trial_expired', 'Trial Expired'),
        ('dunning', 'Dunning'),
        ('cancel_sale', 'Date Cancel'),
        ('closed', 'Closed')], required=True, default='draft', help="Category of the stage")
    is_check_show = fields.Boolean(string='Show on portal', default=False)

class SaleSubscriptionLog(models.Model):
    _inherit = 'sale.subscription.log'

    category = fields.Selection([
        ('draft', 'Unpaid'),
        ('progress', 'Active'),
        ('trial', 'Trial'),
        ('cancel', 'Cancel'),
        ('maintenance', 'Maintenance'),
        ('trial_expired', 'Trial Expired'),
        ('dunning', 'Dunning'),
        ('cancel_sale', 'Date Cancel'),
        ('closed', 'Closed')
    ], required=True, default='draft', help="Subscription stage category when the change occured")
    is_check_show = fields.Boolean(string='Show on portal', default=False)

