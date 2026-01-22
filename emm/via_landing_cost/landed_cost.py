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

from tools.translate import _
from tools.float_utils import float_round, float_compare
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from osv import orm, fields
from datetime import datetime as DT
import openerp.addons.decimal_precision as dp

import logging


# Method to calculation the cost per line based on the given inputs
def _calculate_line_cost(self, cr, uid, qty_in_from_uom, price_per_to_uom, from_uom_obj, to_uom_obj, context=None):
    _uom_pool = self.pool.get('product.uom')
    _qty_in_to_uom = _uom_pool._compute_qty_obj(cr, uid, from_uom_obj, qty_in_from_uom, to_uom_obj, context=context)
    return _qty_in_to_uom * (price_per_to_uom or 0.0)


class account_invoice(orm.Model):
    _inherit = "account.invoice"
    _logger = logging.getLogger(__name__)

    def check_incoming_shipment(self, cr, uid, ids, name, args, context=None):
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            # Return False if any stock.picking related to the account.invoice is not in 'done' state
            res[_obj.id] = len([picking.id for picking in _obj.picking_ids if picking.state not in ('done')]) == 0
        return res

    def check_reclass_period(self, cr, uid, ids, name, args, context=None):
        _period_obj = self.pool.get('account.period')
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = False
            if _obj.period_id:
                period_id_check = _period_obj.find(cr, uid, _obj.check_reclass_date, context=context)
                res[_obj.id] = (_obj.period_id.id not in period_id_check)
        return res

    def _default_valuation_journal(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        journal_codename = 'landing_cost_journal'  # Default Domain configuration code to be used
        journal_id = user.company_id.get_journal_for(journal_codename, context=context)
        return journal_id

    _columns = {
        "picking_ids": fields.many2many('stock.picking', string='Pickings for Landing Cost Proration', domain=[('state', 'not in', ['cancel'])]),
        "move_prorates": fields.one2many('products.on.stock.picking', 'invoice_id', 'Landing Cost Proration',),
        "move_landed_cost": fields.many2one('account.move', 'Landed Cost Journal', readonly=True),
        "check_reclass_date": fields.date('Re-class Date'),
        "valuation_journal_id": fields.many2one('account.journal', 'Valuation Journal'),
        "warning_reclass": fields.function(check_reclass_period, method=True, type='boolean',
            string='Warning', readonly=True),
        "picking_state": fields.function(check_incoming_shipment, method=True, type='boolean',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['picking_ids'], 20),
            }, string='Picking State', readonly=True),
    }

    _defaults = {
        "valuation_journal_id": _default_valuation_journal,
    }

    def _check_total_prorates(self, cr, uid, ids, context=None):
        """
        Validates that the total of prorate must be equal to 100.
        ---------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param ids: Identifier(s) of Current record(s)
        @param context: Standard Dictionary
        @return: True or False
        """
        for _obj in self.browse(cr, uid, ids, context=context):
            _prorates = sum([_line.prorate for _line in _obj.move_prorates])
            if not _obj.move_prorates:
                return True
            if float_compare(_prorates, 100.0, precision_rounding=0.005):
                return False
        return True

    _constraints = [
        (_check_total_prorates, 'The total of Prorate % of all Landing Cost Prorates must be equal to 100.0', ['Landing Cost Prorates']),
    ]

    def action_move_create(self, cr, uid, ids, context=None):
        super(account_invoice, self).action_move_create(cr, uid, ids, context=context)
        for inv in self.browse(cr, uid, ids, context=context):
            if not inv.check_reclass_date:
                inv.write({'check_reclass_date': inv.date_invoice}, context=context)
        return True

    def onchange_move_lines(self, cr, uid, ids, picking_ids, move_prorates, context=None):
        # It is assumed that only one record will be processed at any point of time
        assert (len(ids) <= 1), _("Only one row can be processed at any point of time")

        _sm_pool = self.pool.get('stock.move')
        _list_pool = self.pool.get('products.on.stock.picking')
        _invoice = ids and self.browse(cr, uid, ids[0], context=context) or False

        # Precision of the Prorate value
        _precision = _list_pool._columns.get('prorate', False)
        _precision = _precision and _precision.digits[1] or 2

        # List of new stock moves
        _new_list_id = _sm_pool.search(cr, uid, [('picking_id', 'in', picking_ids[0][2])], context=context)
        _new_list = _sm_pool.browse(cr, uid, _new_list_id)

        # List of "old" stock moves
        _old_list = {}
        for _line in (_invoice and _invoice.move_prorates or []):
            _old_list.update({_line.move_id.id: _line.id})

        # Construct the new lines
        _total_cost_price = 0
        _moves = []
        _move_ids = []
        for line in _new_list:
            # Calculate _line_cost and accumulate it as _total_cost_price to be used for proration
            prodlot = line.prodlot_id

            if line.picking_id.type == 'out':
                sale_line = line.sale_line_id
                if sale_line:
                    _price_per_to_uom = sale_line.price_unit
                else:
                    if prodlot:
                        _price_per_to_uom = prodlot.product_id and prodlot.product_id.list_price or 0.0
                    else:
                        _price_per_to_uom = line.product_id and line.product_id.product_tmpl_id and line.product_id.product_tmpl_id.list_price or 0.0
            else:
                if prodlot:
                    _price_per_to_uom = prodlot.cost_price_per_unit or 0.0
                else:
                    _price_per_to_uom = line.product_id and line.product_id.product_tmpl_id and line.product_id.product_tmpl_id.standard_price or 0.0

            _line_cost = _calculate_line_cost(self, cr, uid, line.product_qty, _price_per_to_uom, line.product_uom, line.product_id.uom_id, context=context)
            _total_cost_price += _line_cost

            if ids:
                # If the account.invoice has been saved before
                if line.id in _old_list.keys():
                    # Stock.move in old list, do nothing just append to the new list
                    _moves.append([4, _old_list.get(line.id, False), False])
                    _move_ids.append(_old_list.get(line.id, False))

                    # Pop the line from _old_list, so that _old_list will
                    # contain only lines that are not in the _new_list
                    _old_list.pop(line.id, None)
                else:
                    # Stock.move is not in the old list, create the products.on.stock.picking and append it to the list
                    _new_id = _list_pool.create(cr, uid, {'invoice_id': ids[0], 'move_id': line.id}, context=context)
                    _moves.append([4, _new_id, False])
                    _move_ids.append(_new_id)
            else:
                # If the account.invoice has not been saved before
                _to_append = {
                    'move_id': line.id,
                    'picking_id': line.picking_id.id,
                    'product_uom': line.product_uom.id,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'serial_number': line.prodlot_id.id,
                    'price_unit': _price_per_to_uom,
                    'line_cost': _line_cost,
                }
                _moves.append(_to_append)

        # Remove the lines in the _old_list (the remaining that are not in the _new_list)
        for _id in _old_list.values():
            _list_pool.unlink(cr, uid, _id, context=context)

        # Calculate and update the value of Prorate
        _total = 100.0
        _total_amt_processed = _total_cost_price
        if ids:
            for line in _list_pool.browse(cr, uid, _move_ids, context=context):
                _prorate = _total_amt_processed and (_total * line.line_cost / _total_amt_processed) or 0.0
                _prorate = float_round(_prorate, precision_digits=_precision)
                _total -= _prorate
                _total_amt_processed -= line.line_cost
                line.write({'prorate': _prorate})
        else:
            for line in _moves:
                _prorate = _total_amt_processed and (_total * line.get('line_cost', 0.0) / _total_amt_processed) or 0.0
                _prorate = float_round(_prorate, precision_digits=_precision)
                _total -= _prorate
                _total_amt_processed -= line.get('line_cost', 0.0)
                line.update({'prorate': _prorate})

        return {'value': {'move_prorates': _moves}}

    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(account_invoice, self).copy_data(cr, uid, id, context=context)
        res.pop("move_landed_cost", False)
        return res

    def reclass_journal(self, cr, uid, ids, context=None):
        _invoice_obj_list = self.browse(cr, uid, ids, context=context)
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        _data = []

        for _invoice in _invoice_obj_list:
            if _invoice.move_landed_cost:
                raise orm.except_orm(
                    _('Error'),
                    _("Invoice %s's landing cost has been re-classed!" % (_invoice.number))
                )
            # Every account.invoice object, create account.move inside account.invoice
            journal_id = _invoice.valuation_journal_id and _invoice.valuation_journal_id.id or False
            if not journal_id:
                raise orm.except_orm(
                    _('Error'),
                    _('Valuation Journal has not been defined!')
                )
            date = _invoice.date_invoice or DT.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            move = {
                'name': _invoice.move_id.name,
                'ref': _invoice.move_id.ref,
                'journal_id': journal_id,
                'date': date,
                'narration': _invoice.comment,
                'company_id': _invoice.company_id.id,
                'state': _invoice.move_id.state
            }
            new_move_id = move_obj.create(cr, uid, move, context=context)

            # Tax account list
            tax_accounts = []
            for tax in _invoice.tax_line:
                tax_accounts.append(tax.account_id)

            # Copy data that will be used for prorates
            for _line in _invoice.move_id.line_id:
                if _line.account_id != _line.partner_id.property_account_payable and _line.partner_id.property_account_receivable:
                    if _line.account_id not in tax_accounts:
                        to_append = move_line_obj.copy_data(cr, uid, _line.id, context=context)
                        _data.append(to_append)

            # Switch debit and credit, then create account.move.line which is linked to new account.move
            for data in _data:
                new_credit = data['debit']
                new_debit = data['credit']
                data.update({'debit': new_debit, 'credit': new_credit, 'move_id': new_move_id})
                amount_currency_origin = data.get('amount_currency', False)
                if amount_currency_origin:
                    amount_currency = -1 * amount_currency_origin
                    data.update({'amount_currency': amount_currency})
                move_line_id = move_line_obj.create(cr, uid, data, context=context)
                _vals_to_write = data.copy()
                amount_currency = _vals_to_write.get('amount_currency', False)

                sum_debit = 0.0
                sum_credit = 0.0
                counter = 1
                len_lines = len(_invoice.move_prorates)
                for _prorate in _invoice.move_prorates:
                    new_debit = _prorate.prorate * data['credit'] / 100.0
                    new_credit = _prorate.prorate * data['debit'] / 100.0

                    sum_debit = sum_debit + round(new_debit, 2)
                    sum_credit = sum_credit + round(new_credit, 2)

                    lot_number = _prorate.serial_number.id
                    product = _prorate.product_id.id
                    if amount_currency_origin:
                        amount_currency = new_debit - new_credit
                    else:
                        amount_currency = amount_currency_origin

                    if counter == len_lines:
                        if sum_credit != data['debit']:
                            new_credit = new_credit + data['debit'] - sum_credit
                        if sum_debit != data['credit']:
                            new_debit = new_debit + data['credit'] - sum_debit
                    counter += 1

                    _vals_to_write.update({
                        'debit': new_debit,
                        'credit': new_credit,
                        'move_id': new_move_id,
                        'prod_lot_id': lot_number,
                        'product_id': product,
                        'amount_currency': amount_currency,
                    })
                    move_line_id = move_line_obj.create(cr, uid, _vals_to_write, context=context)

            # Link the new account.move to account.invoice
            self.write(cr, uid, _invoice.id, {'move_landed_cost': new_move_id}, context=context)


