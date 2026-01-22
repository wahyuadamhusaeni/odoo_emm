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
    'name': 'Approval List for PT Eka Maju Mesinindo',
    'version': '1.0',
    'description': """
    This module provide Approval Items and Approval Scheme data for PT Eka Maju Mesinindo
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'emm_stock_enhancements',
        'via_approval_account',
        'via_approval_sale',
        'via_approval_stock',
        'via_approval_purchase',
        'via_approval_service',
        'via_approval_report',
        'emm_approval_rma',
    ],
    'data': [
        'stock_view.xml',
        'approval_data.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
