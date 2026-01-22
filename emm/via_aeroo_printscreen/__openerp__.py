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
    "name": 'VIA Aeroo Print Sceen Enhancement',
    "version": '1.0',
    "author": "PT. Vikasa Infinity Anugrah",
    "category": 'VIA/Reporting',
    "description": """
        Enhances Alistek's Print Screen to cater for slectively filtering out columns that are not visible or columns in which the user has no right to access.
    """,
    "website": "http://www.infi-nity.com",
    "license": "GPL-3",
    "depends": [
        'report_aeroo_printscreen',
    ],
    "data": [
        'data/module_data.xml',
    ],
    "update_xml": [],
    "js": [],
    "installable": True,
    "active": False,
}
