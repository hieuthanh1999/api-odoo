from odoo.http import request
from odoo import http, _
from odoo.exceptions import AccessDenied
import logging
import json


_logger = logging.getLogger(__name__)


class SubscriptionController(http.Controller):

    @http.route('/subscription/admin/update', type="json", methods=["POST", "GET"],  auth='none', csrf=False, website=True)
    def update_admin_password(self):
        params = json.loads(request.httprequest.get_data().decode(request.httprequest.charset))
        sub_code = params.get('code', False)
        old_password_hashed = params.get('old_password_hashed', False)
        new_password = params.get('new_password', False)

        if not all([sub_code, old_password_hashed, new_password]):
            raise AccessDenied(_("Not enough params"))
        subscription = request.env['sale.subscription'].sudo().search([('code', '=', sub_code.upper())])
        if subscription:
            verify = request.env['res.users'].sudo()._crypt_context().verify(subscription.admin_password, old_password_hashed)
            if verify:
                subscription.with_context(ignore_update_admin_pwd=True).write({'admin_password': new_password})
        return json
