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
    'name': 'Warehouse Management Enhancements',
    'version': '1.3',
    'category': 'Warehouse Management',
    'complexity': 'normal',
    'description': """
    This module provides some enhancements to the existing modules used in stock process:
    * Add link between stock move and account move on stock move form
    * Fix Product Lot creation from Partial Stock Move and Partial Stock Picking wizards
      by defaulting the Product ID
    * Display the address in Delivery Order
    * Fix incorrect sequence name when Partial Picking is executed on Internal Moves listed
      in https://bugs.launchpad.net/openobject-addons/+bug/1200619
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'stock',
    ],
    'data': [
        'stock_view.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
