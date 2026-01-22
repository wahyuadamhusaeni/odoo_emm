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
    'name': 'Jasper Reports Utility for Human Resource Related Functions',
    'version': '1.0',
    'category': 'Reporting',
    'description': """
    This module adds functionalities required to support Human Resource related
    functions to the utility Jasper Reports Utility framework.
    """,
    'author': 'PT. Vikasa Infinity Anugrah',
    'website': 'http://www.infi-nity.com/',
    'depends': [
        'via_jasper_report_utils',
        'hr',
    ],
    'init_xml': [],
    'update_xml': [
        'framework_main_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
}
