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


class split_in_production_lot(orm.TransientModel):
    _inherit = 'stock.move.split'

    def split(self, cr, uid, ids, move_ids, context=None):
        """
        To split stock moves into production lot and write purchase order line
        price in product lot's cost price.
        ---------------------------------------------------------------------
        @param self : object pointer
        @param cr : database cursor
        @param uid : current logged in user
        @param move_ids: the ID or list of IDs of stock move we want to split
        @return: New Created move ids.
        """
        res = super(split_in_production_lot, self).split(cr, uid, ids, move_ids, context=context)

        # Update the Cost Price Per Unit matching the corresponding Purchase Price in Company's Currency
        uom_obj = self.pool.get('product.uom')
        _co_ccy_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        _ccy_pool = self.pool.get('res.currency')
        for moves in self.pool.get('stock.move').browse(cr, uid, res, context=context):
            _line = moves.purchase_line_id
            if _line and moves.prodlot_id:
                # Covert Price Unit to Company's Currency
                _pol_ccy = _line.order_id.pricelist_id.currency_id.id
                _price = _line.price_unit
                if _co_ccy_id != _pol_ccy:
                    _ctx = {'date': _line.date_order}
                    _price = _ccy_pool.compute(cr, uid, _pol_ccy, _co_ccy_id, _price, context=_ctx)

                # Account for UOM Difference (Purchase Line's UOM vs Production Lot's Product UOM)
                # If Purchase Line's UOM is not specified, assume that it will use Product UOM
                _pol_uom = _line.product_uom and _line.product_uom.id or _line.product_id.uom_id.id or False
                _prod_uom = moves.prodlot_id.product_id.uom_id.id or False
                if _pol_uom != _prod_uom:
                    _price = uom_obj._compute_price(cr, uid, _pol_uom, _price, to_uom_id=_prod_uom)

                moves.prodlot_id.write({'cost_price_per_unit': _price}, context=context)

        return res

split_in_production_lot()
