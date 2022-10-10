# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Onnet Customer signup',
    'version': '1.1',
    'summary': 'Onnet Customer signup software',
    'sequence': 10,
    'author': 'Mai',
    'description': """Onnet Customer signup software""",
    'category': 'Uncategorized',
    'website': 'https://www.odoo.com',
    'depends': [
        'base','portal',
        'onnet_custom_error',
        'sale_subscription',
        'product',
        'onnet_custom_subscription',
        'website_sale', 'crm', 'base',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'views/templates.xml',
        'views/common.xml',
        'views/inherit_lead_views.xml',
        'views/email_active_sale.xml',
        'wizard/sale_subscription_close_reason_wizard_views.xml',
        'views/view_custom.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web.assets_frontend': [
            '/onnet_customer_signup/static/src/css/customer_style_sheet.css',
            # '/onnet_customer_signup/static/src/js/user_custom_javascript.js',
            '/onnet_customer_signup/static/src/js/intlTelInput.js',
            '/onnet_customer_signup/static/src/js/main.js',
            '/onnet_customer_signup/static/src/js/detail_page.js',
            '/onnet_customer_signup/static/src/js/jquery_validate.js'
        ]
    },
    'license': 'LGPL-3',
}
