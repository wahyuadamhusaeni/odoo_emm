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
from tools.translate import _


class account_invoice(orm.Model):
    _inherit = "account.invoice"

    def _refund_cleanup_lines(self, cr, uid, lines, context=None):
        rv = super(account_invoice, self)._refund_cleanup_lines(cr, uid, lines, context=context)

        for line in rv:
            for field in ['taxform_id']:
                if field in line[2]:
                    del line[2][field]
        return rv

    _columns = {
        'invoice_taxform_ids': fields.one2many('account.invoice.tax', 'invoice_id', 'Tax Forms'),
    }

account_invoice()


class account_invoice_tax(orm.Model):
    _inherit = 'account.invoice.tax'

    _columns = {
        'invoice_type': fields.related('invoice_id', 'type', string='Invoice Type', type='char', readonly=True, store=False),
        'invoice_state': fields.related('invoice_id', 'state', string='Invoice State', type='char', readonly=True, store=False),
        'taxform_id': fields.many2one(string='Taxform', obj='account.taxform'),
    }

    def create_taxform(self, cr, uid, ids, context=None):
        res = {}
        if not context:
            context = {}
        if isinstance(ids, (list, tuple, dict, )):
            select = list(ids)
        else:
            select = [ids]

        _taxform_pool = self.pool.get('account.taxform')
        _model = 'account.invoice.tax'
        for _obj in self.pool.get(_model).browse(cr, uid, select, context=context):
            _tax_inv = _obj.invoice_id or False
            if not _tax_inv:
                # No Invoice
                res[_obj.id] = False
                if isinstance(ids, (int, long, )) or (len(ids) == 1):
                    raise orm.except_orm(_('Error!'), _("No Invoice is specified"))
            elif _tax_inv.state not in ('open', 'paid'):
                # Invoice is not in 'open' or 'paid' state, so don't create taxform
                res[_obj.id] = False
                if isinstance(ids, (int, long, )) or (len(ids) == 1):
                    raise orm.except_orm(_('Error!'), _("Invoice %s is not in 'open' or 'paid' state.") % (_obj.internal_number))
            elif _tax_inv.type in ('out_refund', 'in_invoice'):
                # Taxform cannot be generated for customer refund or supplier invoice
                res[_obj.id] = False
                if isinstance(ids, (int, long, )) or (len(ids) == 1):
                    raise orm.except_orm(_('Error!'), _('Taxform cannot be generated for customer refund or supplier invoice.'))
            elif _obj.taxform_id:
                if _obj.taxform_id.state in ['printed', 'draft']:
                    # The tax has already had printed or draft taxform created, just return it
                    res[_obj.id] = _obj.taxform_id.id
                    if isinstance(ids, (int, long, )) or (len(ids) == 1):
                        raise orm.except_orm(_('Warning!'), _('Taxform has been generated for invoice %s.') % (_obj.internal_number))
            else:
                _val = {'invoice_tax_id': _obj.id, 'invoice_id': _tax_inv.id, }
                _taxform_id = _taxform_pool.create(cr, uid, _val, context=context)
                _obj.write({'taxform_id': _taxform_id})
                res[_obj.id] = _taxform_id

        return isinstance(ids, (int, long, )) and res[ids] or res

    def view_taxform(self, cr, uid, ids, context=None):
        if not ids:
            return []
        # This method assumes that only 1 tax line's taxform is to be displayed at any time
        _obj = self.browse(cr, uid, ids[0], context=context)
        return {
            'name': _("Account Taxform"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.taxform',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'res_id': _obj.taxform_id.id,
        }

account_invoice_tax()
