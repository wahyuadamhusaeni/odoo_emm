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
    'name': 'Lot Valuation',
    'version': '1.44.1',
    'category': 'Warehouse Management',
    'complexity': 'normal',
    'description': """
      The main purpose of this module is to provide product valuation with lot based valuation (including FIFO and LIFO).
      You can have the following features incorporated.
       * New Cost Methods are introduced FIFO, LIFO and Lot Based.
       * It lets you create valuation/revaluation documents based on the newly added cost methods.
       * It also lets you update the standard_price based on the latest supplier invoice.
       * You can set tracking based on the cost methods.
       * You can add Production Lot in invoice and Cost Price in the production Lot.
       * If stock valuation is being peformed on new cost methods update the cost price based on the lot.
       * Based on costing method FIFO/LIFO creating moves in Delievery Order depends on Production Lot When Sale Order Confirmed
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'account',
        'product',
        'via_stock_enhancements',
        'sale',
        'sale_stock',
        'purchase',
        'via_company_journal_default',
    ],
    'data': [
        'wizard/lot_create_revaluation_view.xml',
        'wizard/cost_revaluation_view.xml',
        'product_view.xml',
        'stock_view.xml',
        'invoice_view.xml',
        'lot_valuation_view.xml',
        'lot_valuation_workflow.xml',
        'security/ir.model.access.csv',
        'lot_valuation_data.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
