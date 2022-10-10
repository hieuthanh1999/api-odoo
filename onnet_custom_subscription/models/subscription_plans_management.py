# -*- coding: utf-8 -*-
from builtins import set
import logging
import requests
from odoo import api, fields, models, exceptions, _
from werkzeug.urls import url_encode, url_join
from odoo.addons.payment_stripe import utils as stripe_utils
from odoo.addons.payment_stripe.const import API_VERSION, PROXY_URL, WEBHOOK_HANDLED_EVENTS
from odoo.exceptions import ValidationError
from odoo.http import request



_logger = logging.getLogger(__name__)

class SubscriptionPlansManagement(models.Model):
    _inherit = 'product.template'
    _description = "Subscription Plans Management"
    _order = "sequence asc, id desc"

    quantity_user = fields.Integer(string='User quantity', default=1)
    detailed_type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service')], string='Product Type', default='service', required=True,
        help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
             'A consumable product is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.')
    is_subscription_plans = fields.Boolean(string='Subscription Plans', default=False)
    industry = fields.Many2many(comodel_name='industry.management',
                                string="Industry Name",
                                relation='product_template_industry',
                                column1='product_template_id',
                                column2='industry_id')
    tab_module = fields.One2many('tab.category', 'plans', string='Category Management', copy=True, auto_join=True, required=True)
    tab_feature = fields.One2many('tab.feature', 'planss', string='Feature Tab', copy=True, auto_join=True)
    sequence = fields.Integer("Sequence")

    @api.model
    def create(self, vals):
        if vals.get('industry'):
            if len(vals.get('tab_module')) == 0:
                raise exceptions.ValidationError(_('Please select related modules'))
            if vals.get('quantity_user') < 1:
                raise exceptions.ValidationError(_('Please select minimum number of users at least 1'))
            sup = super(SubscriptionPlansManagement, self).create(vals)
        else:
            sup = super(SubscriptionPlansManagement, self).create(vals)
        return sup

    def write(self, vals):
        self._sanitize_vals(vals)
        if self.is_subscription_plans == True:
            if vals.get('quantity_user') and vals.get('quantity_user') < 1:
                raise exceptions.ValidationError(_('Please select minimum number of users at least 1'))
            if vals.get('tab_module'):
                if len(vals.get('tab_module')) == 1:
                    raise exceptions.ValidationError(_('Please select related modules'))
                else:
                    sup = super(SubscriptionPlansManagement, self).write(vals)
                    return sup
            else:
                sup = super(SubscriptionPlansManagement, self).write(vals)
                return sup
        else:
            sup = super(SubscriptionPlansManagement, self).write(vals)
            return sup


    def get_price_with_price_list(self, price_list, quantity):
        pro_info = self._get_combination_info(False, int(self.product_variant_id.id or 0), int(quantity), price_list)
        return pro_info['price']


class PaymentAcquirerInherit(models.Model):
    _inherit = 'payment.acquirer'
    def _stripe_make_request(self, endpoint, payload=None, method='POST', offline=False):
        """ Make a request to Stripe API at the specified endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request
        :param dict payload: The payload of the request
        :param str method: The HTTP method of the request
        :param bool offline: Whether the operation of the transaction being processed is 'offline'
        :return The JSON-formatted content of the response
        :rtype: dict
        :raise: ValidationError if an HTTP error occurs
        """
        self.ensure_one()
        email_support = request.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.email_support')
        url = url_join('https://api.stripe.com/v1/', endpoint)
        headers = {
            'AUTHORIZATION': f'Bearer {stripe_utils.get_secret_key(self)}',
            'Stripe-Version': API_VERSION,  # SetupIntent requires a specific version.
            **self._get_stripe_extra_request_headers(),
        }
        try:
            response = requests.request(method, url, data=payload, headers=headers, timeout=60)
            # Stripe can send 4XX errors for payment failures (not only for badly-formed requests).
            # Check if an error code is present in the response content and raise only if not.
            # See https://stripe.com/docs/error-codes.
            # If the request originates from an offline operation, don't raise and return the resp.
            if not response.ok \
                    and not offline \
                    and 400 <= response.status_code < 500 \
                    and response.json().get('error'):  # The 'code' entry is sometimes missing
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError:
                    _logger.exception("invalid API request at %s with data %s", url, payload)
                    error_msg = response.json().get('error', {}).get('message', '')
                    raise ValidationError(
                        "Stripe: " + _(
                            "%s Please contact our Support Team %s.",  error_msg, email_support
                        )
                    )
        except requests.exceptions.ConnectionError:
            _logger.exception("unable to reach endpoint at %s", url)
            raise ValidationError("Stripe: " + _("Could not establish the connection to the API."))
        return response.json()