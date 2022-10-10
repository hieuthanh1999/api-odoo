# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, exceptions
import logging
_logger = logging.getLogger(__name__)

class UserIndustry(models.Model):
    _name = "users.industry"
    _description = "User Industry Sale Subscription"

    res_user = fields.Many2one('res.users', required=True,  index=True, copy=False)
    res_partner = fields.Many2one('res.partner', index=True, required=True, copy=False)
    industry_management = fields.Many2one('industry.management', required=True, index=True, copy=False)
    sale_subscription = fields.Many2one('sale.subscription', required=True, index=True, copy=False,  ondelete='cascade')
    number = fields.Many2one('number.industry', index=True, copy=False,  ondelete='cascade')

    @api.model
    def create(self, vals):
        record = super(UserIndustry, self).create(vals)
        try:
            check = self.sudo().search_count([('industry_management', '=', vals.get('industry_management')), ('res_partner', '=', vals.get('res_partner'))])
            record_old = self.sudo().search([('industry_management', '=', vals.get('industry_management')), ('res_partner', '=', vals.get('res_partner'))])
            count = 1
            if check == 1:
                self.env['number.industry'].sudo().create({
                    'industry_management': vals.get('industry_management'),
                    'users_industry': record,
                    'res_partner': vals.get('res_partner'),
                    'check_quantity': 1
                })
            else:
                count += 1
                self.env['number.industry'].sudo().browse(record_old.number.id).write({
                    'check_quantity': count
                })
                return record
        except Exception as e:
            _logger.info(str(e))


    
    def check_industry_in_res_partner(self, industry_id, user_id):
        """
        Check out industry in res partner
        param: industry_id
        param: user_id
        return True/False
        """
        try:
            record = self.sudo().search([('industry_management', '=', int(industry_id)), ('res_user', '=', user_id)])

            record_count = self.sudo().search_count([('industry_management', '=', int(industry_id)), ('res_user', '=', user_id)])
            trial_template = int(self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.trial_template'))
            days = int(self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.count_trial'))
            if record:
                for index in record:
                    template_id = index.sale_subscription.template_id.id
                    if (record_count + 1) > days and template_id == int(trial_template):
                        return True
                    else:
                        return False
            elif days == 0:
                return True
            else:
                return False

        except Exception as e:
            _logger.info(str(e))

class NumberIndustry(models.Model):
    _name = "number.industry"
    _description = "Number Sale Subscription"

    users_industry = fields.One2many('users.industry', 'number', index=True, copy=False)
    industry_management = fields.Many2one('industry.management', index=True, copy=False)
    quantity = fields.Integer('Quantity', compute='_quantity')
    check_quantity = fields.Integer('Quantity')
    res_partner = fields.Many2one('res.partner', index=True, copy=False)


    @api.depends('users_industry')
    def _quantity(self):
        for index in self:
            count = self.env['users.industry'].sudo().search_count([('industry_management', '=', index.users_industry.industry_management.id), ('res_partner', '=', index.res_partner.id)])
            index.quantity = count

    def update_quantity(self):
        for index in self:
            if index.check_quantity > 1:
                index.check_quantity -= 1
                index.sudo().write({'check_quantity': index.check_quantity})
            elif index.check_quantity == 1:
                index.unlink()
