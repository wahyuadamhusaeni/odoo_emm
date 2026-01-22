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
    "name": "VIA Financial Reports",
    "version": "1.2",
    'category': 'VIA/Reporting/Accounting',
    "author": "Vikasa Infinity Anugrah, PT",
    'description': """
    This module provides financial report menu and the financial reports.
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    "website": "http://www.infi-nity.com",
    'images': [],
    "depends": [
        'base',
        'account',
        'via_jasper_report_utils_account',
        'decimal_precision',
        'via_reporting_tree',
    ],
    'data': [
        'security/via_financial_reports_security.xml',
        'res_company_view.xml',
        'via_reporting_tree_registration.xml',
        'report/reporting_service_registration.xml',
        'account_view.xml',
        'report/trial_balance/trial_balance_registration.xml',
        'report/general_ledger/general_ledger_registration.xml',
        'report/cash_flow/cash_flow_registration.xml',
        'menu.xml',
        'wizard/cash_flow_view.xml',
        'wizard/trial_balance_view.xml',
        'wizard/general_ledger_view.xml',
        'wizard/financial_reports_view.xml',
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
