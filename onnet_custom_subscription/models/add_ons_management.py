# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AddOnsManagement(models.Model):
    _inherit = 'product.template'
    _description = "Add-ons Management"
    _order = "sequence, id desc"

    is_add_ons = fields.Boolean(string='Add-ons', default=False)
    sequence = fields.Integer("Sequence")

    @api.model_create_multi
    def create(self, vals_list):
        cate_addons_id = int(self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.product_category_addons'))
        cate_subscrip_id = int(self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.product_category_subscription'))
        for record in vals_list:
            if 'tab_module' in record.keys():
                record.update({"categ_id": cate_subscrip_id})
            else:
                record.update({"categ_id": cate_addons_id})
            sub = super(AddOnsManagement, self).create(vals_list)
        return sub
      
    is_trial = fields.Boolean(string='Is Trial', default=False)
    is_recurring = fields.Boolean(string='Recurring', default=False)

    @api.onchange('is_trial')
    def update_is_recurring(self):
        if self.is_trial == True:
            self.is_recurring = False
