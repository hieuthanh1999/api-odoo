# -*- coding: utf-8 -*-
from builtins import tuple

from odoo import api, fields, models


class UsersInherit(models.Model):
    _inherit = 'res.users'
    _description = "Res Users Inherit"

    industry_management = fields.One2many('industry.management', 'res_users', string='Industry Management', copy=True,auto_join=True)

    def send_email_done(self):
        """Send Email notifications should be send out when the account is verified"""
        email_context = self.env.context.copy()
        partner_id = self.partner_id.id
        sale_subscription = self.env['sale.subscription'].sudo().search([('partner_id', '=', partner_id)], limit=1)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # update context
        email_context.update({
            'base_url': base_url,
            'website': sale_subscription.website,
            'sale_id': sale_subscription.id
        })

        template = self.env.ref('onnet_custom_subscription.email_notifications_account')
        id_email = template.with_context(email_context).sudo().send_mail(self.id)
        self.env['mail.mail'].sudo().search([('id', '=', id_email)]).send()

    def get_password(self):
        """retrieve user's password"""
        params = [self.id]
        self.env.cr.execute("SELECT password FROM res_users WHERE id = %s", tuple(params))
        pass_tuple = self.env.cr.fetchall()
        return pass_tuple[0][0]


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'
    _description = "Res Partner Inherit"

    number_industry = fields.One2many('number.industry', 'res_partner', string='Assigned Trial Subscriptions', copy=True, auto_join=True)