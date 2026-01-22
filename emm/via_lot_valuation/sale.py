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

from osv import orm
from tools.translate import _
from via_base_enhancements.tools import prep_dict_for_write


class sale_order(orm.Model):
    _inherit = 'sale.order'

    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """
        This method is creating move of the product from prodution Lot Based on FIFO/LIFO costing method
        ------------------------------------------------------------------------------------------------
        @param self: ojbect pointer
        @param cr: database cursor
        @param uid: current logged in user
        @param order: browse record of sale order
        @param order_lines: contain list of browse moves of sale order
        @param picking_id: contain delivery order's id of created from sale order
        @param context: Standard Dictionary
        """
        result = super(sale_order, self)._create_pickings_and_procurements(cr, uid, order, order_lines, picking_id, context)
        _fields_to_move = ['picking_id', 'product_id', 'date', 'date_expected', 'product_uom', 'product_packaging', 'location_id', 'location_dest_id', 'sale_line_id', 'state', 'note', 'company_id']
        uom_obj = self.pool.get('product.uom')
        lot_obj = self.pool.get('stock.production.lot')
        stock_move_obj = self.pool.get('stock.move')
        for picking in order.picking_ids:
            for move in picking.move_lines:
                if move.product_id.is_auto_assign:
                    move_vals = move.read(context=context)
                    move_vals = move_vals and prep_dict_for_write(cr, uid, move_vals[0], context=context) or {}
                    for k in move_vals.keys():
                        if k not in _fields_to_move:
                            del move_vals[k]

                    _prod_uom = move.product_id and move.product_id.uom_id.id or False
                    _move_uom = ((move.product_uom and move.product_uom.id) or
                                (move.product_uos and move.product_uos.id) or
                                _prod_uom)

                    move_vals.update({
                        'name': move.product_id.name,
                        'product_uos_qty': (move.product_uos and move.product_uos_qty) or move.product_qty,
                        'product_uos': _move_uom,
                        'address_id': move.address_id.id or move.picking_id.sale_id.partner_shipping_id.id,
                    })

                    # Get all available Production Lot sorted based on the Product's Cost Method
                    _res = lot_obj.get_available_lots(cr, uid,
                        product_id=move.product_id.id,
                        location_id=move.location_id.id,
                        context=context)

                    # Auto assign based on available Production Lots
                    _req_qty = move.product_qty
                    if (_move_uom != _prod_uom):
                        # Required Quantity is converted into Product's UOM for ease of calculation
                        _req_qty = uom_obj._compute_qty(cr, uid, _move_uom, _req_qty, _prod_uom)

                    _first = True
                    for _lot_info in _res:
                        if _req_qty <= 0:
                            # Till required quantity is fulfilled
                            break

                        _pl_id = _lot_info.get('prodlot_id', False)
                        _lot_qty = _lot_info.get('qty', 0.0)
                        _qty_to_consume = min(_req_qty, _lot_qty)

                        # Only consume if there is quantity to consume
                        if _qty_to_consume:
                            _update_val = {
                                'prodlot_id': _pl_id,
                                'product_qty': _qty_to_consume,
                            }

                            if _first:
                                _first = False
                                # Quantity from first lot is logged to the move
                                move.write(_update_val, context=context)
                            else:
                                # Quantity from subsequent lots is logged in different move
                                move_data = move_vals.copy()
                                move_data.update(_update_val)
                                stock_move_obj.create(cr, uid, move_data, context=context)

                            _req_qty -= _qty_to_consume

                    if _req_qty > 0 and not _first:
                        # Create one last move without Production Lot if this is not the first
                        # Don't change anything if it is the first
                        _update_val = {
                            'prodlot_id': False,
                            'product_qty': _req_qty,
                        }
                        move_data = move_vals.copy()
                        move_data.update(_update_val)
                        stock_move_obj.create(cr, uid, move_data, context=context)

        return result

sale_order()
