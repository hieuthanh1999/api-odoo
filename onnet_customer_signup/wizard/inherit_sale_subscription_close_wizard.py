# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleSubscriptionCloseReasonWizard(models.TransientModel):
    _inherit = "sale.subscription.close.reason.wizard"
    _description = 'Subscription Close Reason Wizard Inherit'

    description = fields.Html(string='Description', translate=True)

    @api.onchange('close_reason_id')
    def onchang_close_reason(self):
        if self.close_reason_id:
            pass

    def set_close(self):
        self.ensure_one()
        subscription = self.env['sale.subscription'].browse(self.env.context.get('active_id'))
        if self.description:
            subscription.message_post(body=_('closing text: %s', self.description))

        subscription.close_reason_id = self.close_reason_id
        subscription.set_close()

