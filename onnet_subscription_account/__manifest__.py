{
    "name": "Onnet Subscription Account",
    "summary": """ Some custom Subscription Account of Onnet""",
    "version": "1.0.0",
    'author': 'ThanhNH',
    'depends': ['sale_subscription', 'onnet_customer_signup', 'onnet_custom_subscription', 'payment', 'website_sale', 'base'],
    'data': [
        'views/subscription_account.xml',
        'views/inherit_form_sale_stage_views.xml',
        'views/search_inherit_sale_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web.assets_frontend': [
            '/onnet_subscription_account/static/src/css/modal_style.css',
            '/onnet_subscription_account/static/src/js/modal_plans.js',
            '/onnet_subscription_account/static/src/js/sweet_alert.js'
        ]
    },
}
