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
    'name': 'Product Enhancements for PT Eka Maju Mesinindo',
    'version': '1.1',
    'category': 'Sales Management',
    'complexity': 'normal',
    'description': """
    This module provides some enhancements to the existing modules related to product:
    - Make Product's Internal Reference to be auto-generated and read-only
    - Provision of Product Price listing feature
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'product',
        'via_code_decode'
    ],
    'data': [
        'product_sequence.xml',
        'product_view.xml',
        'price_list_view.xml',
        'code_category.xml',
        'product_pricelist_form_view.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
