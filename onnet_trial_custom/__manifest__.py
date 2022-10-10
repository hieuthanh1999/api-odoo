{
    "name": "Onnet Trial",
    "summary": """ Some custom Trial of Onnet""",
    "version": "1.0.0",
    'author': 'ThanhNH',
    'depends': ['mail', 'onnet_subscription_account', 'onnet_customer_signup',],
    'data': [
        'views/sign_in_views.xml',
        'views/comfirm_password_views.xml',
        'views/invite_screen_views.xml',
        'views/done_screen_views.xml',
        'views/template_email_views.xml',
        'views/hiiboss_move_screen_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web.assets_frontend': [
            '/onnet_trial_custom/static/src/css/modal_style.css',
            '/onnet_trial_custom/static/src/js/sign_in.js'
        ]
    },
}
