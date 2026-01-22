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
    'name': 'Sales Enhancements',
    'version': '1.4',
    'category': 'Sales Management',
    'complexity': 'normal',
    'description': """
    This module provides some enhancements to the existing modules used in sales process:
    * Enable sale order line id on stock move form
    * Fix the calculation of invoiced fields to make it based on SO's amount_untaxed
    * Provide a generic mechanism to attach additional information to Sales Order
    * Removes newline characters when preparing stock.moves' name it is a char field
    * Inclusion of changes introduced to OpenERP Add-Ons Trunk by
      https://code.launchpad.net/~openerp-dev/openobject-addons/trunk-improve-traceback-issues8-bth/+merge/140138.
      to fix the fact that account.invoice.line's product_id_change() does not accept keyword argument 'uom_id'
      anymore
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'account',
        'sale',
        'stock',
        'sale_stock'
    ],
    'data': [
        'sale_enhancement_data.xml',
        'stock_view.xml',
        'sale_view.xml',
        'account_invoice_view.xml',
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
