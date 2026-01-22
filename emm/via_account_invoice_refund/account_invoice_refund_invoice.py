# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
#    Copyright (c) 2011 - 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

import netsvc
from osv import fields, osv
from tools.translate import _


class account_invoice_refund_invoice(osv.osv):
    _name = "account.invoice.refund.invoice"
    _description = "Account Invoice Refund Invoice"
    logger = netsvc.Logger()

    def _get_refund_types(self, cr, uid, context=None):
        _pool = self.pool.get('account.invoice.refund')
        return _pool and _pool._columns['filter_refund'] and _pool._columns['filter_refund'].selection or []

    _columns = {
        'invoice_id': fields.many2one('account.invoice', 'Invoice ID'),
        'invoice_refund_id': fields.many2one('account.invoice', 'Refund Invoice'),
        'refund_type': fields.selection(_get_refund_types, 'Refund Type'),
        'partner_id': fields.related('invoice_refund_id', 'partner_id', type='many2one', relation='res.partner', readonly=True, string='Partner'),
        'date_invoice': fields.related('invoice_refund_id', 'date_invoice', type='date', readonly=True, string='Date'),
        'number': fields.related('invoice_refund_id', 'number', type='char', size=64, string='Number', readonly=True),
        'amount_untaxed': fields.related('invoice_refund_id', 'amount_untaxed', type='float', relation='account.invoice', string='Total', readonly=True),
    }

account_invoice_refund_invoice()
