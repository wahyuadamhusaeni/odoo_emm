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

from osv import osv, fields
import logging

logger = logging.getLogger('via_payment_management')


class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _open_invoices(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            _open_invoices = filter(lambda x: 'open' == x.state, sale.invoice_ids)
            res[sale.id] = len(_open_invoices)

        logger.debug('Return value %s' % str(res))
        return res

    _columns = {
        'open_invoices': fields.function(_open_invoices, string='Open Invoices', type='integer'),
    }

    def action_assign_payment(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        ctx = context.copy()
        ctx['active_ids'] = ids
        ctx['active_id'] = ids[0]
        ctx['active_model'] = self._name
        ctx['order_id'] = ids[0]
        _wiz_pool = self.pool.get("via.assign.payment")
        _wiz_id = _wiz_pool.create(cr, uid, {}, context=ctx)
        _wiz_obj = _wiz_pool.browse(cr, uid, _wiz_id, context=ctx)
        return _wiz_obj.open_page(context=ctx)

sale_order()
