from odoo import models, api, fields, _


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    galicea_openid_id = fields.Many2one(string=_("OAuth Client"), comodel_name='galicea_openid_connect.client')

    def create_vive_software(self):
        if not self.galicea_openid_id:
            galicea_openid = self.env['galicea_openid_connect.client'].create(self.get_openid_vals())
            self.write({'galicea_openid_id': galicea_openid.id})
        super(SaleSubscription, self).create_vive_software()

    def cleanup_vive_software(self):
        super(SaleSubscription, self).cleanup_vive_software()
        if self.galicea_openid_id:
            self.galicea_openid_id.unlink()

    def get_k8s_env(self):
        k8s_env = super(SaleSubscription, self).get_k8s_env()
        if len(self.partner_id.user_ids) > 0:
            user = self.partner_id.user_ids[0]
            k8s_env.extend([
                "-e",
                r"'s/${OAUTH_CLIENTID}/%s/g'" % self.galicea_openid_id.client_id,
                "-e",
                r"'s/${OAUTH_UID}/%s/g'" % user.id,
            ])
        return k8s_env

    def get_openid_vals(self):
        return {
            'name': self.code_lower,
            'auth_redirect_uri': f'http://{self.website}/auth_oauth/signin'
        }
