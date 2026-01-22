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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class stock_picking_prodlot_assign_wizard(orm.TransientModel):
    _name = 'stock.picking.prodlot.assign'

    def split_lot(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        picking_id = context.get('active_id', False)
        pick_obj = self.pool.get('stock.picking')
        picking = pick_obj.browse(cr, uid, picking_id, context=context)
        prodlot_obj = self.pool.get('stock.production.lot')
        move_obj = self.pool.get('stock.move')
        for move in picking.move_lines:
            prodlot_id = move.prodlot_id
            if not prodlot_id:
                if pick_obj._check_split(move) and (move.product_qty >= 1.0):
                    _mv_ids = move.split_move(context=context)
                    for _new_move in move_obj.browse(cr, uid, _mv_ids, context=context):
                        prodlot_id = prodlot_obj.create(cr, uid, {
                            'product_id': _new_move.product_id.id,
                        },
                            context=context)
                        _new_move.write({'prodlot_id': prodlot_id})

        return {'type': 'ir.actions.act_window_close'}
