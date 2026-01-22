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
    'name': 'Accounting Reports for PT Eka Maju Mesinindo',
    'version': '1.4',
    'category': 'Accounting & Finance',
    'description': """
    This module provides accounting report menu and the accounting reports.
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'images': [],
    'depends': [
        'via_reports',
        'stock',
        'via_lot_valuation',
        'via_jasper_report_utils_account',
    ],
    'data': [
        'report/inventory/inventory_registration.xml',
        'report/account_receivable_report_by_customer/account_receivable_report_by_customer_registration.xml',
        'report/account_by_partner/account_by_partner_registration.xml',
        'report/trade_account_receivable_list/trade_account_receivable_list_registration.xml',
        'report/account_by_product/account_by_product_registration.xml',
        'wizard/account_receivable_report_by_customer_view.xml',
        'wizard/inventory_report_view.xml',
        'wizard/account_by_partner.xml',
        'wizard/trade_account_receivable_list_view.xml',
        'wizard/account_by_product.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'license': 'GPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
