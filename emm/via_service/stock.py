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
from datetime import datetime
import time
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp import netsvc


class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    # This method will called code.decode and then return the selection inside the related category (stock_picking_svc_type)
    def _get_selection(self, cr, uid, context=None):
        res = self.pool.get('code.decode').get_selection_for_category(cr, uid, 'via_service', 'stock_picking_svc_type', context=None)
        return res

    _columns = {
        'service_id': fields.many2one('service.request', 'service_id'),
        'picking_svc_type': fields.selection(_get_selection, 'Type'),
        'user_pickup_spare_part': fields.many2one('hr.employee', 'User Pickup for Spare Parts Wizard'),
        'service_request_planning': fields.many2many('service.request', 'service_request_stock_picking_rel', 'stock_picking_id', 'service_request_id', 'Service Request'),
    }

    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(stock_picking, self).copy_data(cr, uid, id, default=default, context=context)
        # res.pop('service_request_planning')
        return res

    def print_pickup_return(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()

        for _picking in self.browse(cr, uid, ids, context=context):
            try:
                if _picking.picking_svc_type == 'pickup':
                    _template = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'pickup_sparepart_form_template', context=context)
                else:
                    _template = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'return_sparepart_form_template', context=context)

                _template = _template and _template.act_report_id and self.pool.get('ir.actions.report.xml').copy_data(cr, uid, _template.act_report_id.id, context=context) or False

                _datas = {
                    'ids': [_picking.id],
                }
                _template.update({'datas': _datas, 'context': ctx})
                return _template
            except:
                raise orm.except_orm(_('Error !'), _('Cannot load form. Please contact your administrator'))

    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        res = super(stock_picking, self).do_partial(cr, uid, ids, partial_datas=partial_datas, context=context)

        delivered_picking = res.get(ids[0]).get('delivered_picking', False)
        if delivered_picking:
            temp = self.browse(cr, uid, delivered_picking, context=context)
            picking = temp.id
            if temp.backorder_id:
                picking = temp.backorder_id.id

            obj_picking = self.browse(cr, uid, picking, context=context)

            if obj_picking.service_id and obj_picking.type == 'out':
                move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','=',obj_picking.id)], context=context)
                for move in self.pool.get('stock.move').browse(cr, uid, move_ids, context=context):
                    service_request_obj = self.pool.get('service.request').browse(cr, uid, obj_picking.service_id.id, context=context)
                    line_value = self.pool.get('account.invoice.line').product_id_change(cr, uid, ids, move.product_id.id, move.product_uom.id, move.product_qty, '', 'out_invoice', service_request_obj.partner.id)
                    line_value = line_value.get('value')

                    line_vals = {
                        'product_id': move.product_id.id,
                        'uos_id': move.product_uos.id,
                        'account_id': line_value.get('account_id'),
                        'price_unit': line_value.get('price_unit'),
                        'invoice_line_tax_id': [(6, 0, line_value.get('invoice_line_tax_id'))],
                        'cost_method': line_value.get('cost_method'),
                        'name': line_value.get('name'),
                        'quantity': move.product_qty,
                        'total': move.product_qty * line_value.get('price_unit'),
                        'origin': move.origin,
                        'zero_price': move.zero_price,
                        'model': self.pool.get('ir.model').search(cr, uid, [('model', '=', 'stock.move')], context=context)[0],
                        'document_id': move.id,
                        'has_invoiced': False,
                    }
                    if move.zero_price:
                        line_vals.update({'price_unit': 0})
                    self.pool.get('service.invoice.line').create(cr, uid, line_vals, context=context)

        return res

stock_picking()


