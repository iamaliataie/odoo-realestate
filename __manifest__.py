# -*- coding: utf-8 -*-
{
    'name': "Real Estate",

    'summary': """
        Real Estate Management to manage your property business
    """,

    'description': """
        Real Estate Management to manage your property business"
    """,

    'author': "Ali Ahmad Ataie",
    'website': "https://ataie.pythonanywhere.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Services',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],
    'application': True,
    'sequence': -1000,

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
