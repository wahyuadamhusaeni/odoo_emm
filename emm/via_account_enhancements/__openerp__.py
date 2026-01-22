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
    'name': 'VIA Account Enhancements',
    'version': '1.4',
    'category': 'Accounting & Finance',
    'complexity': 'easy',
    'description': """
    This module provides some enhancements to the existing modules used in accounting process:
    * Add signed residual amount in account_move_line calculating from reconciled entries
    * Add permutations of totals (base + disc + tax) in the Invoice and Invoice Line
    * Fix the {'type': parent.type} context error when calling account.invoice.line form view
      from views other than account.invoice's form view
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'account',
    ],
    'data': [
        'account_view.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