class stock_picking_out(orm.Model):
    _inherit = 'stock.picking.out'

    #this method will called code.decode and then return the selection inside the related category (stock_picking_svc_type)
    def _get_selection(self, cr, uid, context=None):
        res = self.pool.get('code.decode').get_selection_for_category(cr, uid, 'via_service', 'stock_picking_svc_type', context=None)
        return res

    _columns = {
        'service_id': fields.many2one('service.request', 'service_id'),
        'picking_svc_type': fields.selection(_get_selection, 'Type'),
        'user_pickup_spare_part': fields.many2one('hr.employee', 'User Pickup for Spare Parts Wizard'),
        'service_request_planning': fields.many2many('service.request', 'service_request_stock_picking_rel', 'stock_picking_id', 'service_request_id', 'Service Request'),
    }

    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(stock_picking_out, self).copy_data(cr, uid, id, default=default, context=context)
        # res.pop('service_request_planning')
        return res

stock_picking_out()


class stock_picking_in(orm.Model):
    _inherit = 'stock.picking.in'

    _columns = {
        'service_id': fields.many2one('service.request', 'service_id'),
        'user_pickup_spare_part': fields.many2one('hr.employee', 'User Pickup for Spare Parts Wizard'),
        'service_request_planning': fields.many2many('service.request', 'service_request_stock_picking_rel', 'stock_picking_id', 'service_request_id', 'Service Request'),
    }

    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(stock_picking_in, self).copy_data(cr, uid, id, default=default, context=context)
        # res.pop('service_request_planning')
        return res

stock_picking_in()


class stock_location(orm.Model):
    _inherit = 'stock.location'

    # This method will called code.decode and then return the selection inside the related category (stock_location_area_type)
    def _get_selection(self, cr, uid, context=None):
        res = self.pool.get('code.decode').get_selection_for_category(cr, uid, 'via_service', 'stock_location_area_type', context=None)
        return res

    _columns = {
        'usage_type': fields.selection(_get_selection, 'Location Area Type'),
    }

stock_location()


class stock_move(orm.Model):
    _inherit = 'stock.move'

    _columns = {
        'has_invoiced': fields.boolean('Has Invoiced'),
        'total_price': fields.float('Total Price'),
        'zero_price': fields.boolean('Free Charge'),
    }

    _defaults = {
        'has_invoiced': False,
    }

    #this method will update the value inside vals before stock move is being created
    def create(self, cr, uid, vals, context=None):
        if context is not None:
            if context.get('active_model', '') == 'service.request':
                product = self.pool.get('product.product').browse(cr, uid, vals.get('product_id'), context=context)
                vals.update({
                    'product_uom': product.uom_id.id,
                    'price_unit': product.list_price,
                })
        return super(stock_move, self).create(cr, uid, vals, context=context)

stock_move()


