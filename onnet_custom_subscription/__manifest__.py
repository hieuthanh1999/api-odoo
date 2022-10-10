# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Onnet Sale Subscription',
    'version': '1.1',
    'author': 'ThanhNH',
    'summary': 'Onnet Sale Subscription Module',
    'sequence': 10,
    'description': """
Invoicing & Payments
====================
The specific and easy-to-use Invoicing system in Odoo allows you to keep track of your accounting, even when you are not an accountant. It provides an easy way to follow up on your vendors and customers.

You could use this simplified accounting in case you work with an (external) account to keep your books, and you still want to keep track of payments. This module also offers you an easy method of registering payments, without having to encode complete abstracts of account.
    """,
    'depends': ['sale_subscription', 'product', 'website', 'base', 'account', 'onnet_custom_error'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/modules_management_views.xml',
        'views/industry_management_views.xml',
        'views/subscription_plans_management_views.xml',
        'views/add_ons_management_views.xml',
        'views/website_menu_plans.xml',
        'views/website_index_plans.xml',
        'views/category_management_views.xml',
        'views/firework.xml',
        'views/res_config_settings_views.xml',
        'views/email_dunning_payment_views.xml',
        'views/template_email_active_views.xml',
        'views/template_email_active_trial_views.xml',
        'views/inherit_report_invoice_document_views.xml',
        'views/website_plans_views.xml',
        'views/error_instance_views.xml',
        'views/inherit_res_partner_views.xml',
        'views/expired_version_views.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        "web.assets_frontend": [
            "/onnet_custom_subscription/static/src/css/owl.carousel.css",
            "/onnet_custom_subscription/static/src/css/style_guide.css",
            "/onnet_custom_subscription/static/src/js/owl.carousel.min.js",
            "/onnet_custom_subscription/static/src/css/style.css",
            "/onnet_custom_subscription/static/src/css/firework.css",
            "/onnet_custom_subscription/static/src/js/carousel_plans.js",
            "/onnet_custom_subscription/static/src/js/filework.js",
        ],
    },
}
