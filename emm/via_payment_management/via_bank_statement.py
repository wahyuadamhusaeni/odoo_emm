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
from osv import osv
from osv import fields
import decimal_precision as dp
from tools.translate import _
import logging


class via_bank_statement_line(osv.osv):
    _name = 'via.bank.statement.line'
    _description = 'Details of a bank statement transaction.'

    ## write
    #
    # write overrides the parent orm method by disallowing posted entry
    # and update other than canceling a submitted entry.
    #
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        for line in self.browse(cr, uid, ids, context=context):
            if (line.state == 'posted'):
                raise osv.except_osv(_('Error !'), _('You can not modify a posted entry !'))
            if ((line.state == 'cancel') and (vals.get('state', False) not in ('draft'))):
                raise osv.except_osv(_('Error !'), _('You can not modify a cancelled entry !'))
        return super(via_bank_statement_line, self).write(cr, uid, ids, vals, context=context)

    ## action_submit
    #
    # action_submit is called from workflow when a bank statement line is submitted.
    # It will mark the statement line as submitted.
    #
    def action_submit(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for _line in self.browse(cr, uid, ids, context=context):
            if _line.state in ['draft', ]:
                if (_line.credit != 0) and (_line.debit != 0):
                    raise osv.except_osv(_('Error'), _("Please enter only debit or credit for transaction %s!") % (_line.name))
                if (_line.credit == 0) and (_line.debit == 0):
                    raise osv.except_osv(_('Error'), _("Please enter debit or credit for transaction %s!") % (_line.name))

                _line.write({'state': 'submit'})

        return True

    ## action_cancel_draft
    #
    # action_cancel_draft is called from a button to set a cancelled bank statement line.
    # to a draft state
    #
    def action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for _id in ids:
            wf_service.trg_delete(uid, 'via.bank.statement.line', _id, cr)
            wf_service.trg_create(uid, 'via.bank.statement.line', _id, cr)
        return True

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
        currency_obj = self.pool.get('res.currency')
        for _line in self.browse(cr, uid, ids, context=context):
            if _line.state in ['submit', ]:
                if (_line.credit != 0) and (_line.debit != 0):
                    raise osv.except_osv(_('Error'), _("Please enter only debit or credit for transaction %s!") % (_line.name))
                if (_line.credit == 0) and (_line.debit == 0):
                    raise osv.except_osv(_('Error'), _("Please enter debit or credit for transaction %s!") % (_line.name))

                context_multi_currency = context.copy()
                context_multi_currency.update({'date': _line.date})

                if _line.journal_id.sequence_id:
                    name = seq_obj.get_id(cr, uid, _line.journal_id.sequence_id.id)
                else:
                    raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal !'))
                if not name:
                    raise osv.except_osv(_('Error !'), _('Cannot get sequence for journal %s for company %s!') % (_line.journal_id.name, self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.name))
                if not _line.ref:
                    ref = name.replace('/', '')
                else:
                    ref = _line.ref

                _period = period_obj.find(cr, uid, dt=_line.date, context=context) or False
                move = {
                    'name': name,
                    'journal_id': _line.journal_id.id,
                    'date': _line.date,
                    'ref': ref,
                    'period_id': _period and _period[0] or False
                }
                move_id = move_pool.create(cr, uid, move)

                # Create the first line manually
                company_currency = _line.journal_id.company_id.currency_id.id
                current_currency = _line.journal_id.currency.id and _line.journal_id.currency.id or company_currency
                debit = currency_obj.compute(cr, uid, company_currency, current_currency, _line.debit, context=context)
                credit = currency_obj.compute(cr, uid, company_currency, current_currency, _line.credit, context=context)

                if debit < 0:
                    credit = -debit
                    debit = 0.0
                if credit < 0:
                    debit = -credit
                    credit = 0.0
                sign = debit - credit < 0 and -1 or 1
                # Create the first line of the move
                move_line = {
                    'name': _line.name or '/',
                    'debit': debit,
                    'credit': credit,
                    'account_id': _line.account_id.id,
                    'move_id': move_id,
                    'journal_id': _line.journal_id.id,
                    'period_id': _period and _period[0] or False,
                    'partner_id': _line.partner_id.id,
                    'date': _line.date,
                    'date_maturity': _line.date
                }

                if company_currency != current_currency:
                    move_line = {
                        'currency_id': current_currency or False,
                        'amount_currency': sign * (_line.debit + _line.credit) or 0.0,
                    }

                move_line_pool.create(cr, uid, move_line)
                # Create the 2nd line of the move
                move_line = {
                    'name': _line.name or '/',
                    'debit': credit,
                    'credit': debit,
                    'account_id': _line.opp_account_id.id,
                    'move_id': move_id,
                    'journal_id': _line.journal_id.id,
                    'period_id': _period and _period[0] or False,
                    'partner_id': _line.partner_id.id,
                    'date': _line.date,
                    'date_maturity': _line.date
                }

                if company_currency != current_currency:
                    move_line = {
                        'currency_id': current_currency or False,
                        'amount_currency': sign * (_line.debit + _line.credit) or 0.0,
                    }

                move_line_pool.create(cr, uid, move_line)

                move_pool.post(cr, uid, [move_id], context={})

                _line.write({'state': 'posted', 'move_id': move_id})

        return True

    _columns = {
        'date': fields.date('Bank Date', required=True, readonly=False, states={'posted': [('readonly', True)]}),
        'journal_id': fields.many2one('account.journal', 'Bank Journal', required=True,
            readonly=False, states={'posted': [('readonly', True)]}, domain="[('type', 'in', ('bank', 'cash'))]"),
        'account_id': fields.related('journal_id', 'default_debit_account_id', type='many2one',
            relation='account.account', string='Account used in this journal', readonly=True,
            help='used in statement reconciliation domain, but shouldn\'t be used elswhere.'),
        'opp_account_id': fields.many2one('account.account', 'Opposing Account', required=True, readonly=False, states={'posted': [('readonly', True)]}),
        'company_id': fields.related('journal_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'name': fields.char('Name', size=255, required=True, readonly=False, states={'posted': [('readonly', True)]}),
        'ref': fields.char('Reference', size=64, readonly=False, states={'posted': [('readonly', True)]}),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=False, states={'posted': [('readonly', True)]}),
        'debit': fields.float('Debit', digits_compute=dp.get_precision('Account'), readonly=False, states={'posted': [('readonly', True)]}),
        'credit': fields.float('Credit', digits_compute=dp.get_precision('Account'), readonly=False, states={'posted': [('readonly', True)]}),
        'create_uid': fields.many2one('res.users', 'User', select=True, readonly=True),
        'move_id': fields.many2one('account.move', 'Move', readonly=False, states={'posted': [('readonly', True)]}),
        'state': fields.selection([('draft', 'Draft'), ('submit', 'Submitted'), ('cancel', 'Cancelled'), ('posted', 'Posted')],
            'State', required=True, readonly=True,
            help='When new statement line is created the state will be \'Draft\'. \
            \n* A \'Draft\' statement line can be then \'Submitted\' and hence make editing not possible. \
            \n* A \'Submitted\' statement line can then be \'Posted\' and hence make cancelling not possible. \
            \n* Any statement in \'Draft\' or \'Sumitted\' state can be \'Cancelled\''),
    }

    _defaults = {
        'debit': lambda *a: 0.0,
        'credit': lambda *a: 0.0,
        'date': fields.date.context_today,
        'state': lambda *a: 'draft',
    }

via_bank_statement_line()


class via_bank_statement_line_action(osv.osv_memory):
    """
    This is a place-holder wizard to hold all multi-actions
    """

    _name = "via.bank.statement.line.action"
    _description = "Perform action on the selected bank statement transactions"

    def action_submit(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        if context is None:
            context = {}
        data_inv = self.pool.get('via.bank.statement.line').read(cr, uid, context['active_ids'], ['state'], context=context)

        for record in data_inv:
            if record['state'] not in ('draft'):
                raise osv.except_osv(_('Warning'), _("Selected Invoice(s) cannot be submitted as they are not in 'Draft'!"))
            wf_service.trg_validate(uid, 'via.bank.statement.line', record['id'], 'vbsl_submit', cr)
        return {'type': 'ir.actions.act_window_close'}

    def action_post(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        if context is None:
            context = {}
        data_inv = self.pool.get('via.bank.statement.line').read(cr, uid, context['active_ids'], ['state'], context=context)

        for record in data_inv:
            if record['state'] not in ('submit'):
                raise osv.except_osv(_('Warning'), _("Selected Invoice(s) cannot be posted as they are not in 'Submitted'!"))
            wf_service.trg_validate(uid, 'via.bank.statement.line', record['id'], 'vbsl_post', cr)
        return {'type': 'ir.actions.act_window_close'}

via_bank_statement_line_action()
