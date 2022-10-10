# -*- encoding: utf-8 -*-
{
    'name': 'Theme HiiBoss',
    'category': 'Theme/corporate',
    'sequence': 1000,
    'version': '1.1',
    'license': 'OPL-1',
    'author': 'Atharva System',
    'support': 'support@atharvasystem.com',
    'website' : 'https://www.atharvasystem.com',
    'depends': ['website'],
    'data': [
        'security/ir.model.access.csv',
        'views/headers/headers.xml',
        'views/headers/switch.xml',
        'views/footers/footers.xml',
        'views/footers/switch.xml',
        'views/s_snippets.xml',
        'views/s_services.xml',
        'views/s_feature_slider.xml',
        'views/service_view.xml',
        'views/feature_slider_view.xml',
        'views/megamenu/megamenu.xml',
        'data/ir_assets.xml',

    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_hiiboss/static/src/scss/assets_primary_variables/hiiboss_primary_variables.scss'
        ],
        'web._assets_frontend_helpers': [
            'theme_hiiboss/static/src/scss/assets_frontend_helpers/hiiboss_frontend_helpers.scss',
        ],
        'web.assets_frontend':[
            'theme_hiiboss/static/src/lib/swiper-bundle.min.css',
            'theme_hiiboss/static/src/lib/swiper-bundle.min.js',
            'theme_hiiboss/static/src/scss/snippet.scss',
        ],
        'website.assets_editor':[
            'theme_hiiboss/static/src/js/s_service_snippet/options.js',
            'theme_hiiboss/static/src/js/s_feature_snippet/options.js',
        ],
        'web.assets_qweb': [
            'theme_hiiboss/static/src/xml/service_dialog.xml',
            'theme_hiiboss/static/src/xml/feature_dialog.xml',
        ],
    },
    'snippet_lists': {
        'homepage': ['s_cover', 's_text_image', 's_image_text', 's_masonry_block', 's_call_to_action', 's_picture'],
        'about_us': ['s_text_image', 's_image_text', 's_title', 's_company_team'],
        'our_services': ['s_three_columns', 's_quotes_carousel', 's_references'],
        'pricing': ['s_comparisons'],
        'privacy_policy': ['s_faq_collapse'],
    },
    'application': False,
    'auto_install': False,
}
