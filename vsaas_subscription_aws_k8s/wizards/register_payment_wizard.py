# -*- coding: utf-8 -*-
from re import sub

from odoo import models, fields, api, _

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    _description = 'Register Payment'

    def action_create_payments(self):
        payments = self._create_payments()
        subscription = self.env['sale.subscription'].browse(self.env.context.get('active_id'))
        subscription.set_payment_manual()
        if self._context.get('dont_redirect_to_payments'):
            return True

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })
        return action