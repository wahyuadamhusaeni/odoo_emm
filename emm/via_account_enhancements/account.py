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

from osv import osv, fields
from tools.translate import _
import decimal_precision as dp


class account_move_line(osv.osv):
    _inherit = 'account.move.line'

    def _get_signed_amount_residual(self, cr, uid, ids, field_names, args, context=None):
        """
        An adapted copy if the _amount_residual method in account/account_move_line.py allowing
        calculation of residual amount in company currency to any account type based on
        reconciliation
        """
        res = {}
        if context is None:
            context = {}

        for move_line in self.browse(cr, uid, ids, context=context):
            if move_line.reconcile_id:
                continue
            line_total_in_company_currency = move_line.debit - move_line.credit
            if move_line.reconcile_partial_id:
                for payment_line in move_line.reconcile_partial_id.line_partial_ids:
                    if payment_line.id == move_line.id:
                        continue
                    line_total_in_company_currency += (payment_line.debit - payment_line.credit)

            res[move_line.id] = line_total_in_company_currency
        return res

    _columns = {
        'signed_amount_residual': fields.function(_get_signed_amount_residual, method=True, string='Available Amount', type='float', readonly=True),
    }

account_move_line()


class account_move(osv.osv):
    _inherit = 'account.move'

    def post(self, cr, uid, ids, context=None):
        super(account_move, self).post(cr, uid, ids, context=context)
        valid_moves = self.validate(cr, uid, ids, context)
        self.write(cr, uid, valid_moves, {'state': 'posted'})

        return True

account_move()


class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def _amount_base(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_tax': 0.0,
                'amount_base': 0.0,
                'amount_base_disc': 0.0,
                'amount_base_disc_tax': 0.0,
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_base'] += line.amount_base
                res[invoice.id]['amount_base_disc'] += line.amount_base_disc
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
            res[invoice.id]['amount_base_disc_tax'] = res[invoice.id]['amount_base_disc'] + res[invoice.id]['amount_tax']
            del res[invoice.id]['amount_tax']

        return res

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    _columns = {
        'amount_base': fields.function(_amount_base, digits_compute=dp.get_precision('Account'), string='Base Amount',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='base'),
        'amount_base_disc': fields.function(_amount_base, digits_compute=dp.get_precision('Account'), string='Discounted Amount',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='base'),
        'amount_base_disc_tax': fields.function(_amount_base, digits_compute=dp.get_precision('Account'), string='Discounted Amount with Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='base'),
    }

account_invoice()


class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'

    def _amount_base(self, cr, uid, ids, name, args, context=None):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')

        for line in self.browse(cr, uid, ids):
            res[line.id] = {
                'amount_base': 0.0,
                'amount_base_disc': 0.0,
                'amount_base_disc_tax': 0.0,
                'price_unit_base': 0.0,
                'price_unit_base_disc': 0.0,
                'price_unit_base_disc_tax': 0.0,
            }

            # Get the Base Price Unit with and without Tax
            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_unit, 1.0, product=line.product_id, partner=line.invoice_id.partner_id)
            _disc = (1 - (line.discount or 0.0)/100.0)
            _base_price_unit = taxes.get('total', 0.00)
            _disc_price_unit = _base_price_unit * _disc
            _taxed_price_unit = taxes.get('total_included', 0.00)
            _taxed_disc_price_unit = _taxed_price_unit * _disc
            _qty = line.quantity
            _cur = line.invoice_id and line.invoice_id.currency_id or False

            # Unit Price is not to be recalculated
            res[line.id]['price_unit_base'] = _base_price_unit
            res[line.id]['price_unit_base_disc'] = _disc_price_unit
            res[line.id]['price_unit_base_disc_tax'] = _taxed_disc_price_unit
            if _cur:
                res[line.id]['amount_base'] = cur_obj.round(cr, uid, _cur, _base_price_unit * _qty)
                res[line.id]['amount_base_disc'] = cur_obj.round(cr, uid, _cur, _disc_price_unit * _qty)
                res[line.id]['amount_base_disc_tax'] = cur_obj.round(cr, uid, _cur, _taxed_disc_price_unit * _qty)
            else:
                res[line.id]['amount_base'] = _base_price_unit * _qty
                res[line.id]['amount_base_disc'] = _disc_price_unit * _qty
                res[line.id]['amount_base_disc_tax'] = _taxed_disc_price_unit * _qty

        return res

    _columns = {
        'amount_base': fields.function(_amount_base, digits_compute=dp.get_precision('Account'), type="float", string='Base Subtotal', store=True, multi='base'),
        'amount_base_disc': fields.function(_amount_base, digits_compute=dp.get_precision('Account'), type="float", string='Discounted Subtotal', store=True, multi='base'),
        'amount_base_disc_tax': fields.function(_amount_base, digits_compute=dp.get_precision('Account'), type="float", string='Discounted Subtotal with Tax', store=True, multi='base'),
        'price_unit_base': fields.function(_amount_base, digits_compute=dp.get_precision('Product Price'), type="float", string='Base Unit Price', store=True, multi='base'),
        'price_unit_base_disc': fields.function(_amount_base, digits_compute=dp.get_precision('Product Price'), type="float", string='Discounted Unit Price', store=True, multi='base'),
        'price_unit_base_disc_tax': fields.function(_amount_base, digits_compute=dp.get_precision('Product Price'), type="float", string='Discounted Unit Price with Tax', store=True, multi='base'),
    }

account_invoice_line()
