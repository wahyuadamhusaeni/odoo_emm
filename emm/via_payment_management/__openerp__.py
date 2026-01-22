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
    'name': 'VIA Payment Management',
    'version': '1.3',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'description': """
    This module provides a way to manage pre-collected payments and the assignment
    of those payment to related invoices.  The features provided by this module are:
    * Register a payment recording in batch and create entries based on the entered statement lines
    * Attach registered payment against invoice that is not fully paid yet.
    * Attach registered payment against arbitrary entry.
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': ['sale', 'via_account_enhancements'],
    'data': [
        'account_view.xml',
        'via_bank_statement_view.xml',
        'via_bank_statement_workflow.xml',
        'via_expense_voucher_view.xml',
        'via_expense_voucher_workflow.xml',
        'wizard/via_batch_statement_entry_view.xml',
        'wizard/via_assign_payment_view.xml',
        'res_company_view.xml',
        'sale_view.xml',
        'security/via_payment_management_security.xml',
        'security/ir.model.access.csv',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
