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

from osv import orm, fields


class lot_create_revaluation(orm.TransientModel):
    _name = 'lot.create.revaluation'

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', readonly=True, domain=[('type', '!=', 'service')]),
        'lot_id': fields.many2one('stock.production.lot', 'Serial Number', readonly=True, help='Product lot number of Product.'),
        'cost_price': fields.float('Cost Price', help='Cost price of the Product'),
    }

    def default_get(self, cr, uid, fields, context=None):
        """
         Get the default value from invoice line
         ----------------------------------------
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: A List of fields
         @param context: A standard dictionary
         @return: Return a dictionary which hold the field value pair.
        """
        res = super(lot_create_revaluation, self).default_get(cr, uid, fields, context=context)
        lot_data = self.pool.get('stock.production.lot').browse(cr, uid, context.get('active_id'), context=context)
        res.update({'product_id': lot_data.product_id.id, 'lot_id': lot_data.id, 'cost_price': lot_data.cost_price_per_unit})
        return res

    def lot_valuation_create(self, cr, uid, ids, context=None):
        """
         Create a record in Draft Valuation Document from Cost Revaluation wizard
         -------------------------------------------------------------------------
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: A List of ids
         @param context: A standard dictionary
         @return: Return a id which created.
        """
        if context is None:
            context = {}
        res = {}
        revaluation_obj = self.pool.get('lot.valuation')
        for data in self.browse(cr, uid, ids, context=context):
            if data.lot_id:
                res = {
                    'product_id': data.lot_id.product_id.id,
                    'lot_id': data.lot_id.id,
                    'product_uom_id': data.lot_id.product_id.uom_id.id,
                    'existing_cost_price': data.lot_id.cost_price_per_unit,
                    'valuation_cost_price': data.cost_price
                }
                revaluation_obj.create(cr, uid, res, context=context)
        return {'type': 'ir.actions.act_window_close'}

lot_create_revaluation()