class stock_move_wizard(orm.TransientModel):
    _name = 'stock.move.wizard'
    _description = 'Stock Move Wizard'

    def create(self, cr, uid, vals, context=None):
        product = self.pool.get('product.product').browse(cr, uid, vals.get('product_id'), context=context)
        uos_id = product.uos_id and product.uos_id.id or False
        vals.update({
            'product_uom': product.uom_id.id,
            'product_uos': uos_id,
            'price_unit': product.list_price,
            'total_price': vals.get('product_qty') * product.list_price,
        })
        return super(stock_move_wizard, self).create(cr, uid, vals, context=context)

    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,
                            loc_dest_id=False, partner_id=False, context=None):
        """ On change of product id, if finds UoM, UoS, quantity and UoS quantity.
        @param prod_id: Changed Product id
        @param loc_id: Source location id
        @param loc_dest_id: Destination location id
        @param partner_id: Address id of partner
        @return: Dictionary of values
        """
        if not prod_id:
            return {}
        lang = False
        if partner_id:
            addr_rec = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            if addr_rec:
                lang = addr_rec and addr_rec.lang or False
        ctx = {'lang': lang}

        product = self.pool.get('product.product').browse(cr, uid, [prod_id], context=ctx)[0]
        uos_id = product.uos_id and product.uos_id.id or False
        result = {
            'product_uom': product.uom_id.id,
            'product_uos': uos_id,
            'product_qty': 1.00,
            'product_uos_qty': self.pool.get('stock.move').onchange_quantity(cr, uid, ids, prod_id, 1.00, product.uom_id.id, uos_id)['value']['product_uos_qty'],
            'prodlot_id': False,
            'price_unit': product.list_price,
            'total_price': 1.00 * product.list_price,
        }
        if not ids:
            result['name'] = product.partner_ref
        if loc_id:
            result['location_id'] = loc_id
        if loc_dest_id:
            result['location_dest_id'] = loc_dest_id
        return {'value': result}

    def onchange_product_qty(self, cr, uid, ids, product_qty, product_id, context=None):
        result = {}
        if product_id:
            product_price = self.pool.get('product.product').browse(cr, uid, product_id, context=context).list_price
            result = {
                'total_price': product_qty * product_price,
            }
        return {'value': result}

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True, select=True, domain=[('type', '<>', 'service')], states={'done': [('readonly', True)]}),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True, states={'done': [('readonly', True)]}),
        'state': fields.selection([('draft', 'New'),
                                   ('cancel', 'Cancelled'),
                                   ('waiting', 'Waiting Another Move'),
                                   ('confirmed', 'Waiting Availability'),
                                   ('assigned', 'Available'),
                                   ('done', 'Done'),
                                   ], 'Status', readonly=True, select=True,
                 help="* New: When the stock move is created and not yet confirmed.\n"
                      "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"
                      "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to me manufactured...\n"
                      "* Available: When products are reserved, it is set to \'Available\'.\n"
                      "* Done: When the shipment is processed, the state is \'Done\'."),
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial Number', states={'done': [('readonly', True)]}, help="Serial number is used to put a serial number on the production", select=True),
        'location_id': fields.many2one('stock.location', 'Source Location', required=True, select=True, states={'done': [('readonly', True)]}, help="Sets a location if you produe at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
        'location_dest_id': fields.many2one('stock.location', 'Destination Location', required=True, states={'done': [('readonly', True)]}, select=True, help="Location where the system will stock the finished products."),
        'name': fields.char('Description', required=True, select=True),
        'date': fields.datetime('Date', required=True, select=True, help="Move date: scheduled date until move is done, then date of actual move processing", states={'done': [('readonly', True)]}),
        'origin': fields.related('picking_id', 'origin', type='char', size=64, relation="stock.picking", string="Source", store=True),
        'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
            required=True, states={'done': [('readonly', True)]},
            help="This is the quantity of products from an inventory "
                 "point of view. For moves in the state 'done', this is the "
                 "quantity of products that were actually moved. For other "
                 "moves, this is the quantity of product that is planned to "
                 "be moved. Lowering this quantity does not generate a "
                 "backorder. Changing this quantity on assigned moves affects "
                 "the product reservation, and should be done with care."
        ),
        'price_unit': fields.float('Unit Price', digits_compute=dp.get_precision('Product Price'), help="Technical field used to record the product cost set by the user during a picking confirmation (when average price costing method is used)"),
        'picking_id': fields.many2one('stock.picking', 'Reference', select=True, states={'done': [('readonly', True)]}),
        'has_invoiced': fields.boolean('Has Invoiced'),
        'total_price': fields.float('Total Price'),
        'zero_price': fields.boolean('Free Charge'),
        'product_check_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
    }

    _defaults = {
        'date': fields.datetime.now,
    }

stock_move_wizard()


class stock_return_picking(orm.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self, cr, uid, ids, context=None):
        res = {}
        res = super(stock_return_picking, self).create_returns(cr, uid, ids, context=context)
        pick_obj = self.pool.get('stock.picking')
        if res.get('domain'):
            new_picking_ids = eval(res.get('domain'))[0][2]
            for stock_picking in pick_obj.browse(cr, uid, new_picking_ids, context=context):
                if stock_picking.service_id:
                    pick_obj.write(cr, uid, stock_picking.id, {'picking_svc_type':'return'}, context=context)
        return res

stock_return_picking()


# class stock_partial_picking(orm.TransientModel):
#     _inherit = 'stock.partial.picking'

#     def do_partial(self, cr, uid, ids, context=None):
#         res = super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)
#         print "========================"
#         test = self.browse(cr, uid, ids, context=context)
#         print res
#         print test
#         return res

# stock_partial_picking()