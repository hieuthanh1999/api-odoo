from odoo import models, api, fields, _
import logging

_logger = logging.getLogger(__name__)

class ConfirmPayment(models.TransientModel):
    _name = 'wizard.payment'

    description = fields.Html(string='Description Confirm Payment',
                       help='Optional help text for the users with a description of the target view, such as its usage and purpose.',
                       translate=True)

    def action_submit(self):
        self.ensure_one()
        try:
            subscription = self.env['sale.subscription'].browse(self.env.context.get('active_id'))
            subscription.description_payment = self.description
            subscription.check_confirm_payment = True
            subscription.set_payment_manual()
        except Exception as e:
            _logger.info(str(e))

