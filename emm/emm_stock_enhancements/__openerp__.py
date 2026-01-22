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
    'name': 'Warehouse Management Enhancements for PT Eka Maju Mesinindo',
    'version': '1.7',
    'category': 'Warehouse Management',
    'complexity': 'normal',
    'description': """
    This module provides some enhancements to the existing modules used in stock process:
    - Provide Serial Number (stock.production.lot) creation and assignment function,
      in place of the original method provided by product_serial
    - Feature to attach documents to Serial Number (stock.production.lot) from Stock Move
    - Restrict access to Force Availability to Manager
    - Add messaging and notes logging to Serial Number (stock.production.lot)
    - Allow user to specify Destination Location upon Receive in Delivery Order
    - Add a flag in Delivery Order to indicate that the document is ready for transfer
    - Simplification of some views
    - Make Internal Reference of Product to be unique
    - Add Customer mobile and phone number to the Delivery Order
    - Add control to uniquenss of Product Category Code
    - Add Barcode Printing functionality from Serial Number and Incoming Shipment
    - Add Barcode scanning processing on Delivery Order and Incoming Shipment form views
    - Enhanced stock.picking splitting
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'via_stock_enhancements',
        'via_lot_valuation',
        'product_serial',
        'via_web',
        'stock_split_picking',
    ],
    'data': [
        'stock_view.xml',
        'product_category_view.xml',
        'wizard/attach_doc_to_lot_view.xml',
        'wizard/prodlot_wizard_view.xml',
        'wizard/destination_view.xml',
        'wizard/stock_view.xml',
        'report/print_barcode_view.xml',
        'report/print_barcode_data.xml',
    ],
    'test': [
    ],
    'js': [
        'static/src/js/emm_stock_enhancements_main.js',
    ],
    'css': [
    ],
    'qweb': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
