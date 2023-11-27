# -*- coding: utf-8 -*-

{
    'name': 'New PDF Reports',
    'version': '16.0.1.0.0',
    'category': 'Invoicing Management',
    'description': 'PDF Reports For Odoo 16, Accounting Financial Reports, '
                   'Odoo 16 Financial Reports',
    'summary': 'PDF Reports For Odoo 16',
    'sequence': '-100',
    'author': 'Odoo Mates, Odoo SA',
    'license': 'LGPL-3',
    'company': 'Odoo Mates',
    'maintainer': 'Odoo Mates',
    'support': 'odoomates@gmail.com',
    'website': 'https://www.youtube.com/watch?v=yA4NLwOLZms',
    'depends': ['base','account','web'],

    'data': [
        'security/ir.model.access.csv',
         'rerport/customer_wizard_report_action.xml',
        'rerport/customer_wizard_report_template.xml',

        'wizard/customer_wizard_report.xml',
    ],

    'application': True,
    'auto_install': False,

}
