from odoo import fields, api, models, _
import requests
import logging
_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    def subscription_update(self):
        try:
            headers = {
                "user": "hiiboss.techservices@gmail.com", #FIXME: Should not hardcode this
                "password": self.admin_password
            }
            res = requests.post(f"https://{self.website}/check/subscription",
                                json=self.get_subscription_information(),
                                headers=headers
                                )
            _logger.info(res.text)
        except Exception as e:
            _logger.info(str(e))

    def update_admin_password(self, old_password, new_password):

        try:
            headers = {
                "user": "hiiboss.techservices@gmail.com", #FIXME: Should not hardcode this
                "password": old_password
            }
            data = {
                'old_password': old_password,
                'new_password': new_password
            }
            res = requests.post(f"https://{self.website}/update/admin/password", json=data, headers=headers)
            _logger.info(res.text)
        except Exception as e:
            _logger.info(str(e))

    def write(self, vals):
        if 'admin_password' in vals and not self.env.context.get('ignore_update_admin_pwd', False):
            self.with_context(ignore_update_admin_pwd=True).update_admin_password(self.admin_password, vals.get('admin_password'))
        res = super(SaleSubscription, self.with_context(ignore_update_admin_pwd=True)).write(vals)
        if 'recurring_invoice_line_ids' in vals or 'recurring_next_date' in vals or 'stage_id' in vals:
            self.subscription_update()
        return res
