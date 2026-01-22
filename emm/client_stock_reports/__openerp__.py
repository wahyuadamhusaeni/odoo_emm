# -*- encoding: utf-8 -*-
###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
#
###############################################################################

{
    'name': 'Client Inventory Reports',
    'version': '1.0',
    'category': 'Reporting/Inventory',
    'description': """
    This module provides inventory related report and report menus.
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'images': [],
    'depends': [
        'via_jasper_report_utils_stock',
    ],
    'data': [
        'report/inventory/inventory_registration.xml',
        'wizard/inventory_report_view.xml',
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
