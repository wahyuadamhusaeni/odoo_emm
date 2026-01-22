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
    'name': 'Account Enhancements for PT Eka Maju Mesinindo',
    'version': '1.1',
    'category': 'Generic Modules/Accounting',
    'complexity': 'easy',
    'description': """
This module provide enhancements to account related modules specific for PT Eka Maju Mesinindo:
- Removing menu_action_purchase_receipt (Purchase Receipts) and menu_action_sale_receipt (Sales Receipts)
- Adding domain that Partner that can be selected in Account Invoice is Partner that is a company or of
  type Invoice or Default
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'account_voucher',
    ],
    'data': [
        'account_voucher_view.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
