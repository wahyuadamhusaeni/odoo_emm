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
import openerp.addons.decimal_precision as dp


class sale_order(orm.Model):
    _inherit = 'sale.order'

    def get_amt(self, cr, uid, ids, name, arg, context=None):
        res = {}

        for obj in self.browse(cr, uid, ids, context=context):
            amount_total = obj.amount_total
            invoiced_amt = 0.0
            paid_amt = 0.0
            for invoice in obj.invoice_ids:
                if invoice.state in ['open', 'paid']:
                    _factor = invoice.type in ('out_invoice', 'in_invoice') and 1 or -1
                    paid_amt += _factor * (invoice.amount_total - invoice.residual)
                    invoiced_amt += _factor * invoice.amount_total
            to_invoiced_amt = amount_total - invoiced_amt
            to_pay = amount_total - paid_amt
            res[obj.id] = {
                'total_amt': obj.amount_total,
                'invoiced_amt': invoiced_amt,
                'to_invoiced_amt': to_invoiced_amt,
                'paid_amt': paid_amt,
                'to_pay_amt': to_pay,
            }
        return res

    _columns = {
        'total_amt': fields.function(get_amt, digits_compute=dp.get_precision('Account'), string='Total', multi='all', help="The total amount."),
        'invoiced_amt': fields.function(get_amt, string='Amount Invoiced', method=True, type='float', digits_compute=dp.get_precision('Account'), multi='all', readonly=True),
        'to_invoiced_amt': fields.function(get_amt, string='Amount To Invoice', method=True, type='float', digits_compute=dp.get_precision('Account'), multi='all', readonly=True),
        'paid_amt': fields.function(get_amt, string='Amount Paid', method=True, type='float', digits_compute=dp.get_precision('Account'), multi='all', readonly=True),
        'to_pay_amt': fields.function(get_amt, string='Amount To Be Paid', method=True, type='float', digits_compute=dp.get_precision('Account'), multi='all', readonly=True),
        'so_tracking_by_quantity': fields.one2many('sale.tracking.by.quantity', 'order_id', 'SO Tracking by Quantity', readonly=True),
    }

    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(sale_order, self).copy_data(cr, uid, id, default=default, context=context)
        res.pop('so_tracking_by_quantity', None)
        return res

sale_order()