class products_on_stock_picking(orm.Model):
    _name = "products.on.stock.picking"
    _logger = logging.getLogger(__name__)

    # Calculation of cost per line
    def _line_cost(self, cr, uid, ids, name, args, context=None):
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = {
                "price_unit": 0.0,
                "line_cost": 0.0
            }

            prodlot = _obj.move_id and _obj.move_id.prodlot_id

            if _obj.move_id and _obj.move_id.picking_id and _obj.move_id.picking_id.type == 'out':
                sale_line = _obj.move_id.sale_line_id
                if sale_line:
                    _price_per_to_uom = sale_line.price_unit
                else:
                    if prodlot:
                        _price_per_to_uom = prodlot.product_id and prodlot.product_id.list_price or 0.0
                    else:
                        _price_per_to_uom = _obj.move_id.product_id and _obj.move_id.product_id.product_tmpl_id and _obj.move_id.product_id.product_tmpl_id.list_price or 0.0
            else:
                if prodlot:
                    _price_per_to_uom = prodlot.cost_price_per_unit or 0.0
                else:
                    _price_per_to_uom = _obj.move_id.product_id and _obj.move_id.product_id.product_tmpl_id and _obj.move_id.product_id.product_tmpl_id.standard_price or 0.0
            rv = _calculate_line_cost(self, cr, uid, _obj.move_id.product_qty, _price_per_to_uom, _obj.move_id.product_uom, _obj.move_id.product_id.uom_id, context=context)
            res[_obj.id]['price_unit'] = _price_per_to_uom
            res[_obj.id]['line_cost'] = rv
        return res

    _columns = {
        "invoice_id": fields.many2one('account.invoice', 'Account Invoice'),
        "move_id": fields.many2one('stock.move', 'Stock Move'),
        "picking_id": fields.related('move_id', 'picking_id', type='many2one', relation='stock.picking', string='Picking', readonly=True),
        "product_id": fields.related('move_id', 'product_id', type='many2one', relation='product.product', string='Product', readonly=True),
        "product_uom": fields.related('move_id', 'product_uom', type='many2one', relation='product.uom', string='UoM', readonly=True),
        "product_qty": fields.related('move_id', 'product_qty', type='float', string='Quantity', readonly=True),
        "serial_number": fields.related('move_id', 'prodlot_id', type='many2one', relation='stock.production.lot', string="Serial Number", readonly=True),
        "price_unit": fields.function(_line_cost, method=True, type='float', digits_compute=dp.get_precision('Product Price'), string='Price Unit',
            store={
                'products.on.stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_id'], 20),
            }, readonly=True, multi='line_cost_function'),
        "line_cost": fields.function(_line_cost, method=True, type='float', digits_compute=dp.get_precision('Product Price'), string='Cost of this Line',
            store={
                'products.on.stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_id'], 20),
            }, readonly=True, multi='line_cost_function'),
        "prorate": fields.float('Prorate %', digits_compute=dp.get_precision('Product Price')),
    }
