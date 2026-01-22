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

from osv import fields, orm
from datetime import date
from openerp.tools.translate import _


class service_invoice(orm.TransientModel):
    _name = 'service.invoice'
    _description = 'Service Invoices'

    _columns = {
        'sr_id': fields.integer('SR ID'),
        'stock_move_ids': fields.many2many('stock.move', 'service_invoice_stock_move_rel', 'service_invoice_id', 'stock_move_id', 'Spare Parts Consumed IDs'),
        'stock_move': fields.many2many('stock.move', 'service_invoice_stock_move_rel', 'service_invoice_id', 'stock_move_id', 'Spare Parts Consumed'),
        'service_fee': fields.many2many('service.fee', 'service_invoice_service_fee_rel', 'service_invoice_id', 'service_fee_id', 'Service Executed'),
    }

    def create_service_invoice(self, cr, uid, ids, context=None):
        sr_obj = self.pool.get('service.request').browse(cr, uid, context.get('active_id'), context=context)
        # value = self.pool.get('account.invoice').onchange_partner_id(cr, uid, ids, 'out_invoice', sr_obj.partner.id)
        vals = {
            'partner_id': sr_obj.partner.id,
            'account_id': sr_obj.partner.property_account_receivable.id,
            'payment_term': sr_obj.partner.property_payment_term and sr_obj.partner.property_payment_term.id or False,
            'origin': sr_obj.name,
            'date_invoice': date.today(),
        }

        if sr_obj.partner.property_payment_term and sr_obj.partner.property_payment_term.id or False:
                pterm_list = self.pool.get('account.payment.term').compute(cr, uid, sr_obj.partner.property_payment_term.id, value=1, date_ref=str(date.today()))
                if pterm_list:
                    pterm_list = [line[0] for line in pterm_list]
                    pterm_list.sort()
                    vals.update({'date_due': pterm_list[-1]})
                else:
                    raise orm.except_orm(_('Insufficient Data!'), _('The payment term of supplier does not have a payment term line.'))

        res = self.pool.get('account.invoice').create(cr, uid, vals, context=context)
        # date_due = self.pool.get('account.invoice').onchange_payment_term_date_invoice(cr, uid, res, value.get('value').get('payment_term'), date.today().strftime('%Y-%m-%d'))
        # if date_due:
            # self.pool.get('account.invoice').write(cr, uid, res, {'date_due': date_due.get('value').get('date_due'), }, context=context)
        for stock_move in context.get('stock_move')[0][2]:
            product = self.pool.get('stock.move').browse(cr, uid, stock_move, context=context).product_id
            qty = self.pool.get('stock.move').browse(cr, uid, stock_move, context=context).product_qty
            uom_id = self.pool.get('stock.move').browse(cr, uid, stock_move, context=context).product_uom
            line_value = self.pool.get('account.invoice.line').product_id_change(cr, uid, ids, product.id, uom_id.id, qty, '', 'out_invoice', sr_obj.partner.id)
            line_value = line_value.get('value')
            line_vals = {
                'product_id': product.id,
                'uos_id': line_value.get('uos_id'),
                'account_id': line_value.get('account_id'),
                'price_unit': line_value.get('price_unit'),
                'invoice_line_tax_id': [(6, 0, line_value.get('invoice_line_tax_id'))],
                'cost_method': line_value.get('cost_method'),
                'name': line_value.get('name'),
                'quantity': qty,
            }

            if self.pool.get('stock.move').browse(cr, uid, stock_move, context=context).zero_price:
                line_vals.update({'price_unit': 0})

            line_id = self.pool.get('account.invoice.line').create(cr, uid, line_vals, context=context)
            self.pool.get('account.invoice').write(cr, uid, res, {'invoice_line': [(4, line_id)]}, context=context)
            self.pool.get('stock.move').write(cr, uid, stock_move, {'has_invoiced': True}, context=context)

            #change the value of related service invoice line field has_invoiced to True
            model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'stock.move')], context=context)[0]
            service_invoice_line_ids = self.pool.get('service.invoice.line').search(cr, uid, [('model','=',model),('document_id','=',stock_move)], context=context)
            self.pool.get('service.invoice.line').write(cr, uid, service_invoice_line_ids, {'has_invoiced': True}, context=context)

        for service_fee in context.get('service_fee')[0][2]:
            product = self.pool.get('service.fee').browse(cr, uid, service_fee, context=context).service_id
            qty = self.pool.get('service.fee').browse(cr, uid, service_fee, context=context).service_qty
            uom_id = self.pool.get('service.fee').browse(cr, uid, service_fee, context=context).service_uom
            line_value = self.pool.get('account.invoice.line').product_id_change(cr, uid, ids, product.id, uom_id.id, qty, '', 'out_invoice', sr_obj.partner.id)
            line_value = line_value.get('value')
            line_vals = {
                'product_id': product.id,
                'uos_id': line_value.get('uos_id'),
                'account_id': line_value.get('account_id'),
                'price_unit': line_value.get('price_unit'),
                'invoice_line_tax_id': [(6, 0, line_value.get('invoice_line_tax_id'))],
                'cost_method': line_value.get('cost_method'),
                'name': line_value.get('name'),
                'quantity': qty,
            }

            if self.pool.get('service.fee').browse(cr, uid, service_fee, context=context).zero_price:
                line_vals.update({'price_unit': 0})

            line_id = self.pool.get('account.invoice.line').create(cr, uid, line_vals, context=context)
            self.pool.get('account.invoice').write(cr, uid, res, {'invoice_line': [(4, line_id)]}, context=context)
            self.pool.get('service.fee').write(cr, uid, service_fee, {'has_invoiced': True}, context=context)

            #change the value of related service invoice line field has_invoiced to True
            model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'service.fee')], context=context)[0]
            service_invoice_line_ids = self.pool.get('service.invoice.line').search(cr, uid, [('model','=',model),('document_id','=',service_fee)], context=context)
            self.pool.get('service.invoice.line').write(cr, uid, service_invoice_line_ids, {'has_invoiced': True}, context=context)

        self.pool.get('service.request').write(cr, uid, [context.get('active_id')], {'service_invoice': [(4, res)]}, context=context)
        return res

