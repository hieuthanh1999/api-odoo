# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    contact_us_form = fields.Selection([
        ('enabled', 'Enabled'),
        ('disabled', 'Disabled'),
    ], default='disabled', string='Enable Contact Us for Trial Process')
    image_invite = fields.Binary('Image Screen Invite', readonly=False)
    image_done = fields.Binary('Image Screen Done', readonly=False)

    trial_period = fields.Integer(string='Trial period (days)')
    extension_date = fields.Integer(string='Extension Date (days)')
    count_trial = fields.Integer(string='Number of times to buy trial (Number)', default=1)
    max_number_user = fields.Integer(string='Maximum number of users per plan', config_parameter='onnet_custom_subscription.max_number_user', default= 20)
    # db_expiration_time = fields.Integer(string='Database expiration time (days)')
    instance_removal_period_trial = fields.Integer(string='Instance removal period for Trial description plans (days)')
    instance_removal_period_active = fields.Integer(
        string='Instance removal period for Active description plans (days)')
    user_product_subscription_id = fields.Many2one('product.template',
                                                   string='User Product',
                                                   domain="[('detailed_type', '=', 'service')]",
                                                   config_parameter='onnet_custom_subscription.user_product_subscription',
                                                   help="A product that represents the number of user for a subscription",
                                                   default=lambda self: self.env.ref(
                                                       'onnet_custom_subscription.default_user_product_subscription',
                                                       False))
    annually_product_pricelist_id = fields.Many2one('product.pricelist',
                                                    string='Annually pricelist',
                                                    config_parameter='onnet_custom_subscription.annually_product_pricelist',
                                                    default=lambda self: self.env.ref(
                                                        'onnet_custom_subscription.default_annually_product_pricelist',
                                                        False))
    month_product_pricelist_id = fields.Many2one('product.pricelist',
                                                 string='Month pricelist',
                                                 config_parameter='onnet_custom_subscription.month_product_pricelist',
                                                 default=lambda self: self.env.ref(
                                                     'onnet_custom_subscription.default_month_product_pricelist',
                                                     False))
    product_category_addons_id = fields.Many2one('product.category',
                                                 string='Category Addons',
                                                 config_parameter='onnet_custom_subscription.product_category_addons',
                                                 default=lambda self: self.env.ref(
                                                     'onnet_custom_subscription.default_product_category_addons',
                                                     False))
    product_category_subscription_id = fields.Many2one('product.category',
                                                       string='Category Subscription',
                                                       config_parameter='onnet_custom_subscription.product_category_subscription',
                                                       default=lambda self: self.env.ref(
                                                           'onnet_custom_subscription.default_product_category_subscription',
                                                           False))
    trial_field = fields.Many2one('sale.subscription.stage',
                                  string='Trial Order',
                                  config_parameter='onnet_custom_subscription.sale_subscription_trial',
                                  default=lambda self: self.env.ref(
                                      'onnet_custom_subscription.default_sale_subscription_trial',
                                      False))

    trial_expired_field = fields.Many2one('sale.subscription.stage',
                                          string='Trial Expired',
                                          config_parameter='onnet_custom_subscription.sale_subscription_trial_expired',
                                          default=lambda self: self.env.ref(
                                              'onnet_custom_subscription.default_sale_subscription_trial_expired',
                                              False))

    dunning_field = fields.Many2one('sale.subscription.stage',
                                    string='Dunning',
                                    config_parameter='onnet_custom_subscription.sale_subscription_dunning',
                                    default=lambda self: self.env.ref(
                                        'onnet_custom_subscription.default_sale_subscription_dunning',
                                        False))


    cancelled_field = fields.Many2one('sale.subscription.stage',
                                    string='Dunning',
                                    config_parameter='onnet_custom_subscription.sale_subscription_cancelled',
                                    default=lambda self: self.env.ref(
                                        'onnet_custom_subscription.default_sale_subscription_cancelled',
                                        False))

    draft_field = fields.Many2one('sale.subscription.stage',
                                  string='Unpaid Order',
                                  config_parameter='onnet_custom_subscription.sale_subscription_draft',
                                  default=lambda self: self.env.ref(
                                      'onnet_custom_subscription.default_sale_subscription_draft',
                                      False))
    progress_field = fields.Many2one('sale.subscription.stage',
                                     string='Progress Order',
                                     config_parameter='onnet_custom_subscription.sale_subscription_progress',
                                     default=lambda self: self.env.ref(
                                         'onnet_custom_subscription.default_sale_subscription_progress',
                                         False))
    closed_field = fields.Many2one('sale.subscription.stage',
                                   string='Closed Subscription',
                                   config_parameter='onnet_custom_subscription.sale_subscription_closed',
                                   default=lambda self: self.env.ref(
                                       'onnet_custom_subscription.default_sale_subscription_closed',
                                       False))
    maintain_field = fields.Many2one('sale.subscription.stage',
                                     string='Maintain Subscription',
                                     config_parameter='onnet_custom_subscription.sale_subscription_maintain',
                                     default=lambda self: self.env.ref(
                                         'onnet_custom_subscription.default_sale_subscription_maintain',
                                         False))
    annually_template = fields.Many2one('sale.subscription.template',
                                        string='Annually Template',
                                        config_parameter='onnet_custom_subscription.annually_template',
                                        default=lambda self: self.env.ref(
                                            'onnet_custom_subscription.default_annually_template',
                                            False))
    monthly_template = fields.Many2one('sale.subscription.template',
                                       string='Monthly Template',
                                       config_parameter='onnet_custom_subscription.monthly_template',
                                       default=lambda self: self.env.ref(
                                           'onnet_custom_subscription.default_monthly_template',
                                           False))
    trial_template = fields.Many2one('sale.subscription.template',
                                     string='Trial Template',
                                     config_parameter='onnet_custom_subscription.trial_template',
                                     default=lambda self: self.env.ref(
                                         'onnet_custom_subscription.default_trial_template',
                                         False))

    config_domain = fields.Char(string='Default domain', config_parameter='onnet_custom_subscription.config_domain',
                                default='hiiboss.com')
    user_product_extend_id = fields.Many2one('product.template',
                                             string='Product Extend',
                                             domain="[('detailed_type', '=', 'service')]",
                                             config_parameter='onnet_custom_subscription.user_product_extend',
                                             help="A product extend of order subscription",
                                             default=lambda self: self.env.ref(
                                                 'onnet_custom_subscription.default_user_product_extend',
                                                 False))
    monthly_billing_period = fields.Integer(string='Default monthly',
                                            config_parameter='onnet_custom_subscription.monthly_billing_period',
                                            default=30)
    yearly_billing_period = fields.Integer(string='Default yearly',
                                           config_parameter='onnet_custom_subscription.yearly_billing_period',
                                           default=360)
    text_popular = fields.Char(string='Default popular',
                               config_parameter='onnet_custom_subscription.text_popular',
                               default='Most Popular')

    email_support = fields.Char(string='Email support',
                               config_parameter='onnet_custom_subscription.email_support',
                               default='support@hiiboss-auto.com')

    # Website Fields
    plans_title = fields.Char(string='Plans Title', config_parameter='onnet_custom_subscription.plans_title',
                              default='Subscription Plans')
    plans_title_content = fields.Char(string='Plans Title Content', translate=True,
                                      config_parameter='onnet_custom_subscription.plans_title_content',
                                      default='Grow your business without the busy work')

    @api.constrains('count_trial')
    def _check_value(self):
        if self.count_trial < 0:
            raise ValidationError(_('Please enter a positive number'))

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['contact_us_form'] = \
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.contact_us_form', default='disabled')
        res['image_invite'] = \
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.image_invite')
        res['image_done'] = \
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.image_done')
        res['trial_period'] = \
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.trial_period', default=15)
        res['count_trial'] = \
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.count_trial', default=1)
        res['extension_date'] = \
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.extension_date', default=7)
        res['instance_removal_period_trial'] = \
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.period_trial', default=90)
        res['instance_removal_period_active'] = \
            self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.period_active', default=180)
        return res


    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('onnet_custom_subscription.contact_us_form', self.contact_us_form),
        self.env['ir.config_parameter'].sudo().set_param('onnet_custom_subscription.image_invite',
                                                         self.image_invite),
        self.env['ir.config_parameter'].sudo().set_param('onnet_custom_subscription.image_done',
                                                         self.image_done),
        self.env['ir.config_parameter'].sudo().set_param('onnet_custom_subscription.trial_period',
                                                         self.trial_period)
        self.env['ir.config_parameter'].sudo().set_param('onnet_custom_subscription.extension_date',
                                                         self.extension_date)
        self.env['ir.config_parameter'].sudo().set_param('onnet_custom_subscription.count_trial',
                                                         self.count_trial)
        self.env['ir.config_parameter'].sudo().set_param('onnet_custom_subscription.period_trial',
                                                         self.instance_removal_period_trial)
        self.env['ir.config_parameter'].sudo().set_param('onnet_custom_subscription.period_active',
                                                         self.instance_removal_period_active)
        super(ResConfigSettings, self).set_values()
