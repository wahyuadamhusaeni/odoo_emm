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

import time
from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
from via_base_enhancements.tools import resolve_o2m_operations, prep_dict_for_write


class via_assign_transaction_line(osv.osv_memory):
    _name = "via.assign.transaction.line"
    _description = "Transaction Lines To Assign"

    def _get_amount_residual(self, cr, uid, ids, field_names, args, context=None):
        res = {}
        if context is None:
            context = {}
        for _line in self.browse(cr, uid, ids, context=context):
            res[_line.id] = -1 * _line.move_line_id.signed_amount_residual
        return res

    _columns = {
        'wizard_id': fields.many2one('via.assign.payment', 'Downpyament Wizard', readonly=True),
        'move_line_id': fields.many2one('account.move.line', 'Journal Item To Assign', domain="[('reconcile_id', '=', False)]", required=True),
        'name': fields.related('move_line_id', 'name', string="Name", type='char', size=64, readonly=True),
        'account_id': fields.related('move_line_id', 'account_id', string="Account", type='many2one', relation='account.account', readonly=True),
        'date': fields.related('move_line_id', 'date', type='date', string="Bank Due", readonly=True),
        'debit': fields.related('move_line_id', 'debit', string="Debit", type='float', readonly=True),
        'credit': fields.related('move_line_id', 'credit', string="Credit", type='float', readonly=True),
        'company_id': fields.related('move_line_id', 'company_id', string="Company", type='many2one', relation='res.company', readonly=True),
        'currency_id': fields.related('move_line_id', 'currency_id', string="Currency", type='many2one', relation='res.currency', readonly=True),
#        'amount_residual': fields.related('move_line_id', 'signed_amount_residual', string="Available Amount", type='float', readonly=True),
        'amount_residual': fields.function(_get_amount_residual, method=True, string='Available Amount', type='float', readonly=True),
        'amount_to_use': fields.float('Amount To Use', digits_compute=dp.get_precision('Sale Price')),
        'reconcile_partial_id': fields.related('move_line_id', 'reconcile_partial_id', string="Partial Assignment", type='many2one', relation='account.move.reconcile', readonly=True),
    }

    def create(self, cr, uid, vals, context={}):
        if context is None:
            context = {}

        if vals.get('wizard_id', False):
            # Parent wizard cannot had already have other via_assign_transaction_line
            _wiz = self.pool.get('via.assign.payment').browse(cr, uid, vals['wizard_id'], context=context)
            if (len(_wiz.transaction_lines) > 0):
                raise osv.except_osv(_("Error!"), _("Cannot assign more than one available transaction at any time!!!"))

        return super(via_assign_transaction_line, self).create(cr, uid, vals, context=context)

    def onchange_move_line_id(self, cr, uid, ids, move_line_id, context=None):
        if context is None:
            context = {}

        if ids and ids[0]:
            _trx_line = self.pool.get('via.assign.transaction.line').read(cr, uid, ids[0], context=context)
            if (_trx_line['move_line_id'] == move_line_id):
                return {}

        rv = {'value': {'amount_to_use': 0.0}}
        if move_line_id:
            _aml = self.pool.get('account.move.line').browse(cr, uid, move_line_id, context=context)
            if _aml:
                _aml_data = _aml.read()[0]
                _aml_data = prep_dict_for_write(cr, uid, _aml_data, context=context)

                _aml_data['amount_residual'] = -1 * _aml.signed_amount_residual
                _aml_data['amount_to_use'] = -1 * _aml.signed_amount_residual
                rv['value'].update(_aml_data)

        return rv


