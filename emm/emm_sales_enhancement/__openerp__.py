# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 - 2014 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

{
    'name': 'Sales Enhancements for PT Eka Maju Mesinindo',
    'version': '1.3',
    'category': 'Sales Management',
    'complexity': 'easy',
    'description': """
    This module provides some enhancements to the existing modules used in sales process:
    - Add a revision log to the Sales Order
    - Add blank pricelist placeholders for approval purposes
    - Make Pricelist field in the sale order view readonly and set the pricelist to be customer's pricelist.
    - Provision of email parser for crm.lead model
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',

    'depends': [
        'sale',
        'via_sale_enhancements',
        'emm_product_enhancements',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/add_revision_view.xml',
        'revision_history_view.xml',
        'pricelist_data.xml',
        'company_view.xml',
        'crm_lead_data.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
