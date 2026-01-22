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

from osv import orm
from osv import fields
from tools.translate import _


class purchase_order(orm.Model):
    _inherit = 'purchase.order'

    def get_amount(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for purchase in self.browse(cr, uid, ids, context=context):
            amount_total = purchase.amount_total
            invoiced = 0.0
            total_credit = 0.0
            total_debit = 0.0
            for invoice in purchase.invoice_ids:
                if invoice.state in ['open', 'paid']:
                    _factor = invoice.type in ('out_invoice', 'in_invoice') and 1 or -1
                    invoiced += _factor * invoice.amount_total
                    for payment in invoice.payment_ids:
                        # Do not multiply this with _factor as the direction has been reflected in the credit/debit value
                        total_credit += payment.credit
                        total_debit += payment.debit
            res[purchase.id] = {
                'po_amount_total': purchase.amount_total,
                'amount_invoiced': invoiced,
                'amount_paid': total_debit - total_credit,
                'amount_to_invoice': amount_total - invoiced,
                'amount_to_pay': amount_total - (total_debit - total_credit),
            }
        return res

    _columns = {
        # For Purchase Order Summary
        'po_summary': fields.one2many('purchase.order.summary', 'purchase_id', 'Purchase Order Quantity', readonly=True),
        'po_amount_total': fields.function(get_amount, string='Amount Total', method=True, type='float', multi='summary', readonly=True, help="This is Amount Total"),
        'amount_to_invoice': fields.function(get_amount, string='Amount To Be Invoiced', method=True, type='float', multi='summary', readonly=True, help="This is Amount Total - Amount Invoiced"),
        'amount_invoiced': fields.function(get_amount, string='Amount Invoiced', method=True, type='float', multi='summary', readonly=True, help="This is the Total of all Invoices that are in Done or Paid status"),
        'amount_to_pay': fields.function(get_amount, string='Amount To Pay', method=True, type='float', multi='summary', readonly=True, help="This is Amount Total - Amount Paid"),
        'amount_paid': fields.function(get_amount, string='Amount Paid', method=True, type='float', multi='summary', readonly=True, help="This is the Total of all Debit - Credit of all Payments of all Invoices that are in Done or Paid status"),
    }

    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(purchase_order, self).copy_data(cr, uid, id, default=default, context=context)
        res.pop('po_summary', None)
        return res