class via_assign_payment_line(osv.osv_memory):
    _name = "via.assign.payment.line"
    _description = "Payment Assignment Lines"

    _columns = {
        'wizard_id': fields.many2one('via.assign.payment', 'Payment Assign Wizard', readonly=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', required=True),
        'name': fields.related('invoice_id', 'name', type='char', string="Description", readonly=True),
        'date_invoice': fields.related('invoice_id', 'date_invoice', type='date', string="Invoice Date", readonly=True),
        'date_due': fields.related('invoice_id', 'date_due', type='date', string="Date Due", readonly=True),
        'state': fields.related('invoice_id', 'state', type='selection',
            selection=[('draft', 'Draft'), ('proforma', 'Pro-forma'), ('proforma2', 'Pro-forma'), ('open', 'Open'), ('paid', 'Paid'), ('cancel', 'Cancelled')],
            string="State", readonly=True),
        'account_id': fields.related('invoice_id', 'account_id', string="Account", type='many2one', relation='account.account', readonly=True),
        'company_id': fields.related('invoice_id', 'company_id', string="Company", type='many2one', relation='res.company', readonly=True),
        'currency_id': fields.related('invoice_id', 'currency_id', string="Currency", type='many2one', relation='res.currency', readonly=True),
        'amount_total': fields.related('invoice_id', 'amount_total', string="Total", type='float', readonly=True),
        'residual': fields.related('invoice_id', 'residual', string="Amount Owed", type='float', readonly=True),
        'amount_to_pay': fields.float('Amount To Pay', digits_compute=dp.get_precision('Sale Price')),
    }

    def create(self, cr, uid, vals, context={}):
        if ('__last_update' in context):
            raise osv.except_osv(_("Don't Create!"), _("Payment details can only be created through creation of new invoice!!!"))
        else:
            return super(via_assign_payment_line, self).create(cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, context={}):
        if (ids and ('__last_update' in context)):
            raise osv.except_osv(_("Don't Delete!"), _("If a certain invoice is not to be paid, just set the Amount to Pay to 0.0"))
        else:
            return super(via_assign_payment_line, self).unlink(cr, uid, ids, context=context)


class via_assign_payment(osv.osv_memory):
    _name = "via.assign.payment"
    _description = "Sales Payment Assignment"

    def _get_company_id(self, cr, uid, context=None):
        if context is None:
            context = {}

        _invoice_id = context.get('invoice_id', False)
        _order_id = context.get('order_id', False)
        if _invoice_id:
            _obj = self.pool.get('account.invoice').browse(cr, uid, _invoice_id, context=context)
        elif _order_id:
            _obj = self.pool.get('sale.order').browse(cr, uid, _order_id, context=context)
        else:
            _obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)

        return _obj and _obj.company_id.id or False

    def _get_partner_id(self, cr, uid, context=None):
        if context is None:
            context = {}

        _obj = False
        _invoice_id = context.get('invoice_id', False)
        _order_id = context.get('order_id', False)
        if _invoice_id:
            _obj = self.pool.get('account.invoice').browse(cr, uid, _invoice_id, context=context)
        elif _order_id:
            _obj = self.pool.get('sale.order').browse(cr, uid, _order_id, context=context)

        return _obj and _obj.partner_id.id or False

    def _get_writeoff_amount(self, cr, uid, ids, name, args, context=None):
        if not ids:
            return {}
        # It is assumed that only 1 wizard exist at any point of time for each session
        _wiz = self.pool.get('via.assign.payment').browse(cr, uid, ids[0], context=context)

        res = {}
        debit = credit = 0.0
        if _wiz.transaction_lines:
            for l in _wiz.transaction_lines:
                debit += l.amount_to_use
            for l in _wiz.payment_lines:
                credit += l.amount_to_pay
            res[_wiz.id] = debit - credit
        else:
            res[_wiz.id] = 0
        return res

    _rec_name = 'date'
    _columns = {
        # Payment Line related informations
        'transaction_lines': fields.one2many('via.assign.transaction.line', 'wizard_id', 'Available Payment'),
        'payment_lines': fields.one2many('via.assign.payment.line', 'wizard_id', 'Invoice Details'),

        # Payment related informations
        'date': fields.date('Transaction Date', help="Effective date for payment accounting entries", required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True),
        'order_id': fields.many2one('sale.order', 'Sale Order', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Customer', required=True, readonly=True),
        'payment_holding_account': fields.related('company_id', 'payment_holding_account', string="Payment Holding Account", type='many2one', relation='account.account', readonly=True),
        'payment_assign_journal': fields.many2one('account.journal', 'Payment Assignment Journal', help="Journal used to record payment assignment transaction."),
        'with_writeoff': fields.char('With Write-Off', size=20),
        'writeoff_amount': fields.function(_get_writeoff_amount, method=True, string='Write-Off Amount', type='float'),
        'writeoff_acc_id': fields.many2one('account.account', 'Write-Off Account'),
        'comment': fields.char('Write-Off Comment', size=64),

        # Warning
        'warning': fields.text('Warning'),

        # Allowance to create new invoice (currently not used)
        'new_invoice': fields.boolean('Create invoice?'),

        # Prevention of double processing
        'processed': fields.boolean('Procesed'),
    }

    _defaults = {
        'date': fields.date.context_today,
        'with_writeoff': lambda *a: 'no_writeoff',
        'writeoff_amount': lambda *a: 0.0,
        'company_id': _get_company_id,
        'order_id': lambda s, c, u, ctx: ctx.get('order_id', False),
        'partner_id': _get_partner_id,
        'processed': lambda *a: False,
        'new_invoice': lambda *a: False,
    }

    def _get_warning(self, cr, uid, ids, amount, context=None):
        rv = ''
        if amount:
            if not context:
                context = {}
            pool_lang = self.pool.get('res.lang')
            lang = context.get('lang', 'en_US') or 'en_US'
            lang_ids = pool_lang.search(cr, uid, [('code', '=', lang)])[0]
            lang_obj = pool_lang.browse(cr, uid, lang_ids)
            _formatted = lang_obj.format('%.2f', amount, grouping=True)
            rv = _('The difference %s between Paid Amount amount and sum of Amount to Pay will be put into write-off amount.') % (_formatted)
        return rv

    def onchange_payment_lines(self, cr, uid, ids, transaction_lines, payment_lines, context=None):
        amount = 0.0
        if transaction_lines:
            _line_pool = self.pool.get('via.assign.transaction.line')
            transaction_lines = resolve_o2m_operations(cr, uid, _line_pool, transaction_lines, ['amount_to_use'], context=context) or []
        if payment_lines:
            _line_pool = self.pool.get('via.assign.payment.line')
            payment_lines = resolve_o2m_operations(cr, uid, _line_pool, payment_lines, context=context) or []

        if transaction_lines:
            amount = transaction_lines[0]['amount_to_use']

            for _line in payment_lines:
                amount -= _line['amount_to_pay']
                _line = prep_dict_for_write(cr, uid, _line, context=context)

            return {'value': {
                'writeoff_amount': amount,
                'with_writeoff': amount and 'with_writeoff' or 'no_writeoff',
            }}
        else:
            return {'value': {
                'writeoff_amount': 0.0,
                'with_writeoff': 'no_writeoff',
            }}
        return {}

    def onchange_trx_lines(self, cr, uid, ids, transaction_lines, payment_lines, context=None):
        amount = 0.0
        if transaction_lines:
            _line_pool = self.pool.get('via.assign.transaction.line')
            transaction_lines = resolve_o2m_operations(cr, uid, _line_pool, transaction_lines, ['amount_to_use'], context=context) or []
        if payment_lines:
            _line_pool = self.pool.get('via.assign.payment.line')
            payment_lines = resolve_o2m_operations(cr, uid, _line_pool, payment_lines, context=context) or []

        if transaction_lines:
            amount = transaction_lines[0]['amount_to_use']

            for _line in payment_lines:
                _amount_to_pay = min(_line['amount_to_pay'] or _line['residual'], amount)
                _line['amount_to_pay'] = _amount_to_pay
                amount -= _amount_to_pay
                _line = prep_dict_for_write(cr, uid, _line, context=context)

            return {'value': {
                'payment_lines': payment_lines,
                'writeoff_amount': amount,
                'with_writeoff': amount and 'with_writeoff' or 'no_writeoff',
            }}
        else:
            for _line in payment_lines:
                _line['amount_to_pay'] = 0.0
                _line = prep_dict_for_write(cr, uid, _line, context=context)

            return {'value': {
                'payment_lines': payment_lines,
                'writeoff_amount': 0.0,
                'with_writeoff': 'no_writeoff',
            }}
        return {}

    def open_page(self, cr, uid, ids, context=None):
        _cust_id = context.get('partner_id', False)
        _order_id = context.get('order_id', False)
        _invoice_id = context.get('invoice_id', False)
        _inv_pool = self.pool.get('account.invoice')

        _invoice_to_pay = []
        if _cust_id:
            # Customer is specificed, look for the 'open' invoices that belongs to the partner
            _invoices_to_add = _inv_pool.search(cr, uid, [('partner_id', '=', _cust_id), ('state', '=', 'open')], context=context)
            _invoice_to_pay += _invoices_to_add

        if _order_id:
            # Sale order is specificed, look for the 'open' invoices that belongs to the sale order
            _pool = self.pool.get('sale.order')
            _invoices_obj_to_add = []
            _sale_order = _pool.browse(cr, uid, _order_id, context=context)
            _invoices_obj_to_add = filter(lambda x: 'open' == x.state, _sale_order.invoice_ids)
            _invoice_to_pay += [x.id for x in _invoices_obj_to_add]

        if _invoice_id:
            # Invoice is specificed, use the provided invoice if it is still 'open'
            _invoice = _inv_pool.browse(cr, uid, _invoice_id, context=context)
            if (_invoice.state == 'open'):
                _invoice_to_pay += [_invoice_id]

        # Create the down payment lines from the list of invoices to pay
        # It is assumed that only one wizard will be in the ids list
        _wiz_id = ids[0]
        if _invoice_to_pay:
            _dp_line_pool = self.pool.get('via.assign.payment.line')
            _pool = self.pool.get('account.invoice')
            _dp_lines = []
            ctx = context.copy()
            ctx['auto'] = True
            _inv_obj_to_pay = _pool.browse(cr, uid, _invoice_to_pay, context=context)
            for _inv in _inv_obj_to_pay:
                _vals = {
                    'wizard_id': _wiz_id,
                    'invoice_id': _inv.id,
                    'amount_to_pay': 0.0,
                }
                _dp_line_id = _dp_line_pool.create(cr, uid, _vals, context=ctx)
                _dp_lines.append(_dp_line_id)
            self.pool.get('via.assign.payment').write(cr, uid, [_wiz_id], {'payment_lines': [(6, 0, _dp_lines)]}, context=context)

        # Open the window
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'view_sale_assign_payment')], context=context)
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']

        return {
            'name': _("Assign Payment"),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'via.assign.payment',
            'views': [(resource_id, 'form')],
            'res_id': _wiz_id,
            'type': 'ir.actions.act_window',
            'nodestroy': False,
            'target': 'new',
            'domain': '[]',
            'context': context
        }

    def assign_payment(self, cr, uid, ids, context=None):
        """
         To create invoice and reconcile with corresponding payment
        """
        # It is assumed that only 1 wizard exist at any point of time for each session
        _wiz = self.pool.get('via.assign.payment').browse(cr, uid, ids[0], context=context)

        if not _wiz:
            raise osv.except_osv(_('Error'), _("Error in reading the payment details"))

        if _wiz.processed:
            raise osv.except_osv(_('Error'), _("This request has been processed before"))

        if not _wiz.transaction_lines:
            raise osv.except_osv(_('Error'), _("No payment is selected to be assigned"))

        if len(_wiz.transaction_lines) > 1:
            raise osv.except_osv(_('Error'), _("Please select only one payment to be assigned"))

        if _wiz.transaction_lines[0].amount_to_use <= 0.0:
            raise osv.except_osv(_('Error'), _("Incorrect payment amount (zero available or credit)"))

        if not _wiz.payment_lines:
            raise osv.except_osv(_('Error'), _("No invoice is selected to be assigned"))

        if _wiz.transaction_lines[0].amount_to_use == _wiz.writeoff_amount:
            raise osv.except_osv(_('Error'), _("Payment is not assigned to any invoice"))

        if not _wiz.payment_holding_account:
            raise osv.except_osv(_('Error'), _("Please set the Payment Holding Account for company %s before proceeding") % (_wiz.company_id.name))

        if not _wiz.payment_assign_journal:
            raise osv.except_osv(_('Error'), _("Please set the Payment Assignment Journal"))

        if not _wiz.date:
            raise osv.except_osv(_('Error'), _("Please set the Transaction Date"))

        if context is None:
            context = {}

        _company = _wiz.transaction_lines[0].move_line_id.company_id
        _coy_ccy = _wiz.company_id.currency_id.id
        _ccy = _wiz.payment_assign_journal and _wiz.payment_assign_journal.currency and _wiz.payment_assign_journal.currency.id or _coy_ccy
        _forex = (_ccy != _coy_ccy)

        pool_lang = self.pool.get('res.lang')
        lang = context.get('lang', 'en_US') or 'en_US'
        lang_ids = pool_lang.search(cr, uid, [('code', '=', lang)])[0]
        lang_obj = pool_lang.browse(cr, uid, lang_ids)

        # Validation for selected transaction lines
        for _lines in _wiz.transaction_lines:
            if (_lines.amount_to_use) and ((_lines.amount_residual - _lines.amount_to_use) < 0):
                _formatted_atu = lang_obj.format('%.2f', _lines.amount_to_use, grouping=True)
                _formatted_res = lang_obj.format('%.2f', _lines.amount_residual, grouping=True)
                raise osv.except_osv(_('Error'), _("Line %s transaction %s is less than used %s") % (_lines.name, _formatted_res, _formatted_atu))
            if _company.id != _lines.company_id.id:
                _msg = _("The available payment is recorded in company %s while transaction %s is registered in company %s") % (_company.name, _lines.name, _lines.company_id.name)
                raise osv.except_osv(_('Error'), _msg)

        # Validation for selected invoices
        for _lines in _wiz.payment_lines:
            if (_lines.amount_to_pay) and ((_lines.residual - _lines.amount_to_pay) < 0):
                _formatted_atu = lang_obj.format('%.2f', _lines.amount_to_pay, grouping=True)
                _formatted_res = lang_obj.format('%.2f', _lines.residual, grouping=True)
                raise osv.except_osv(_('Error'), _("Invoice %s payment %s is more than residual %s") % (_lines.number, _formatted_atu, _formatted_res))
            if _company.id != _lines.company_id.id:
                _msg = _("The invoice to pay is recorded in company %s while invoice %s is registered in company %s") % (_company.name, _lines.number, _lines.company_id.name)
                raise osv.except_osv(_('Error'), _msg)

        # A. Create the reconciliation journal entry:
        _payment_line_ids = []
        _invoice_line_ids = []
        _line_ids = []
        _payment = []

        obj_move_line = self.pool.get('account.move.line')
        obj_move = self.pool.get('account.move')
        obj_ccy = self.pool.get('res.currency')

        #  Get the period
        ctx = context.copy()
        ctx.update(company_id=_company.id, account_period_prefer_normal=True)
        _period_ids = self.pool.get('account.period').find(cr, uid, _wiz.date, context=ctx)
        _period_id = _period_ids and _period_ids[0] or False

        # Create the move, the same company id as the available payment
        _move = {
            'journal_id': _wiz.payment_assign_journal.id,
            'date': _wiz.date,
            'period_id': _period_id,
        }
        move_id = obj_move.create(cr, uid, _move, context=ctx)

        #  One leg reversing the payment_holding_account in the payment_lines
        for _lines in _wiz.transaction_lines:
            if _lines.amount_to_use:
                _move_line = _lines.move_line_id
                _amount_to_use_ccy = _forex and obj_ccy.compute(cr, uid, _coy_ccy,
                                        _ccy, _lines.amount_to_use,
                                        context={'date': time.strftime('%Y-%m-%d')}) or False
                _vals = obj_move_line.copy_data(cr, uid, _move_line.id, context=context)
                for k in _vals.keys():
                    # Delete the values that not to be copied over
                    if k in ('reconcile_id', 'reconcile_partial_id', 'date_maturity', 'date_created', 'move_id', 'period_id'):
                        del _vals[k]

                # Set the values to the new values when needed.
                # currency_id, account_id, period_id, and company_id need to be reset because they have defaults
                _vals.update({
                    'move_id': move_id,
                    'date': _wiz.date,
                    'name': 'Reconcile %s' % _move_line.name,
                    'debit': (_lines.amount_to_use > 0) and _lines.amount_to_use or 0.0,
                    'credit': (_lines.amount_to_use < 0) and -_lines.amount_to_use or 0.0,
                    'currency_id': _forex and _ccy or False,
                    'amount_currency': _amount_to_use_ccy,
                    'journal_id': _wiz.payment_assign_journal.id,
                    'account_id': _move_line.account_id.id,
                    'company_id': _move_line.account_id.company_id.id,
                    'period_id': _period_id,
                })

                _line_id = obj_move_line.create(cr, uid, _vals, context=context)
                _payment_line_ids.append([_move_line.id, _line_id])
                _line_ids.append(_line_id)
                _payment.append(_move_line.name)
            else:
                # The line does not have value (0.0), this should not happen
                continue

        # Another leg reversing the invoice's partner AR account
        for _lines in _wiz.payment_lines:
            if _lines.amount_to_pay:
                _invoice = _lines.invoice_id
                _remaining_amount_to_pay = _lines.amount_to_pay
                # Look for the appropriate line to reconcile
                # Identified by the same way move line is created and grouped in
                # account/account_invoice.py's action_move_create():
                # * same account_id as the invoice's
                # * empty tax_code_id, product_id, and analytic_account_id
                # * date_maturity the same as invoice's date_due or empty
                _invoice_moves = filter(lambda x:
                    ((x.account_id.id == _invoice.account_id.id) and
                    (not x.tax_code_id) and
                    (not x.product_id) and
                    (not x.analytic_account_id) and
                    (x.date_maturity == (_invoice.date_due or False))),
                    _invoice.move_id.line_id)
                for _move_line in _invoice_moves:
                    _vals = obj_move_line.copy_data(cr, uid, _move_line.id, context=context)
                    for k in _vals.keys():
                        # Delete the values that not to be copied over
                        if k in ('reconcile_id', 'reconcile_partial_id', 'date_maturity', 'date_created', 'move_id', 'period_id'):
                            del _vals[k]
                    # Set the values to the new values when needed.
                    # currency_id, account_id, period_id, and company_id need to be reset because they have defaults
                    if _remaining_amount_to_pay:
                        _amount_to_pay = min(_move_line.amount_residual, _remaining_amount_to_pay)
                        _amount_to_pay_ccy = _forex and obj_ccy.compute(cr, uid, _coy_ccy,
                                                _ccy, _amount_to_pay,
                                                context={'date': time.strftime('%Y-%m-%d')}) or False
                        _vals.update({
                            'move_id': move_id,
                            'date': _wiz.date,
                            'name': 'Reconcile %s' % _invoice.name,
                            'debit': (_amount_to_pay < 0) and -_amount_to_pay or 0.0,
                            'credit': (_amount_to_pay > 0) and _amount_to_pay or 0.0,
                            'currency_id': _forex and _ccy or False,
                            'amount_currency': _amount_to_pay_ccy,
                            'journal_id': _wiz.payment_assign_journal.id,
                            'account_id': _move_line.account_id.id,
                            'company_id': _move_line.account_id.company_id.id,
                            'period_id': _period_id,
                            'partner_id': _invoice.move_id and _invoice.move_id.partner_id and _invoice.move_id.partner_id.id or False,
                            'date_maturity': _invoice.date_due or False,
                        })
                        _line_id = obj_move_line.create(cr, uid, _vals, context=context)
                        _invoice_line_ids.append([_move_line.id, _line_id])
                        _line_ids.append(_line_id)
                        _remaining_amount_to_pay -= _amount_to_pay
            else:
                # The line does not have value (0.0), this should not happen
                continue

        # Create the write-off line
        if _wiz.writeoff_amount:
            _account_id = _wiz.writeoff_acc_id and _wiz.writeoff_acc_id.id or False
            _amount_wo_ccy = _forex and obj_ccy.compute(cr, uid, _coy_ccy,
                                    _ccy, _wiz.writeoff_amount,
                                    context={'date': time.strftime('%Y-%m-%d')}) or False
            _line_id = obj_move_line.create(cr, uid, {
                'move_id': move_id,
                'date': _wiz.date,
                'name': _wiz.comment,
                'credit': (_wiz.writeoff_amount > 0) and _wiz.writeoff_amount or 0.0,
                'debit': (_wiz.writeoff_amount < 0) and -_wiz.writeoff_amount or 0.0,
                'currency_id': _forex and _ccy or False,
                'amount_currency': _amount_wo_ccy,
                'journal_id': _wiz.payment_assign_journal.id,
                'account_id': _account_id,
                'company_id': _wiz.writeoff_acc_id.company_id.id,
                'period_id': _period_id,
            })
            _line_ids.append(_line_id)
        else:
            # No write-off have value (0.0)
            pass

        # Update and post the move
        _ref = ','.join(_payment)
        _vals = {
            'ref': _ref[:64],
            'narration': 'Assigning payments %s' % _ref,
        }
        obj_move.write(cr, uid, [move_id], _vals, context=context)
        obj_move.post(cr, uid, [move_id], context=context)

        # 2. Reconcile the pair of moves
        for _pair in (_invoice_line_ids + _payment_line_ids):
            obj_move_line.reconcile_partial(cr, uid, _pair, 'manual', context=context)

        _wiz.write({'processed': True}, context=context)

        return {'type': 'ir.actions.act_window_close'}

via_assign_payment()
via_assign_transaction_line()
via_assign_payment_line()
