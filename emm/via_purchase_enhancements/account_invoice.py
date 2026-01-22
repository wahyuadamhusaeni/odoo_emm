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
from openerp import netsvc
from openerp import SUPERUSER_ID


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    def confirm_paid(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).confirm_paid(cr, uid, ids, context=context)
        purchase_order_obj = self.pool.get('purchase.order')
        # read access on purchase.order object is not required
        if not purchase_order_obj.check_access_rights(cr, uid, 'read', raise_exception=False):
            user_id = SUPERUSER_ID
        else:
            user_id = uid
        po_ids = purchase_order_obj.search(cr, user_id, [('invoice_ids', 'in', ids)], context=context)
        wf_service = netsvc.LocalService("workflow")
        for po_id in po_ids:
            # Signal purchase order workflow that an invoice has been validated.
            wf_service.trg_write(uid, 'purchase.order', po_id, cr)
        return res

    def invoice_validate(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
        purchase_order_obj = self.pool.get('purchase.order')
        # read access on purchase.order object is not required
        if not purchase_order_obj.check_access_rights(cr, uid, 'read', raise_exception=False):
            user_id = SUPERUSER_ID
        else:
            user_id = uid
        po_ids = purchase_order_obj.search(cr, user_id, [('invoice_ids', 'in', ids)], context=context)
        wf_service = netsvc.LocalService("workflow")
        for po_id in po_ids:
            # Signal purchase order workflow that an invoice has been validated.
            wf_service.trg_write(uid, 'purchase.order', po_id, cr)
        return res