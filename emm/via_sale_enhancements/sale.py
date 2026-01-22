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

logger = logging.getLogger(__name__)


class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _invoiced(self, cursor, user, ids, name, arg, context=None):
        """
        This method overrides the original one written in sale/sale.py basing the calculation of
        whether an SO is invoiced or not on the portion of SO's amount_untaxed that has been
        consumed by the SO's confirmed (not draft or cancelled) invoices' amount_untaxed.
        """
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            _invoiced_amount = 0.0
            for invoice in sale.invoice_ids:
                if invoice.state not in ('draft', 'cancel'):
                    _invoiced_amount += invoice.amount_total
            res[sale.id] = (_invoiced_amount == sale.amount_total)
        return res

    def _invoiced_search(self, cursor, user, obj, name, args, context=None):
        """
        This method called the super method.  It need to be overridden as the invoiced
        field definition is overridden
        """
        return super(sale_order, self)._invoiced_search(cursor, user, obj, name, args, context=None)

    _columns = {
        'validity': fields.date('Valid Through', help="Date when the validity of quotation expires."),
        'invoiced': fields.function(_invoiced, method=True, string='Paid',
            fnct_search=_invoiced_search, type='boolean', help="It indicates that an invoice has been paid."),
        'sale_info': fields.one2many('sale.info', 'sale_order_id', 'Sales Order Info'),
    }

    def _get_param_value(self, cr, uid, ids, param_name, context=None):
        if isinstance(ids, (list, tuple, dict, )):
            select = list(ids)
        else:
            select = [ids]

        val_obj = self.pool.get('sale.info')
        res = {}
        for so_id in select:
            _dom = [('sale_order_id', '=', so_id), ('so_parameter', '=', param_name)]
            val_rec_id = val_obj.search(cr, uid, _dom, context=context)
            _val = val_rec_id and val_obj.browse(cr, uid, val_rec_id[0], context=context) or False
            _val = _val and _val.value or ''
            res[so_id] = _val

        if isinstance(ids, (int, long, )) or (len(ids) == 1):
            res = res[ids[0]]

        return res

sale_order()
