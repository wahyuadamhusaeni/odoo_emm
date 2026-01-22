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

from openerp.osv import orm, osv, fields
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

CHECKLIST_STATES = [('draft', 'Draft'), ('done', 'Done')]


class bank_checklist(orm.Model):
    _name = 'bank.checklist'

    _columns = {
        'name': fields.char('Name', size=128, required=False, states={'done': [('readonly', True)]}),
        'journal_id': fields.many2one('account.journal', 'Bank Account', required=False, states={'done': [('readonly', True)]}),
        'state': fields.selection(CHECKLIST_STATES, 'Status', required=False, readonly=True),
        'fully_checked': fields.boolean('Fully Checked', readonly=True),
        'parent_ids': fields.one2many('bank.checklist.line', 'line_id', 'Child Codes', store=True, states={'done': [('readonly', True)]}),
        'company_id': fields.many2one('res.company', 'Company', required=False, readonly=True),
        'date': fields.date('Date', required=True, states={'done': [('readonly', True)]}),
    }

    _defaults = {
        'state': lambda *a: 'draft',
        'name': lambda *a: '/',
        'date': fields.date.context_today,
    }

    # Validate record to matching account journal id with each line of journal item
    def _validate_journal(self, cr, uid, ids, context=None):
        for _id in ids:
            bank_obj = self.browse(cr, uid, _id) or False
            journal_id = bank_obj.journal_id and bank_obj.journal_id.id or False
            for line in bank_obj.parent_ids:
                _journal_id = line.move_id and line.move_id.journal_id and line.move_id.journal_id.id or False
                if journal_id != _journal_id:
                    raise osv.except_osv(_('Warning'), _("Journal Item %s does not relate to Bank Account %s!") % (line.move_id and line.move_id.name or '', bank_obj.journal_id and bank_obj.journal_id.name or ''))
        return True

    # Confirm bank checklist state and update fully_check into TRUE
    def action_confirm_bank(self, cr, uid, ids, context=None):
        vals = {}
        valid = self._validate_journal(cr, uid, ids, context=context)
        if valid:
            vals = {'state': 'done', 'fully_checked': True}
        return self.write(cr, uid, ids, vals, context=context)

bank_checklist()


class bank_checklist_line(orm.Model):
    _name = 'bank.checklist.line'

    _columns = {
        'name': fields.char('OBI', required=False, help="Originator to Beneficiary Information"),
        'date': fields.date('Date', required=False),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'ref': fields.char('Reference', size=32),
        'company_id': fields.related('line_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'move_id': fields.many2one('account.move', 'Journal Item', required=False),
        'line_id': fields.many2one('bank.checklist', 'Bank Checklist', required=False),
        'debit': fields.float('Debit', digits_compute=dp.get_precision('Account'), readonly=False),
        'credit': fields.float('Credit', digits_compute=dp.get_precision('Account'), readonly=False),
    }

    _defaults = {
        'date': fields.date.context_today,
        'debit': lambda *a: 0.0,
        'credit': lambda *a: 0.0,
    }

    _sql_constraints = [
        ('journal_item', 'unique (move_id)', 'The journal item must be unique !'),
    ]

bank_checklist_line()
