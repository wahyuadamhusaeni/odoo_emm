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
import time
import decimal_precision as dp

LOT_BASED_METHODS = ['fifo', 'lifo', 'lot_based']
AUTO_ASSIGN_METHODS = ['fifo', 'lifo']


class product_template(orm.Model):
    _inherit = 'product.template'

    _columns = {
        'cost_method': fields.selection([('standard', 'Standard Price'), ('average', 'Average Price'), ('fifo', 'Lot: FIFO'), ('lifo', 'Lot: LIFO'), ('lot_based', 'Lot Based')], 'Costing Method', required=True,
            help="Standard Price: the cost price is fixed and recomputed periodically (usually at the end of the year), Average Price: the cost price is recomputed at each reception of products, FIFO/LIFO/Lot Based :computing stock move / accounting move based their costing move "),
        'old_cost_price': fields.float('Old Cost Price', help="Old Cost Price is stored when you update the Cost Price in Product", digits_compute=dp.get_precision('Purchase Price'))
    }

    def write(self, cr, uid, ids, vals, context=None):
        """
        Overridden the write method to store the old value of the cost price in a field.
        --------------------------------------------------------------------------------
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current Logged in User's Identifier
        @param ids : Record's Identifier(s)
        @param vals : The Dictionary having the field,value pairs to be updated.
        @param context : The Standard Dictionary
        @ return True
        """
        if vals.get('standard_price'):
            cr.execute("UPDATE product_template SET old_cost_price = standard_price WHERE id IN (%s)" % (', '.join(map(lambda x: str(x), ids))))

        return super(product_template, self).write(cr, uid, ids, vals, context=context)

product_template()


class product_product(orm.Model):
    _inherit = 'product.product'

    def _is_lot_based(self, cr, uid, ids, name, args, context=None):
        """
        This determines whether the Product's Cost Method is considered lot based
        -------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Current Records
        @param name: Functional field's name
        @param args: Other arguments
        @param context: standard Dictionary
        @return: Dictionary having identifier of the record as key and is_lot_based boolean values
        """
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = {}
            res[_obj.id].update({'is_lot_based': _obj.track_production or (_obj.cost_method in LOT_BASED_METHODS) or False})
            res[_obj.id].update({'is_auto_assign': (_obj.cost_method in AUTO_ASSIGN_METHODS) or False})

        return res

    def onchange_cost_method(self, cr, uid, ids, cost_method):
        """
        This method adds the new price based on the latest supplier invoice in the Cost Price.
        Also sets the Lots flag if the Cost Method is FIFO, LIFO or Lot Based.
        --------------------------------------------------------------------------------------
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current Logged in User's Identifier
        @param ids : Record's Identifier(s)
        @param cost_method : The Cost method selected in the Product
        @param Dictionary : A Dictionary of values that updates the standard price based on the
        latest supplier invoice and sets the Lots flag.
        """
        res = {}
        # Set the Lot Tracking
        _track = cost_method in LOT_BASED_METHODS
        res_val = ({'track_production': _track, 'track_incoming': _track, 'track_outgoing': _track})
        if _track and ids:
            product_id = ids[0]
            inv_line_obj = self.pool.get('account.invoice.line')
            # Search the cost price from the latest supplier invoice.
            query = """SELECT l.id
                       FROM account_invoice_line l,
                            account_invoice a,
                            account_move m
                       WHERE a.move_id = m.id
                       AND l.invoice_id = a.id
                       AND l.product_id = %s
                       AND a.date_invoice <= %s
                       AND a.type = 'in_invoice'
                       AND a.state in ('open', 'paid')
                       AND m.create_date <= %s
                       ORDER BY m.create_date DESC
                       LIMIT 1"""
            params = (product_id, time.strftime('%Y-%m-%d'), time.strftime('%Y-%m-%d %H:%M:%S'))
            cr.execute(query, params)
            inv_line_id = cr.fetchone()

            # If Latest Invoice is found update the product price with the latest price fetched.
            if inv_line_id:
                inv_line_id = inv_line_id[0]
                inv_line = inv_line_obj.browse(cr, uid, inv_line_id)
                res_val.update({
                    'standard_price': inv_line.price_unit,
                    'old_cost_price': inv_line.product_id.standard_price
                })
                self.write(cr, uid, [product_id], {'standard_price': inv_line.price_unit})

        res.update({'value': res_val})
        return res

    _columns = {
        'is_lot_based': fields.function(_is_lot_based, string='Is Lot Based ?', type='boolean', multi='lot_based'),
        'is_auto_assign': fields.function(_is_lot_based, string='Is Auto Assign ?', type='boolean', multi='lot_based'),
    }

product_product()
