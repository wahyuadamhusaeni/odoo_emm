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
import decimal_precision as dp
from tools.translate import _
import time


class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    # Pass the product lot when invoice line create
    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id, invoice_vals, context=None):
        """ Builds the dict containing the values for the invoice line
        ---------------------------------------------------------------
            @param group: True or False
            @param picking: picking object
            @param: move_line: move_line object
            @param: invoice_id: ID of the related invoice
            @param: invoice_vals: dict used to created the invoice
            @param context: Standard Dictionary
            @return: dict that will be used to create the invoice line
        """
        res = super(stock_picking, self)._prepare_invoice_line(cr, uid, group, picking, move_line, invoice_id, invoice_vals, context=context)
        res.update({'prod_lot_id': move_line.prodlot_id.id})
        return res

stock_picking()


class stock_production_lot(orm.Model):
    _inherit = 'stock.production.lot'

    _columns = {
        'cost_price_per_unit': fields.float('Cost Price Per Unit', readonly=True, digits_compute=dp.get_precision('Purchase Price'),
            help='It is the cost per unit of the product in the production lot that will be taken in the account moves generated related to the lot')
    }

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        """
        This Method Changes the Cost Price in the Product Lot related to the product.
        It updates the cost price per Unit with the value of related Product Cost Price.
        -------------------------------------------------------------------------------
        @param self: object pointer
        @param cr: database cursor
        @param uid: current logged in user
        @param ids: Current record(s) Identifier(s)
        @param product_id: Identifier of the Product
        @param context: Standard Dictionary
        @return A dictionary that contains a nested dictionary having field value pair
        """
        if not product_id:
            return {'value': {'product_id': False, 'cost_price_per_unit': False}}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            return {'value': {'product_id': product_id, 'cost_price_per_unit': product.standard_price}}

    def create(self, cr, uid, vals, context=None):
        """
        This method updates the vals directory with the cost price per unit for production lot.
        ---------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param vals: Vals Directory having field, value pairs
        @param context: Standard Dictionary
        @return: Identifier of the newly created record
        """
        if not vals.get('cost_price_per_unit', False) and vals.get('product_id', False):
            _tmp = self.onchange_product_id(cr, uid, [], vals['product_id'], context=context)
            _tmp = _tmp and _tmp['value'] or {}
            vals.update(_tmp)
        return super(stock_production_lot, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """
        This method updates the vals directory with the cost price per unit for production lot.
        ---------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier(s) of the current record(s)
        @param vals: Vals Directory having field, value pairs
        @param context: Standard Dictionary
        @return: True
        """
        if not vals.get('cost_price_per_unit', False) and vals.get('product_id', False):
            _tmp = self.onchange_product_id(cr, uid, ids, vals['product_id'], context=context)
            _tmp = _tmp and _tmp['value'] or {}
            vals.update(_tmp)
        return super(stock_production_lot, self).write(cr, uid, ids, vals, context=context)

    def get_available_lots(self, cr, uid, product_id=False, location_id=False, context=None):
        """
        Returns all the available Production Lots (those with quantity > 0) that belongs to the
        specified location and product
        ---------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param product_id: The Product ID sought
        @param location_id: The Location ID where the Lots reside
        @param order: Sorting order of the Production Lot by way of Production Lot's date
        @param context: Standard Dictionary
        @return: A list of dictionary containing the Production Lot ID ('prodlot_id'),
            Quantity Available in the Product's UOM ('qty'), Date of Production Lot ('date'),
            Product ID ('product_id'), Location ID ('location_id')
        """

        if not product_id or not location_id:
            raise orm.except_orm(_('Error'), _('Product and Location must be specified!'))

        # Get all available Production Lot sorted based on the Product's Cost Method
        _query = """
        SELECT
            prodlot_id,
            SUM(qty) AS qty,
            MAX(date) AS date,
            MAX(product_id) AS product_id,
            MAX(location_id) AS location_id
        FROM (
            SELECT spl.date AS date,
                sm.location_id,
                sm.product_id,
                sm.prodlot_id,
                -sum(sm.product_qty /uo.factor) as qty
            FROM stock_move AS sm
            JOIN stock_production_lot spl
                ON (spl.id=sm.prodlot_id)
            LEFT JOIN stock_location sl
                ON (sl.id = sm.location_id)
            LEFT JOIN product_uom uo
                ON (uo.id=sm.product_uom)
            WHERE STATE = 'done'
            GROUP BY spl.date, sm.location_id, sm.product_id, sm.product_uom, sm.prodlot_id
            UNION ALL
            SELECT spl.date AS date,
                sm.location_dest_id AS location_id,
                sm.product_id,
                sm.prodlot_id,
                sum(sm.product_qty /uo.factor) as qty
            FROM stock_move AS sm
            JOIN stock_production_lot spl
                ON (spl.id=sm.prodlot_id)
            LEFT JOIN stock_location sl
                ON (sl.id = sm.location_dest_id)
            LEFT JOIN product_uom uo
                ON (uo.id=sm.product_uom)
            WHERE STATE = 'done'
            GROUP BY spl.date, sm.location_dest_id, sm.product_id, sm.product_uom, sm.prodlot_id
        ) AS sorted_prod_lot_qty
        WHERE location_id = %s AND product_id = %s
        GROUP BY prodlot_id
        HAVING SUM(qty) > 0
        """

        _product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        _order_by = ' ORDER BY date %s, location_id, product_id, prodlot_id' % ((_product.cost_method == 'lifo') and 'DESC' or '')
        _sql = _query + _order_by
        params = (location_id, product_id)
        cr.execute(_sql, params)
        return cr.dictfetchall()

stock_production_lot()


class stock_move(orm.Model):
    _inherit = 'stock.move'

    _columns = {
        'cost_method': fields.related('product_id', 'cost_method', type='char', size=64, string='Cost Method')
    }

    def calculate_lot_cost_price_per_unit(self, cr, uid, prodlot_id=False, purchase_line_id=False, context=None):
        _price = False
        if purchase_line_id:
            _pol = self.pool.get('purchase.order.line').browse(cr, uid, purchase_line_id, context=context)
            _price = _pol.price_unit

            if prodlot_id:
                # Account for UOM Difference (Purchase Order Line's UOM vs Production Lot's Product UOM)
                # If Purchase Order Line's UOM is not specified, assume that it will use Product UOM
                _lot = self.pool.get('stock.production.lot').browse(cr, uid, prodlot_id, context=context)
                _pol_uom = _pol.product_uom and _pol.product_uom.id or _pol.product_id.uom_id.id or False
                _prod_uom = _lot.product_id and _lot.product_id.uom_id.id or False
                if _pol_uom != _prod_uom:
                    _price = self.pool.get('product.uom')._compute_price(cr, uid, _pol_uom, _price, to_uom_id=_prod_uom)

            # Convert to the Company's Currency
            _co_ccy_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
            _pol_ccy = _pol.order_id.pricelist_id.currency_id.id
            if _co_ccy_id != _pol_ccy:
                _ctx = {'date': _pol.date_order}
                _price = self.pool.get('res.currency').compute(cr, uid, _pol_ccy, _co_ccy_id, _price, context=_ctx)

        return _price

    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,
                            loc_dest_id=False, partner_id=False):
        """
        When you change product based on product's stock move's stock method field is set.
        ----------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifiers of the Current Records
        @prod_id: Product
        @loc_id: Source Location of Stock Move
        @loc_dest_id: Destination Location of Stock Move
        @partner_id: Partner
        @return Dictionary containing value/warning as key and field, value pair or warning message as value.
        """
        res = super(stock_move, self).onchange_product_id(cr, uid, ids, prod_id=prod_id, loc_id=loc_id, loc_dest_id=loc_dest_id, partner_id=partner_id)
        if prod_id:
            product = self.pool.get('product.product').browse(cr, uid, prod_id)
            _val = res.get('value', {})
            _val.update({'cost_method': product.cost_method})
            res['value'] = _val
        return res

    def _create_account_move_line(self, cr, uid, move, src_account_id, dest_account_id, reference_amount, reference_currency_id, context=None):
        """
        This method replaces the cost price of the product based on the product lot if the cost_method is FIFO/LIFO and Lot Based
        ---------------------------------------------------------------------------------------------------------------------------------------
        @param self: object pointer
        @param cr: database cursor
        @param uid: current logged in user
        @param move: The Stock move for which we want to create accounting moves.
        @param src_account_id: The Source Account from which the amount will be debited.
        @param dest_account_id: The Destination Account in which the amount will be credited.
        @param reference_amount: The Reference amount used in the moves
        @param reference_currency_id: The Reference Currency of the amount
        @param context: Standard Dictionary
        @return Action to close the wizard
        """
        result = super(stock_move, self)._create_account_move_line(cr, uid, move, src_account_id, dest_account_id, reference_amount, reference_currency_id, context=context)
        if move.product_id.is_lot_based and move.prodlot_id:
            _cppu = move.prodlot_id.cost_price_per_unit
            _co_ccy_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id

            # Account for UOM Difference (Stock Move's UOM vs Production Lot's Product UOM)
            # If Stock Move's UOM is not specified, assume that it will use Product UOM
            _sm_uom = move.product_uom and move.product_uom.id or move.product_id.uom_id.id or False
            _prod_uom = move.prodlot_id.product_id and move.prodlot_id.product_id.uom_id.id or False
            if _sm_uom != _prod_uom:
                # Express if Stock Move's UOM terms
                _cppu = self.pool.get('product.uom')._compute_price(cr, uid, _prod_uom, _cppu, to_uom_id=_sm_uom)

            new_amount = _cppu * move.product_qty
            for acc_move in result:
                if 'debit' in acc_move[2]:
                    acc_move[2].update({'debit': new_amount})

                if 'credit' in acc_move[2]:
                    acc_move[2].update({'credit': new_amount})

                # Propagate the production lot information
                acc_move[2].update({'prod_lot_id': move.prodlot_id and move.prodlot_id.id})

                # Also update Amount Currency if necessary
                _am_ccy = acc_move[2].get('currency_id', False)
                if _am_ccy and (_am_ccy != _co_ccy_id):
                    _am_date = acc_move[2].get('date', time.strftime('%Y-%m-%d'))
                    _ctx = {'date': _am_date}
                    new_amount = self.pool.get('res.currency').compute(cr, uid, _co_ccy_id, _am_ccy, new_amount, context=_ctx)
                    acc_move[2].update({'amount_currency': new_amount})

        return result

    def _create_product_valuation_moves(self, cr, uid, move, context=None):
        """
        Generate the appropriate accounting moves if the product being moves is subject
        to real_time valuation tracking, and the source or destination location is
        a transit location or is outside of the company.
        """
        # Location type is not internal
        if move.product_id.valuation == 'real_time' and move.location_dest_id.company_id \
           and (move.location_id.usage != 'internal' and move.location_dest_id.usage != 'internal'):
            if context is None:
                context = {}
            src_company_ctx = dict(context, force_company=move.location_id.company_id.id)
            dest_company_ctx = dict(context, force_company=move.location_dest_id.company_id.id)

            account_moves = []
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, dest_company_ctx)
            reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid, move, src_company_ctx)
            account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_src, acc_dest, reference_amount, reference_currency_id, context))]

            move_obj = self.pool.get('account.move')

            _account_move_to_link = []
            for j_id, move_lines in account_moves:
                _account_move_to_link.append(
                    move_obj.create(
                        cr, uid, {
                            'journal_id': j_id,
                            'line_id': move_lines,
                            'ref': move.picking_id and move.picking_id.name
                        }, context=context))
            self.write(cr, uid, move.id, {'account_move_id': [(6, 0, _account_move_to_link)]}, context=context)
        else:
            super(stock_move, self)._create_product_valuation_moves(cr, uid, move, context=context)

    def create(self, cr, uid, vals, context=None):
        """
        This method updates the update the related Production Lot (if any) Cost Price Per Unit
        to the the Purchase Price (if any)
        ---------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param vals: Vals Directory having field, value pairs
        @param context: Standard Dictionary
        @return: Identifier of the newly created record
        """
        rv = super(stock_move, self).create(cr, uid, vals, context=context)

        prodlot_id = vals.get('prodlot_id', False)
        purchase_line_id = vals.get('purchase_line_id', False)
        if prodlot_id and purchase_line_id:
            _price = self.calculate_lot_cost_price_per_unit(cr, uid, prodlot_id=prodlot_id, purchase_line_id=purchase_line_id, context=context)
            self.pool.get('stock.production.lot').write(cr, uid, [prodlot_id], {'cost_price_per_unit': _price}, context=context)

        return rv

    def write(self, cr, uid, ids, vals, context=None):
        """
        This method updates the update the related Production Lot (if any) Cost Price Per Unit
        to the the Purchase Price (if any)
        ---------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier(s) of the current record(s)
        @param vals: Vals Directory having field, value pairs
        @param context: Standard Dictionary
        @return: True
        """
        if isinstance(ids, (list, tuple, dict, )):
            select = list(ids)
        else:
            select = [ids]

        rv = super(stock_move, self).write(cr, uid, select, vals, context=context)

        for _obj in self.browse(cr, uid, select, context=context):
            if _obj.prodlot_id and _obj.purchase_line_id:
                _price = self.calculate_lot_cost_price_per_unit(cr, uid, prodlot_id=_obj.prodlot_id.id, purchase_line_id=_obj.purchase_line_id.id, context=context)
                _obj.prodlot_id.write({'cost_price_per_unit': _price}, context=context)

        return rv

stock_move()
