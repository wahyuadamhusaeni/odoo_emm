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

from openerp import netsvc
import time

from openerp.osv import orm, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class claim_move_history(orm.TransientModel):
    _name = 'claim.move.history'
    _description = 'Claimed Move History'

    _columns = {
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial Number',
            help='Serial Number being claimed.'),
        'product_id': fields.related('prodlot_id', 'product_id', type='many2one', relation='product.product', string='Product',
            help='The product being claimed.'),
        'sale_ids': fields.many2many('sale.order', string='Sale Orders',
            help='Sale Order of the claimed product/serial number'),
        'stock_moves': fields.related('prodlot_id', 'move_ids', type='one2many', relation='stock.move', string='Product Moves',
            help='Moves of the claimed product/serial number'),
        'invoice_line': fields.many2many('account.invoice.line', string='Invoiced Lines',
            help='Customer Invoice Lines of the claimed product/serial number'),
    }

    def default_get(self, cr, uid, fields, context=None):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary with default values for all field in ``fields``
        """
        if context is None:
            context = {}

        res = super(claim_move_history, self).default_get(cr, uid, fields, context=context)

        _lot_id = res.get('prodlot_id', False)
        _prodlot_pool = self.pool.get('stock.production.lot')
        _prodlot_id = _lot_id and _prodlot_pool.browse(cr, uid, _lot_id, context=context) or False
        if _prodlot_id:
            _move_ids = []
            _invoice_line_id = []
            _sale_ids = []
            for _move in _prodlot_id.move_ids:
                _move_ids.append(_move.id)
                if _move.sale_line_id:
                    _sale_ids.append(_move.sale_line_id.order_id.id)
                    for line in _move.sale_line_id.invoice_lines:
                        _invoice_line_id.append(line.id)

            if 'product_id' in fields:
                res.update({'product_id':  _prodlot_id.product_id and _prodlot_id.product_id.id or False})

            if 'invoice_line' in fields:
                res.update({'invoice_line':  [(6, 0, list(set(_invoice_line_id)))]})

            if 'stock_moves' in fields:
                res.update({'stock_moves':  list(set(_move_ids))})

            if 'sale_ids' in fields:
                res.update({'sale_ids':  [(6, 0, list(set(_sale_ids)))]})
        return res
