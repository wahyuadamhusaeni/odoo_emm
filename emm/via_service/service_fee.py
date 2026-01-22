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


class service_fee_wizard(orm.TransientModel):
    _name = 'service.fee.wizard'
    _description = 'Service Fee Wizard'

    _columns = {
        'sr_id': fields.integer('SR ID'),
        'service_fee_id': fields.many2many('service.fee', 'service_fee_wizard_service_fee_rel', 'service_fee_wizard_id', 'service_fee_id', 'Service Fee'),
    }

    _defaults = {
        'sr_id': lambda self, cr, uid, context: context['service_request_id'],
    }

    #this method will get service_fee_ids and then link it with the service request document
    # def create_service_fee(self, cr, uid, ids, context=None):
    #     service_fee = context.get('service_fee_id',[])
    #     service_fee_ids = [service_fee_id[1] for service_fee_id in service_fee]
    #     for service_fee in service_fee_ids:
    #         res = self.pool.get('service.request').write(cr, uid, [context.get('active_id')], {'service_request': [(4, service_fee)]})
    #     return True

    #this method will get service_fee_ids, change the service type to 'execute' and then link it with the service request document
    def execute_service_fee(self, cr, uid, ids, context=None):
        service_fee = context.get('service_fee_id', [])
        service_fee_ids = service_fee[0][2]
        for service_fee in service_fee_ids:
            self.pool.get('service.fee').write(cr, uid, service_fee, {'service_type': 'execute'}, context=context)
            res = self.pool.get('service.request').write(cr, uid, [context.get('sr_id')], {'service_execute': [(4, service_fee)]}, context=context)

            #create service invoice line based on service fee
            service_fee_obj = self.pool.get('service.fee').browse(cr, uid, service_fee, context=context)
            service_request_obj = self.pool.get('service.request').browse(cr, uid, context.get('sr_id'))
            line_value = self.pool.get('account.invoice.line').product_id_change(cr, uid, ids, service_fee_obj.service_id.id, service_fee_obj.service_uom.id, service_fee_obj.service_qty, '', 'out_invoice', service_request_obj.partner.id)
            line_value = line_value.get('value')
            line_vals = {
                'product_id': service_fee_obj.service_id.id,
                'uos_id': line_value.get('uos_id'),
                'account_id': line_value.get('account_id'),
                'price_unit': line_value.get('price_unit'),
                'invoice_line_tax_id': [(6, 0, line_value.get('invoice_line_tax_id'))],
                'cost_method': line_value.get('cost_method'),
                'name': line_value.get('name'),
                'quantity': service_fee_obj.service_qty,
                'total': service_fee_obj.service_qty * line_value.get('price_unit'),
                'origin': service_fee_obj.sr_id.name,
                'zero_price': service_fee_obj.zero_price,
                'model': self.pool.get('ir.model').search(cr, uid, [('model', '=', 'service.fee')], context=context)[0],
                'document_id': service_fee,
                'has_invoiced': False,
            }
            if service_fee_obj.zero_price:
                line_vals.update({'price_unit': 0})
            self.pool.get('service.invoice.line').create(cr, uid, line_vals, context=context)
        return res

service_fee_wizard()


class service_fee(orm.Model):
    _name = 'service.fee'
    _description = 'Service Fee'

    #this method will get the value of product_uom and price_unit based on service_id and store it
    def create(self, cr, uid, vals, context=None):
        service = self.pool.get('product.product').browse(cr, uid, vals.get('service_id'), context=context)
        # sr_obj = self.pool.get('service.request').browse(cr, uid, context.get('active_id'))
        service_qty = vals.get('service_qty')
        vals.update({
            'service_uom': service.uom_id.id,
            'service_price': service.list_price,
            'service_total': service_qty * service.list_price,
        })
        return super(service_fee, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        for service in self.browse(cr, uid, ids, context=context):
            if vals.get('service_qty'):
                vals.update({
                    'service_total': vals.get('service_qty') * service.service_price
                    })
        return super(service_fee, self).write(cr, uid, ids, vals, context=context)

    #define the selection list
    service_fee_type = [
        ('request', 'Request'),
        ('execute', 'Execute'),
    ]

    _columns = {
        'sr_id': fields.many2one('service.request', 'Service Request', required=True),
        'service_id': fields.many2one('product.product', 'Service', required=True),
        'service_qty': fields.float('Qty', required=True),
        'service_uom': fields.many2one('product.uom', 'UOM'),
        'service_price': fields.float('Unit Price'),
        'service_type': fields.selection(service_fee_type, 'Type'),
        'has_invoiced': fields.boolean('Has Invoiced'),
        'service_total': fields.float('Total Price'),
        'zero_price': fields.boolean('Free Charge'),
        'additional': fields.boolean('Additional'),
    }

    _defaults = {
        'service_type': 'request',
        'has_invoiced': False,
        'additional': False,
    }

    #this method is called when there is any changes with 'service_id' field
    #this method will automatically fill the service_uom and service_price field based on the related service
    def onchange_service_id(self, cr, uid, ids, service_id=False, context=None):
        if not service_id:
            return {}

        service = self.pool.get('product.product').browse(cr, uid, [service_id], context=context)[0]
        result = {
            'service_uom': service.uom_id.id,
            'service_qty': 1.00,
            'service_price': service.list_price,
            'service_total': 1.00 * service.list_price,
        }
        return {'value': result}

    def onchange_service_qty(self, cr, uid, ids, service_qty=False, service_id=False, context=None):
        if not service_id:
            return {}

        service = self.pool.get('product.product').browse(cr, uid, [service_id], context=context)[0]
        result = {
            'service_total': service_qty * service.list_price,
        }
        return {'value': result}

service_fee()
