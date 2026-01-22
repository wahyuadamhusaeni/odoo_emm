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
    'name': 'Enhancements of cross functionalities between Purchase and HR',
    'version': '1.0',
    'category': 'Purchase Management',
    'complexity': 'easy',
    'description': """
    This module provides enhancements to the existing Purchase and HR modules:
    - Add additional department field to Purchase Requisition refering to HR module department
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'hr',
        'purchase_requisition',
        'via_code_decode',
    ],
    'data': [
        'purchase_requisition_view.xml'
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
