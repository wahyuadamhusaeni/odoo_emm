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
import logging


class via_batch_statement_entry_line(osv.osv_memory):
    _name = 'via.batch.statement.entry.line'
    _description = 'A place holder for bank statement line.'

    _columns = {
        'wizard_id': fields.many2one('via.batch.statement.entry', 'Wizard', readonly=True),
        'name': fields.char('Name', size=255, required=True),
        'ref': fields.char('Reference', size=64),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'debit': fields.float('Debit', digits_compute=dp.get_precision('Account')),
        'credit': fields.float('Credit', digits_compute=dp.get_precision('Account')),
    }

    _defaults = {
        'debit': lambda *a: 0.0,
        'credit': lambda *a: 0.0,
    }


class via_batch_statement_entry(osv.osv_memory):
    _name = 'via.batch.statement.entry'
    _description = 'Form to enter statement lines of same Date, Journal and Account'
    __logger = logging.getLogger(_name)

    def write(self, cr, uid, ids, vals, context={}):
        try:
            return super(via_batch_statement_entry, self).write(cr, uid, ids, vals, context=context)
        except:
            raise

    def onchange_journal(self, cr, uid, ids, journal_id, context=None):
        _journal = journal_id and self.pool.get('account.journal').browse(cr, uid, journal_id, context=context) or False
        _co_id = _journal and _journal.company_id or False
        _opp_acc_id = _co_id and _co_id.payment_holding_account or False
        return {'value': {'company_id': _co_id and _co_id.id or False, 'opp_account_id': _opp_acc_id and _opp_acc_id.id or False}}

    def record_transactions(self, cr, uid, ids, context=None):
        """
         Record actual bank statements and create corresponding move line in draft state
        """
        # It is assumed that only 1 wizard exist at any point of time for each session
        _wiz = self.pool.get('via.batch.statement.entry').browse(cr, uid, ids[0], context=context)

        if not _wiz:
            raise osv.except_osv(_('Error'), _("Error in reading the transaction details"))

        if not _wiz.journal_id:
            raise osv.except_osv(_('Error'), _("No journal selected!"))

        if not _wiz.journal_id.company_id:
            raise osv.except_osv(_('Error'), _("Journal %s is not linked to any company.  Please fix.") % (_wiz.journal_id.name))

        if not _wiz.journal_id.company_id.payment_holding_account:
            raise osv.except_osv(_('Error'), _("Company %s does not have Payment Holding Account set-up. Please fix.") % (_wiz.journal_id.company_id.name))

        if not _wiz.statement_lines:
            raise osv.except_osv(_('Error'), _("No transaction lines entered!"))

        if context is None:
            context = {}

        _obj_pool = self.pool.get('via.bank.statement.line')
        _created_lines = []
        _statement = {
            'date': _wiz.date,
            'journal_id': _wiz.journal_id.id,
            'opp_account_id': _wiz.journal_id.company_id.payment_holding_account.id,
        }
        self.__logger.debug('Payment holding account is %s', _wiz.journal_id.company_id.payment_holding_account.name)

        for _line in _wiz.statement_lines:
            _statement.update({
                'name': _line.name,
                'ref': _line.ref,
                'partner_id': _line.partner_id.id,
                'debit': _line.debit,
                'credit': _line.credit,
            })
            _created_lines.append(_obj_pool.create(cr, uid, _statement))

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        mod_id = mod_obj.search(cr, uid, [('name', '=', 'action_bank_statement_lines')])[0]
        res_id = mod_obj.read(cr, uid, mod_id, ['res_id'])['res_id']
        act_win = act_obj.read(cr, uid, res_id, [])
        act_win['target'] = 'new'
        act_win['domain'] = [('id', 'in', _created_lines)]
        return act_win
        # return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'date': fields.date('Bank Date', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True),
        'journal_id': fields.many2one('account.journal', 'Bank Journal', domain="[('type','in',('bank','cash')), ('company_id', '=', company_id)]", required=True),
        # Use the opposing account set-up in the company
        'opp_account_id': fields.related('company_id', 'payment_holding_account', string="Opposing Account", type='many2one', store=True, relation='account.account', required=True, readonly=True),

        'statement_lines': fields.one2many('via.batch.statement.entry.line', 'wizard_id', 'Line Details'),
    }

    _defaults = {
        'date': fields.date.context_today,
        'company_id': lambda s, c, u, ctx: s.pool.get('res.users').browse(c, u, u, ctx).company_id.id or False,
        'opp_account_id': lambda s, c, u, ctx: s.pool.get('res.users').browse(c, u, u, ctx).company_id.payment_holding_account.id or False,
    }

via_batch_statement_entry()
via_batch_statement_entry_line()
