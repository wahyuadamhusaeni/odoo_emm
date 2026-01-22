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

from openerp.osv import orm
from openerp import netsvc
from openerp.tools.translate import _


class sale_order(orm.Model):
    _inherit = "sale.order"

    def test_state(self, cr, uid, ids, mode, *args):
        assert mode in ('finished', 'canceled'), _("invalid mode for test_state")
        finished = True
        canceled = False
        write_done_ids = []
        write_cancel_ids = []
        for order in self.browse(cr, uid, ids, context={}):
            for line in order.order_line:
                move_ids = self.pool.get('stock.move').search(cr, uid, [('sale_line_id', '=', line.id)], context={})
                temp = [move.state for move in self.pool.get('stock.move').browse(cr, uid, move_ids, context={})]
                if all(state == 'done' for state in temp):
                    if line.state != 'done':
                        write_done_ids.append(line.id)
                    else:
                        True
                elif not all(state == 'done' for state in temp):
                    finished = False
                if 'cancel' in temp:
                    canceled = True
                    if line.state != 'exception':
                        write_cancel_ids.append(line.id)

        if write_done_ids:
            self.pool.get('sale.order.line').write(cr, uid, write_done_ids, {'state': 'done'})
        if write_cancel_ids:
            self.pool.get('sale.order.line').write(cr, uid, write_cancel_ids, {'state': 'exception'})

        if mode == 'finished':
            return finished
        elif mode == 'canceled':
            return canceled

    def check_shipped_paid(self, cr, uid, ids, context=None):
        check = []
        for sale in self.browse(cr, uid, ids, context=context):
            picking_ids = self.pool.get('stock.picking').search(cr, uid, [('sale_id', '=', sale.id), ('type', '=', 'out')], context=context)
            for picking in self.pool.get('stock.picking').browse(cr, uid, picking_ids, context=context):
                if picking.state == 'done' and picking.invoice_state == 'invoiced':
                    for invoice in sale.invoice_ids:
                        if invoice.state in ['paid', 'cancel']:
                            check.append(True)
                        else:
                            check.append(False)
                elif picking.state == 'done' and picking.invoice_state == 'none':
                    check.append(True)
                elif picking.state == 'cancel':
                    check.append(True)
                else:
                    check.append(False)

        if check:
            result = True
            for boolean in check:
                result = result and boolean
        else:
            result = False

        return result

    def action_ship_end(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_ship_end(cr, uid, ids, context=context)
        cr.execute('SELECT order_id '
                   'FROM sale_order_invoice_rel '
                   'WHERE invoice_id IN %s ',
                   (tuple(ids),))
        sale_ids = [r[0] for r in cr.fetchall()]

        _wkf = netsvc.LocalService("workflow")
        for sid in sale_ids:
            _wkf.trg_write(uid, 'sale.order', sid, cr)
        return res

sale_order()
