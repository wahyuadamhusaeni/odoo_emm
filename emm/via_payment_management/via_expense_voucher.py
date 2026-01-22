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
import netsvc
from osv import osv, fields
import decimal_precision as dp
from tools.translate import _
from via_base_enhancements.tools import resolve_o2m_operations, prep_dict_for_write


class via_account_move_line(osv.osv):
    _name = 'via.account.move.line'
    _description = 'A proxy of the actual account_move_line table'

    _columns = {
        'exp_voucher_id': fields.many2one('via.expense.voucher', 'Expense Voucher', readonly=True),
        'move_line_id': fields.many2one('account.move.line', 'Move Line', required=True),
        'name': fields.related('move_line_id', 'name', type='char', size=64, string='Name', store=True, readonly=True),
        'quantity': fields.related('move_line_id', 'quantity', type='float', digits=(16, 2), string='Qty', store=True, readonly=True),
        'product_uom_id': fields.related('move_line_id', 'product_uom_id', type='many2one', relation='product.uom', string='UoM', store=True, readonly=True),
        'product_id': fields.related('move_line_id', 'product_id', type='many2one', relation='product.product', string='Product', store=True, readonly=True),
        'debit': fields.related('move_line_id', 'debit', type='float', digits_compute=dp.get_precision('Account'), string='Debit', store=True, readonly=True),
        'credit': fields.related('move_line_id', 'credit', type='float', digits_compute=dp.get_precision('Account'), string='Credit', store=True, readonly=True),
        'account_id': fields.related('move_line_id', 'account_id', type='many2one', relation='account.account', string='Account', store=True, readonly=True),
        'move_id': fields.related('move_line_id', 'move_id', type='many2one', relation='account.move', string='Move', store=True, readonly=True),
        'narration': fields.related('move_line_id', 'narration', type='text', string='Narration', store=True, readonly=True),
        'ref': fields.related('move_line_id', 'ref', string='Reference', type='char', size=64, store=True, readonly=True),
        'statement_id': fields.related('move_line_id', 'statement_id', type='many2one', relation='account.bank.statement', string='Statement', store=True, readonly=True),
        'reconcile_id': fields.related('move_line_id', 'reconcile_id', type='many2one', relation='account.move.reconcile', string='Assg.', store=True, readonly=True),
        'reconcile_partial_id': fields.related('move_line_id', 'reconcile_partial_id', type='many2one', relation='account.move.reconcile', string='Partial Assg.', store=True, readonly=True),
        'amount_currency': fields.related('move_line_id', 'amount_currency', type='float', digits_compute=dp.get_precision('Account'), string='Amount', store=True, readonly=True),
        'amount_residual_currency': fields.related('move_line_id', 'amount_residual_currency', type='float', digits_compute=dp.get_precision('Account'), string='Amount Residual', store=True, readonly=True),
        'amount_residual': fields.related('move_line_id', 'signed_amount_residual', type='float', digits_compute=dp.get_precision('Account'), string='Amount Residual', store=True, readonly=True),
        'currency_id': fields.related('move_line_id', 'currency_id', type='many2one', relation='res.currency', string='Currency', store=True, readonly=True),
        'period_id': fields.related('move_line_id', 'period_id', type='many2one', relation='account.period', string='Period', store=True, readonly=True),
        'journal_id': fields.related('move_line_id', 'journal_id', type='many2one', relation='account.journal', string='Journal', store=True, readonly=True),
        'blocked': fields.related('move_line_id', 'blocked', type='boolean', string='Litigation', store=True, readonly=True),
        'partner_id': fields.related('move_line_id', 'partner_id', type='many2one', relation='res.partner', string='Partner', store=True, readonly=True),
        'date_maturity': fields.related('move_line_id', 'date_maturity', type='date', string='Due Date', store=True, readonly=True),
        'date': fields.related('move_line_id', 'date', string='Effective date', type='date', store=True, readonly=True),
        'balance': fields.related('move_line_id', 'balance', string='Balance', store=True, readonly=True),
        'tax_code_id': fields.related('move_line_id', 'tax_code_id', type='many2one', relation='account.tax.code', string='Tax Account', store=True, readonly=True),
        'tax_amount': fields.related('move_line_id', 'tax_amount', type='float', digits_compute=dp.get_precision('Account'), string='Tax/Base Amount', store=True, readonly=True),
        'account_tax_id': fields.related('move_line_id', 'account_tax_id', type='many2one', relation='account.tax', string='Tax', store=True, readonly=True),
        'analytic_account_id': fields.related('move_line_id', 'analytic_account_id', type='many2one', relation='account.analytic.account', string='Analytic Account', store=True, readonly=True),
        'company_id': fields.related('move_line_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'amount_to_use': fields.float('Amount To Use', digits_compute=dp.get_precision('Sale Price')),
    }

    def onchange_move_line_id(self, cr, uid, ids, move_line_id, context=None):
        if context is None:
            context = {}

        # Not saved o2m row sometimes pass the ids as a non numeric information
        if ids and isinstance(ids[0], (int, long, )) and ids[0]:
            _trx_line = self.pool.get('via.account.move.line').read(cr, uid, ids[0], context=context)
            if (_trx_line['move_line_id'] == move_line_id):
                return {}

        rv = {'value': {'amount_to_use': 0.0}}
        if move_line_id:
            _aml = self.pool.get('account.move.line').browse(cr, uid, move_line_id, context=context)
            if _aml:
                _aml_data = _aml.read()[0]
                _aml_data = prep_dict_for_write(cr, uid, _aml_data, context=context)

                _aml_data['amount_residual'] = _aml.signed_amount_residual
                _aml_data['amount_to_use'] = _aml.signed_amount_residual
                rv['value'].update(_aml_data)

        return rv


class via_expense_voucher_line(osv.osv):
    _name = 'via.expense.voucher.line'
    _description = 'Details of voucher for journal against temporary bank moves'

    _columns = {
        'exp_voucher_id': fields.many2one('via.expense.voucher', 'Expense Voucher', readonly=True),
        'move_line_id': fields.many2one('account.move.line', 'Move Line', readonly=True),
        'ref': fields.char('Reference', size=64, readonly=False, states={'posted': [('readonly', True)]}),
        'name': fields.char('Name', size=64, required=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=False, states={'posted': [('readonly', True)]}),
        'account_id': fields.many2one('account.account', 'Account',
            domain="[('type','not in', ('view','consolidation','closed')), '|', ('company_id', '=', parent.company_id), ('company_id', '=', False)]",
            required=True, readonly=False, states={'posted': [('readonly', True)]}),
        'debit': fields.float('Debit', digits_compute=dp.get_precision('Account'), readonly=False, states={'posted': [('readonly', True)]}),
        'credit': fields.float('Credit', digits_compute=dp.get_precision('Account'), readonly=False, states={'posted': [('readonly', True)]}),
        'state': fields.related('exp_voucher_id', 'state', type='char', string='State', readonly=True),
    }

    _defaults = {
        'debit': lambda *a: 0.0,
        'credit': lambda *a: 0.0,
    }


class via_expense_voucher(osv.osv):
    _name = 'via.expense.voucher'
    _description = 'Voucher for journal against temporary bank moves'
    _rec_name = 'date'
    _order = "date desc, id desc"

    ## onchange_get_lines
    #
    # set the values of several fields:
    # - populate bank_lines based on the given journal and payment_holding_account and reconcile status
    #
    def onchange_get_lines(self, cr, uid, ids, date, opp_acc_id, journal_id, context=None):
        _aml_pool = self.pool.get('account.move.line')
        _move_lines = _aml_pool.search(cr, uid,
            [('date', '=', date), ('account_id', '=', opp_acc_id), ('journal_id', '=', journal_id), ('reconcile_id', '=', False)],
            context=context)

        # It is assumed that only one record is changed at a time
        _bank_lines = []
        _assignment_lines = []
        _bank_m2olines = []
        _bank_mlines = {}
        _vexv = False
        rv = {'value': {}}
        if ids:
            _vexv = self.pool.get('via.expense.voucher').browse(cr, uid, ids[0], context=context)
            _assignment_lines = map(lambda x: x.id, _vexv.assignment_lines)

            for _line in _vexv.bank_lines:
                _bank_mlines[_line.move_line_id.id] = _line.id

        _aaml_pool = self.pool.get('via.account.move.line')
        for _line in _move_lines:
            if _line in _bank_mlines:
                _bank_lines.append(_bank_mlines[_line])
                _bank_m2olines.append((1, _bank_mlines[_line], {}))
            else:
                if ids and _vexv:
                    _new_line = _aaml_pool.create(cr, uid, {'exp_voucher_id': _vexv.id, 'move_line_id': _line}, context=context)
                    _bank_lines.append(_new_line)
                    _bank_m2olines.append((1, _new_line, {}))
                else:
                    _aml = _aml_pool.browse(cr, uid, _line, context=context)
                    if _aml:
                        _aml_data = _aml.read()[0]
                        for _key in ['id', 'create_uid', 'create_date', 'write_uid', 'write_date', 'amount_residual']:
                            if _key in _aml_data:
                                del _aml_data[_key]
                        _aml_data = prep_dict_for_write(cr, uid, _aml_data, context=context)

                        _aml_data['move_line_id'] = _line
                        _aml_data['amount_residual'] = _aml.signed_amount_residual
                        _aml_data['amount_to_use'] = _aml.signed_amount_residual
                        rv['value'].update(_aml_data)

                    _bank_lines.append(_aml_data)
                    _bank_m2olines.append((1, False, _aml_data))

        rv = self.onchange_lines(cr, uid, ids, _bank_m2olines, _assignment_lines, context=context)
        rv['value']['bank_lines'] = _bank_lines

        return rv

    ## onchange_lines
    #
    # set the values of several fields:
    # - no_of_lines is set based on number of bank transaction lines
    # - bank_sum is sum of all (credit - debit) of the bank transaction lines
    # - assingment_sum is sum of all (credit - debit) of the assignment transaction lines
    # - writeoff_amount is bank_sum - assignment_sum
    #
    def onchange_lines(self, cr, uid, ids, bank_lines, assignment_lines, context=None):
        _bank_sum = 0.0
        _assignment_sum = 0.0

        _line_pool = self.pool.get('via.account.move.line')
        bank_lines = resolve_o2m_operations(cr, uid, _line_pool, bank_lines, ['amount_to_use'], context)
        _line_pool = self.pool.get('via.expense.voucher.line')
        assignment_lines = resolve_o2m_operations(cr, uid, _line_pool, assignment_lines, ['credit', 'debit'], context)

        for _line in bank_lines:
            _bank_sum -= _line.get('amount_to_use', 0.0)

        for _line in assignment_lines:
            _assignment_sum += (_line['credit'] - _line['debit'])

        return {'value': {
            'no_of_lines': len(bank_lines),
            'bank_sum': _bank_sum,
            'assignment_sum': _assignment_sum,
            'with_writeoff': (_bank_sum != _assignment_sum),
            'writeoff_amount': _bank_sum - _assignment_sum,
        }}

    ## write
    #
    # write overrides the parent orm method by disallowing posted entry
    # and update other than canceling a submitted entry.
    #
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        for line in self.browse(cr, uid, ids, context=context):
            if vals:
                if (line.state == 'posted'):
                    raise osv.except_osv(_('Error !'), _('You can not modify a posted entry !'))
                if ((line.state == 'cancel') and (vals.get('state', False) not in ('draft'))):
                    raise osv.except_osv(_('Error !'), _('You can not modify a cancelled entry !'))
        return super(via_expense_voucher, self).write(cr, uid, ids, vals, context=context)

    ## action_cancel_draft
    #
    # action_cancel_draft is called from a button to set a cancelled bank statement line.
    # to a draft state
    #
    def action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for _id in ids:
            wf_service.trg_delete(uid, 'via.expense.voucher', _id, cr)
            wf_service.trg_create(uid, 'via.expense.voucher', _id, cr)
        return True

    ## action_submit
    #
    # action_submit is called from workflow when a voucher is submitted.
    # It will perform validation on the data entered and mark the voucher
    # as submitted if the document is clean.
    #
    def action_submit(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for _doc in self.browse(cr, uid, ids, context=context):
            if _doc.state in ['draft', ]:
                if not _doc.opp_account_id:
                    raise osv.except_osv(_('Error'), _("Company %s does not have Payment Holding Account set-up. Please fix.") % (_doc.company_id.name))
                if not _doc.bank_lines:
                    raise osv.except_osv(_('Error'), _("No bank transaction selected!"))
                for _line in _doc.assignment_lines:
                    if (_line.credit != 0) and (_line.debit != 0):
                        raise osv.except_osv(_('Error'), _("Please enter only debit or credit for line %s of voucher %s!") % (_line.name, _doc.id))
                    if (_line.credit == 0) and (_line.debit == 0):
                        raise osv.except_osv(_('Error'), _("Please enter debit or credit for for line %s of voucher %s!") % (_line.name, _doc.id))
                if _doc.writeoff_amount and not (_doc.writeoff_acc_id and _doc.comment):
                    raise osv.except_osv(_('Error'), _("Please provide Write-Off Account and Comment in voucher %s!") % (_doc.id))

                _doc.write({'state': 'submit'})

            return True

        return False

    ## action_post
    #
    # action_post is called from workflow when a bank statement line is posted.
    # It will create corresponding account move and account move line
    #
    def action_post(self, cr, uid, ids, context=None):

        if context is None:
            context = {}

        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        period_obj = self.pool.get('account.period')
        seq_obj = self.pool.get('ir.sequence')
        for _doc in self.browse(cr, uid, ids, context=context):
            if _doc.state in ['submit', ]:
                _line_to_recon = []

                if _doc.journal_id.sequence_id:
                    name = seq_obj.get_id(cr, uid, _doc.journal_id.sequence_id.id)
                else:
                    raise osv.except_osv(_('Error !'), _('Please define a sequence for journal %s!') % (_doc.journal_id.name))
                if not name:
                    raise osv.except_osv(_('Error !'), _('Cannot get sequence for journal %s for company %s!') % (_doc.journal_id.name, self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.name))
                ref = name.replace('/', '')

                _period = period_obj.find(cr, uid, dt=_doc.assign_date, context=context) or False
                move = {
                    'name': name,
                    'journal_id': _doc.journal_id.id,
                    'date': _doc.assign_date,
                    'ref': ref,
                    'period_id': _period and _period[0] or False
                }
                move_id = move_pool.create(cr, uid, move)

                # Create move line for each assignment_lines
                for _line in _doc.assignment_lines:
                    if (_line.credit != 0) and (_line.debit != 0):
                        raise osv.except_osv(_('Error'), _("Please enter only debit or credit for line %s of voucher %s!") % (_line.name, _doc.id))
                    if (_line.credit == 0) and (_line.debit == 0):
                        raise osv.except_osv(_('Error'), _("Please enter debit or credit for for line %s of voucher %s!") % (_line.name, _doc.id))

                    debit = _line.debit
                    credit = _line.credit

                    if debit < 0:
                        credit = -debit
                        debit = 0.0
                    if credit < 0:
                        debit = -credit
                        credit = 0.0

                    move_line = {
                        'name': _line.name or '/',
                        'debit': debit,
                        'credit': credit,
                        'account_id': _line.account_id.id,
                        'move_id': move_id,
                        'journal_id': _doc.journal_id.id,
                        'period_id': _period and _period[0] or False,
                        'partner_id': _line.partner_id and _line.partner_id.id or False,
                        'date': _doc.assign_date,
                    }
                    move_line_pool.create(cr, uid, move_line)

                # Create move line for each bank_lines, reverse the credit and debit
                for _line in _doc.bank_lines:
                    # Only if amount to use is there, if not, ignore it.
                    if _line.amount_to_use:
                        debit = 0.0
                        credit = _line.amount_to_use

                        if debit < 0:
                            credit = -debit
                            debit = 0.0
                        if credit < 0:
                            debit = -credit
                            credit = 0.0

                        move_line = {
                            'name': _line.name or '/',
                            'debit': debit,
                            'credit': credit,
                            'account_id': _line.account_id.id,
                            'move_id': move_id,
                            'journal_id': _doc.journal_id.id,
                            'period_id': _period and _period[0] or False,
                            'partner_id': _line.partner_id and _line.partner_id.id or False,
                            'date': _doc.assign_date,
                        }
                        id = move_line_pool.create(cr, uid, move_line)
                        _line_to_recon.append([id, _line.move_line_id.id])

                # Create move line for write-off if any
                if _doc.writeoff_amount:
                    debit = 0.0
                    credit = _doc.writeoff_amount

                    if debit < 0:
                        credit = -debit
                        debit = 0.0
                    if credit < 0:
                        debit = -credit
                        credit = 0.0

                    move_line = {
                        'name': _doc.comment,
                        'debit': debit,
                        'credit': credit,
                        'account_id': _doc.writeoff_acc_id.id,
                        'move_id': move_id,
                        'journal_id': _doc.journal_id.id,
                        'period_id': _period and _period[0] or False,
                        'date': _doc.assign_date,
                    }
                    move_line_pool.create(cr, uid, move_line)

                move_pool.post(cr, uid, [move_id], context={})

                for _pair in _line_to_recon:
                    move_line_pool.reconcile_partial(cr, uid, _pair, 'manual', context=context)

                _doc.write({'state': 'posted', 'move_id': move_id})

            return True

        return False

    def _get_period(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        periods = self.pool.get('account.period').find(cr, uid, context=context)
        return periods and periods[0] or False

    def _get_expense_journal(self, cr, uid, context=None):
        if context is None:
            context = {}
        _ex_journals = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.expense_journals
        rv = _ex_journals and [x.id for x in _ex_journals] or []
        return rv

    def _get_voucher_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('via.expense.voucher.line').browse(cr, uid, ids, context=context):
            result[line.exp_voucher_id.id] = True
        return result.keys()

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for _vexv in self.browse(cr, uid, ids, context=context):
            res[_vexv.id] = {
                'no_of_lines': 0,
                'bank_sum': 0.0,
                'assignment_sum': 0.0,
                'writeoff_amount': 0.0,
                'with_writeoff': False,
            }
            for line in _vexv.bank_lines:
                res[_vexv.id]['bank_sum'] -= line.amount_to_use
            for line in _vexv.assignment_lines:
                res[_vexv.id]['assignment_sum'] += (line.credit - line.debit)
            res[_vexv.id]['writeoff_amount'] = res[_vexv.id]['bank_sum'] - res[_vexv.id]['assignment_sum']
            res[_vexv.id]['with_writeoff'] = (res[_vexv.id]['writeoff_amount'] != 0.0)
            res[_vexv.id]['no_of_lines'] = len(_vexv.bank_lines)
        return res

    _columns = {
        'date': fields.date('Bank Date', required=True, readonly=False, states={'posted': [('readonly', True)]}),
        'state': fields.selection([('draft', 'Draft'), ('submit', 'Submitted'), ('cancel', 'Cancelled'), ('posted', 'Posted')],
            'State', required=True, readonly=True,
            help='When new expense voucher is created the state will be \'Draft\'. \
            \n* A \'Draft\' expense voucher can be then \'Submitted\' and hence make editing not possible. \
            \n* A \'Submitted\' expense voucher can then be \'Posted\' and hence make cancelling not possible. \
            \n* Any voucher in \'Draft\' or \'Sumitted\' state can be \'Cancelled\''),
        'source_journal_id': fields.many2one('account.journal', 'Source Journal', required=True,
            readonly=False, states={'posted': [('readonly', True)]}, domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]"),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'expense_journals': fields.related('company_id', 'expense_journals', type='many2many', relation='account.journal', string='Journals', readonly=True),
        'opp_account_id': fields.related('company_id', 'payment_holding_account', type='many2one', relation='account.account', string='Account', store=True, readonly=True),
        'journal_id': fields.many2one('account.journal', 'Assignment Journal', required=True,
            readonly=False, states={'posted': [('readonly', True)]},
            domain="[('type', 'not in', ('bank', 'cash')), ('company_id', '=', company_id), ('id', 'in', expense_journals[0][2])]"),
        'assign_date': fields.date('Assignment Date', required=True, readonly=False, states={'posted': [('readonly', True)]}),
        'period_id': fields.many2one('account.period', 'Period', readonly=False, states={'posted': [('readonly', True)]}),
        'bank_lines': fields.one2many('via.account.move.line', 'exp_voucher_id', 'Bank Transactions', ondelete='cascade', readonly=False, states={'posted': [('readonly', True)]}),
        'assignment_lines': fields.one2many('via.expense.voucher.line', 'exp_voucher_id', 'Assignment', ondelete='cascade', readonly=False, states={'posted': [('readonly', True)]}),
        'no_of_lines': fields.function(_amount_all, method=True, string='No. of Lines',
            store={
                'via.expense.voucher': (lambda self, cr, uid, ids, c={}: ids, ['bank_lines', 'assignment_lines'], 20),
                'via.expense.voucher.line': (_get_voucher_line, ['debit', 'credit'], 20),
            },
            multi='all', type="integer", readonly=True),
        'bank_sum': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Bank Total',
            store={
                'via.expense.voucher': (lambda self, cr, uid, ids, c={}: ids, ['bank_lines', 'assignment_lines'], 20),
                'via.expense.voucher.line': (_get_voucher_line, ['debit', 'credit'], 20),
            },
            multi='all', type="float", readonly=True),
        'assignment_sum': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Assignment Total',
            store={
                'via.expense.voucher': (lambda self, cr, uid, ids, c={}: ids, ['bank_lines', 'assignment_lines'], 20),
                'via.expense.voucher.line': (_get_voucher_line, ['debit', 'credit'], 20),
            },
            multi='all', type="float", readonly=True),
        'writeoff_amount': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Write-Off Amount',
            store={
                'via.expense.voucher': (lambda self, cr, uid, ids, c={}: ids, ['bank_lines', 'assignment_lines'], 20),
                'via.expense.voucher.line': (_get_voucher_line, ['debit', 'credit'], 20),
            },
            multi='all', type='float', readonly=True),
        'with_writeoff': fields.function(_amount_all, method=True, string='With Write-Off',
            store={
                'via.expense.voucher': (lambda self, cr, uid, ids, c={}: ids, ['bank_lines', 'assignment_lines'], 20),
                'via.expense.voucher.line': (_get_voucher_line, ['debit', 'credit'], 20),
            },
            multi='all', type='char', size=20, readonly=True),
        'writeoff_acc_id': fields.many2one('account.account', 'Write-Off Account', readonly=False, states={'posted': [('readonly', True)]}),
        'comment': fields.char('Write-Off Comment', size=64, readonly=False, states={'posted': [('readonly', True)]}),
        'move_id': fields.many2one('account.move', 'Move', readonly=True),
    }

    _defaults = {
        'date': fields.date.context_today,
        'assign_date': fields.date.context_today,
        'state': lambda *a: 'draft',
        'period_id': _get_period,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        'opp_account_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.payment_holding_account.id,
        'expense_journals': _get_expense_journal,
    }

via_expense_voucher()
via_expense_voucher_line()
via_account_move_line()
