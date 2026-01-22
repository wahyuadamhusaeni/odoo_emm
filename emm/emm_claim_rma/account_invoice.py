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
from tools.translate import _


class account_invoice(orm.Model):
    _inherit = "account.invoice"

    _columns = {
        'claim_id': fields.many2one('crm.claim', 'Claim'),
    }

    # 7.a.i. Inherit  _refund_cleanup_lines method by replacing it (copy from the original)  from
    # account/account_invoice.py.  At the beginning of for line in lines  loop add a check to see
    # if line.id is included in  context.get('claim_invoice_line', []) or not.  If not, continue  (ignore).
    def _refund_cleanup_lines(self, cr, uid, lines, context=None):
        """
        Convert records to dict of values suitable for one2many line creation

        :param list(browse_record) lines: records to convert
        :return: list of command tuple for one2many line creation [(0, 0, dict of valueis), ...]
        """
        if context is None:
            context = {}

        _ids = context.get('claim_invoice_line', [])
        _line_to_process = []
        if _ids:
            _line_to_process = [_line for _line in lines if _line.id in _ids]
        else:
            _line_to_process = lines

        return super(account_invoice, self)._refund_cleanup_lines(cr, uid, _line_to_process, context=None)

    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):

        if context is None:
            context = {}

        result = super(account_invoice, self)._prepare_refund(cr, uid, invoice,
            date=date, period_id=period_id, description=description,
            journal_id=journal_id, context=context)

        _claim_id = context.get('claim_id', False)
        if _claim_id:
            result.update({'claim_id': _claim_id})
        return result
