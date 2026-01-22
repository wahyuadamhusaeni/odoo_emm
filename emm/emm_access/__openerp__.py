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
    'name': "Access Rights for PT Eka Maju Mesinindo",
    'version': '1.0',
    'category': 'Security & Access',
    'description': """
Defines changes in views that correlates to access right requirement from PT Eka Maju Mesinindo
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'purchase',
        'sale',
        'product_price_currency',
        'via_stock_enhancements',
        'via_lot_valuation',
        'emm_approval',
    ],
    'data': [
        'sale_view.xml',
        'purchase_view.xml',
        'stock_view.xml',
        'product_view.xml',
        'res_partner_view.xml',
    ],
    'images': [
    ],
    'installable': True,
    'auto_install': False,
}