service_invoice()


class service_invoice_line(orm.Model):
    _name = 'service.invoice.line'
    _description = 'Service Invoice Line'

    _columns = {
        'product_id': fields.many2one('product.product', 'Product'),
        'uos_id': fields.many2one('product.uom', 'Unit of Measure'),
        'account_id': fields.many2one('account.account', 'Account'),
        'price_unit': fields.float('Unit Price'),
        'invoice_line_tax_id': fields.many2many('account.tax', 'service_invoice_line_account_tax_rel', 'service_invoice_line_id', 'account_tax_id', 'Taxes'),
        'cost_method': fields.selection([('standard', 'Standard Price'), ('average', 'Average Price'), ('fifo', 'Lot: FIFO'), ('lifo', 'Lot: LIFO'), ('lot_based', 'Lot Based')], 'Costing Method'),
        'name': fields.text('Description'),
        'quantity': fields.float('Quantity'),
        'total': fields.float('Total'),
        'zero_price': fields.boolean('Free Change'),
        'has_invoiced': fields.boolean('Has Invoiced'),
        'origin': fields.char('Origin'),
        'model': fields.many2one('ir.model', 'Model'),
        'document_id': fields.integer('Document Id'),
    }

    _defaults = {
        'has_invoiced': False,
    }

    def make_invoices(self, cr, uid, ids, context=None):
        temp = []
        active_ids = []

        if context.get('active_ids'):
            active_ids = context.get('active_ids')
        else:
            active_ids = ids

        for active_id in active_ids:
            obj = self.pool.get('service.invoice.line').browse(cr, uid, active_id, context=context)
            if obj.origin not in temp:
                temp.append(obj.origin)

        for origin in temp:
            sr_id = self.pool.get('service.request').search(cr, uid, [('name', '=', origin)], context=context)
            sr_obj = self.pool.get('service.request').browse(cr, uid, sr_id[0], context=context)
            # value = self.pool.get('account.invoice').onchange_partner_id(cr, uid, 1, 'out_invoice', sr_obj.partner.id)
            # date_due = self.pool.get('account.invoice').onchange_payment_term_date_invoice(cr, uid, active_ids, value.get('value').get('payment_term'), date.today().strftime('%Y-%m-%d'))
            vals = {
                'partner_id': sr_obj.partner.id,
                'account_id': sr_obj.partner.property_account_receivable.id,
                'payment_term': sr_obj.partner.property_payment_term and sr_obj.partner.property_payment_term.id or False,
                'origin': sr_obj.name,
                'date_invoice': date.today(),
            }

            if sr_obj.partner.property_payment_term and sr_obj.partner.property_payment_term.id or False:
                pterm_list = self.pool.get('account.payment.term').compute(cr, uid, sr_obj.partner.property_payment_term.id, value=1, date_ref=str(date.today()))
                if pterm_list:
                    pterm_list = [line[0] for line in pterm_list]
                    pterm_list.sort()
                    vals.update({'date_due': pterm_list[-1]})
                else:
                    raise orm.except_orm(_('Insufficient Data!'), _('The payment term of supplier does not have a payment term line.'))

            res = self.pool.get('account.invoice').create(cr, uid, vals, context=context)
            self.pool.get('service.request').write(cr, uid, sr_obj.id, {'service_invoice': [(4, res)]}, context=context)

            service_invoice_line_ids = self.pool.get('service.invoice.line').search(cr, uid, [('origin', '=', origin), ('id', 'in', active_ids)], context=context)
            for service_invoice_line in self.pool.get('service.invoice.line').browse(cr, uid, service_invoice_line_ids, context=context):
                product = service_invoice_line.product_id.id
                qty = service_invoice_line.quantity
                uom_id = self.pool.get('product.product').browse(cr, uid, product, context=context).uom_id.id
                line_value = self.pool.get('account.invoice.line').product_id_change(cr, uid, active_ids, product, uom_id, qty, '', 'out_invoice', sr_obj.partner.id)
                line_value = line_value.get('value')
                line_vals = {
                    'product_id': product,
                    'uos_id': line_value.get('uos_id'),
                    'account_id': line_value.get('account_id'),
                    'price_unit': line_value.get('price_unit'),
                    'invoice_line_tax_id': [(6, 0, line_value.get('invoice_line_tax_id'))],
                    'cost_method': line_value.get('cost_method'),
                    'name': line_value.get('name'),
                    'quantity': qty,
                }

                if service_invoice_line.zero_price:
                    line_vals.update({'price_unit': 0})

                line_id = self.pool.get('account.invoice.line').create(cr, uid, line_vals, context=context)
                self.pool.get('account.invoice').write(cr, uid, res, {'invoice_line': [(4, line_id)]}, context=context)
                model = self.pool.get('ir.model').browse(cr, uid, service_invoice_line.model.id, context=context).model
                self.pool.get('service.invoice.line').write(cr, uid, service_invoice_line.id, {'has_invoiced': True}, context=context)
                self.pool.get(model).write(cr, uid, service_invoice_line.document_id, {'has_invoiced': True}, context=context)
        return res

service_invoice_line()
