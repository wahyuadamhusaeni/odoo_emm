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

from openerp.osv import fields, orm
from openerp.tools.translate import _
from openerp import netsvc
from datetime import datetime as DT
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class account_invoice_refund(orm.TransientModel):
    _inherit = "account.invoice.refund"

    _columns = {
        'invoice_lines': fields.many2many('account.invoice.line', 'invoice_refund_rel', string='Invoices Lines', readonly=True),
    }

    # This is a enhanced copy of the same method from the original account/wizard/account_invoice_refund.py
    # This method will process refund from the given invoice_lines instead of from invoice
    def compute_refund_line(self, cr, uid, ids, mode='refund', context=None):
        """
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: the account invoice refund’s ID or list of IDs

        """
        inv_ref_inv_obj = self.pool.get('account.invoice.refund.invoice')
        inv_obj = self.pool.get('account.invoice')
        reconcile_obj = self.pool.get('account.move.reconcile')
        account_m_line_obj = self.pool.get('account.move.line')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        wf_service = netsvc.LocalService('workflow')
        inv_tax_obj = self.pool.get('account.invoice.tax')
        inv_line_obj = self.pool.get('account.invoice.line')
        res_users_obj = self.pool.get('res.users')
        claim_obj = self.pool.get('crm.claim')
        period_obj = self.pool.get('account.period')

        if context is None:
            context = {}

        claim = context.get('claim_id', False)
        claim = claim and claim_obj.browse(cr, uid, claim, context=context) or False

        for form in self.browse(cr, uid, ids, context=context):
            created_inv = []
            date = False
            period = False
            description = False
            company = res_users_obj.browse(cr, uid, uid, context=context).company_id
            journal_id = form.journal_id.id

            _invoice_ids = list(set([x.invoice_id.id for x in form.invoice_lines]))
            _invoice_line_ids = list(set([x.id for x in form.invoice_lines]))
            ctx = context.copy()
            ctx.update({'claim_invoice_line': _invoice_line_ids})
            inv = False
            for inv in inv_obj.browse(cr, uid, _invoice_ids, context=context):
                refund = None
                inv_id = False
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    raise orm.except_orm(_('Error!'), _('Cannot %s draft/proforma/cancel invoice.') % (mode))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise orm.except_orm(_('Error!'), _('Cannot %s invoice which is already reconciled, invoice should be unreconciled first. You can only refund this invoice.') % (mode))

                journal_id = journal_id or (inv.journal_id and inv.journal_id.id) or False
                date = form.date or inv.date_invoice or DT.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
                date_period = period_obj.find(cr, uid, dt=date, context=context)
                period = ((form.period and form.period.id) or
                          (date_period and date_period[0]) or
                          (inv.period_id and inv.period_id.id) or False)
                description = form.description or inv.name or claim.name and (_('Refund for claim %s') % claim.name) or ''

                if not period:
                    raise orm.except_orm(_('Data Insufficient !'), _('No Period found on Invoice!'))

                refund_id = inv_obj.refund(cr, uid, [inv.id], date, period, description, journal_id, context=ctx)
                refund = inv_obj.browse(cr, uid, refund_id[0], context=context)

                _to_update = {
                    'date_due': date,
                    'check_total': inv.check_total
                }
                if claim and claim.partner_id:
                    _to_update.update({'partner_id': claim.partner_id.id})
                inv_obj.write(cr, uid, [refund.id], _to_update, context=context)
                inv_obj.button_compute(cr, uid, refund_id)

                created_inv.append(refund_id[0])

                if mode in ('cancel', 'modify'):
                    movelines = inv.move_id.line_id
                    to_reconcile_ids = {}
                    for line in movelines:
                        if line.account_id.id == inv.account_id.id:
                            to_reconcile_ids[line.account_id.id] = [line.id]
                        if type(line.reconcile_id) != osv.orm.browse_null:
                            reconcile_obj.unlink(cr, uid, line.reconcile_id.id)
                    wf_service.trg_validate(uid, 'account.invoice',
                                        refund.id, 'invoice_open', cr)
                    refund = inv_obj.browse(cr, uid, refund_id[0], context=context)
                    for tmpline in refund.move_id.line_id:
                        if tmpline.account_id.id == inv.account_id.id:
                            to_reconcile_ids[tmpline.account_id.id].append(tmpline.id)
                    for account in to_reconcile_ids:
                        account_m_line_obj.reconcile(
                            cr, uid, to_reconcile_ids[account],
                            writeoff_period_id=period,
                            writeoff_journal_id=inv.journal_id.id,
                            writeoff_acc_id=inv.account_id.id
                        )
                    if mode == 'modify':
                        invoice = inv_obj.read(cr, uid, [inv.id],
                                    ['name', 'type', 'number', 'reference',
                                    'comment', 'date_due', 'partner_id',
                                    'partner_insite', 'partner_contact',
                                    'partner_ref', 'payment_term', 'account_id',
                                    'currency_id', 'invoice_line', 'tax_line',
                                    'journal_id', 'period_id'], context=context)
                        invoice = invoice[0]
                        del invoice['id']
                        invoice_lines = inv_line_obj.browse(cr, uid, invoice['invoice_line'], context=context)
                        invoice_lines = inv_obj._refund_cleanup_lines(cr, uid, invoice_lines, context=context)
                        tax_lines = inv_tax_obj.browse(cr, uid, invoice['tax_line'], context=context)
                        tax_lines = inv_obj._refund_cleanup_lines(cr, uid, tax_lines, context=context)
                        invoice.update({
                            'type': inv.type,
                            'date_invoice': date,
                            'state': 'draft',
                            'number': False,
                            'invoice_line': invoice_lines,
                            'tax_line': tax_lines,
                            'period_id': period,
                            'name': description
                        })
                        for field in ('partner_id', 'account_id', 'currency_id', 'payment_term', 'journal_id'):
                                invoice[field] = invoice[field] and invoice[field][0]
                        inv_id = inv_obj.create(cr, uid, invoice, {})
                        if inv.payment_term.id:
                            data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], inv.payment_term.id, date)
                            if 'value' in data and data['value']:
                                inv_obj.write(cr, uid, [inv_id], data['value'])
                        created_inv.append(inv_id)

                # Create entry for refund invoices
                _inv_list = []
                if refund:
                    _val = {
                        'invoice_id': inv.id,
                        'invoice_refund_id': refund.id,
                        'refund_type': mode,
                        'partner_id': refund.partner_id.id,
                        'number': refund.number,
                        'amount_untaxed': refund.amount_untaxed,
                        'date_invoice': refund.date_invoice,
                    }
                    inv_ref_inv_id = inv_ref_inv_obj.create(cr, uid, _val, context=context)
                    _inv_list.append((4, inv_ref_inv_id))

                if inv_id:
                    _mod_inv = inv_obj.browse(cr, uid, inv_id, context=context)
                    _val = {
                        'invoice_id': inv.id,
                        'invoice_refund_id': _mod_inv.id,
                        'refund_type': mode,
                        'partner_id': _mod_inv.partner_id.id,
                        'number': _mod_inv.number,
                        'amount_untaxed': _mod_inv.amount_untaxed,
                        'date_invoice': _mod_inv.date_invoice,
                    }
                    inv_ref_inv_id = inv_ref_inv_obj.create(cr, uid, _val, context=context)
                    _inv_list.append((4, inv_ref_inv_id))
                inv_obj.write(cr, uid, [inv.id], {'refund_invoices': _inv_list}, context=context)
            if not inv:
                raise orm.except_orm(
                    _('Error'),
                    _('Please add invoice(s)!')
                )
            xml_id = (inv.type == 'out_refund') and 'action_invoice_tree1' or \
                     (inv.type == 'in_refund') and 'action_invoice_tree2' or \
                     (inv.type == 'out_invoice') and 'action_invoice_tree3' or \
                     (inv.type == 'in_invoice') and 'action_invoice_tree4'
            result = mod_obj.get_object_reference(cr, uid, 'account', xml_id)
            id = result and result[1] or False

            result = act_obj.read(cr, uid, id, context=context)
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain

            return result

    def invoice_refund_line(self, cr, uid, ids, context=None):
        data_refund = self.read(cr, uid, ids, ['filter_refund'], context=context)[0]['filter_refund']
        return self.compute_refund_line(cr, uid, ids, data_refund, context=context)
