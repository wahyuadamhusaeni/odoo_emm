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
from openerp.tools.translate import _


class spare_parts_wizard(orm.TransientModel):
    _name = 'spare.parts.wizard'
    _description = 'Spare Parts Wizard'

    _columns = {
        'stock_move_id': fields.many2many('stock.move.wizard', 'spare_parts_wizard_stock_move_wizard_rel', 'spare_parts_wizard_id', 'stock_move_wizard_id', 'Stock Move'),
        'location_from_request': fields.many2one('stock.location', 'From Location', required=False),
        'location_to_request': fields.many2one('stock.location', 'Destination', required=False),
        'location_from_pickup': fields.many2one('stock.location', 'Pickup Location From', required=False),
        'location_to_pickup': fields.many2one('stock.location', 'Pickup Location To', required=False),
        'location_from_consume': fields.many2one('stock.location', 'From Location', required=False),
        'location_to_consume': fields.many2one('stock.location', 'Consumer Location', required=False),
        'location_from': fields.many2one('stock.location', 'From Location', required=False),
        'location_to': fields.many2one('stock.location', 'Destination', required=False),
        'user_pickup': fields.many2one('hr.employee', 'User Pickup', required=False),
        'product_id': fields.many2one('product.product', 'Product'),
        'stock_location': fields.many2many('stock.location', 'spare_parts_wizard_stock_location_rel', 'spare_parts_wizard_id', 'stock_location_id', 'Stock Location', readonly=True),
    }

    _defaults = {
        'location_from_request': lambda self, cr, uid, context: context['location_from_request'],
        'location_to_request': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid).company_id.pickup_location.id,
        'location_from_pickup': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid).company_id.pickup_location.id,
        'location_to_pickup': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid).company_id.transit_location.id,
        'location_from_consume': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid).company_id.transit_location.id,
        'location_to_consume': lambda self, cr, uid, context: self.pool.get('res.partner').browse(cr, uid, context['partner']).property_stock_customer.id,
    }

    # This method used to return dictionary that contains product_id and total product_qty based on related move_lines
    def calculate_total_product_qty(self, cr, uid, ids, move_lines=None, context=None):
        res = {}
        product_temp_list_1 = []
        product_temp_list_2 = {}
        for move_id in move_lines:
            obj = self.pool.get('stock.move').browse(cr, uid, move_id, context=context)
            product_id = obj.product_id.id
            product_qty = obj.product_qty
            if product_id not in product_temp_list_1:
                product_temp_list_1.append(product_id)
                product_temp_list_2.update({product_id: product_qty})
            elif product_id in product_temp_list_1:
                qty = product_temp_list_2.get(product_id)
                new_qty = qty + product_qty
                product_temp_list_2.update({product_id: new_qty})
        res = {'product_list': product_temp_list_2}
        return res

    def create_and_link_stock_move_wizard(self, cr, uid, ids, move_lines_id=None, move_lines_id_2=None, context=None):
        if not move_lines_id:
            return True

        prod_list_1 = self.calculate_total_product_qty(cr, uid, ids, move_lines_id, context=context).get('product_list')
        prod_list_2 = self.calculate_total_product_qty(cr, uid, ids, move_lines_id_2, context=context).get('product_list')

        # For each stock move found, link it into the newly created spare parts wizard object
        product_temp = []
        new_move_id = []
        for move_id in move_lines_id:
            obj = self.pool.get('stock.move').browse(cr, uid, move_id, context=context)
            if obj.product_id.id not in product_temp:
                product_temp.append(obj.product_id.id)
                product_qty = prod_list_1.get(obj.product_id.id, 0)
                product_qty_out = prod_list_2.get(obj.product_id.id, 0)
                total_qty = product_qty - product_qty_out
                value = {
                    'product_id': obj.product_id.id,
                    'product_uom': obj.product_uom.id,
                    'state': 'draft',
                    'location_id': obj.location_id.id,
                    'prodlot_id': obj.prodlot_id.id,
                    'location_dest_id': obj.location_dest_id.id,
                    'name': obj.name,
                    'has_invoiced': obj.has_invoiced,
                    'total_price': obj.price_unit * total_qty,
                    'origin': self.pool.get('service.request').browse(cr, uid, context.get('active_id'), context=context).name,
                    'price_unit': obj.price_unit,
                    'product_qty': total_qty,
                }
                if total_qty > 0:
                    res = self.pool.get('stock.move.wizard').create(cr, uid, value, context=context)
                    new_move_id.append(res)
        return self.pool.get('spare.parts.wizard').write(cr, uid, ids[0], {'stock_move_id': [(6, 0, new_move_id)]}, context=context)

    def refresh_pickup(self, cr, uid, ids, context=None):
        sr_obj = self.pool.get('service.request').browse(cr, uid, context.get('active_id'), context=context)
        pickup_location_id = context.get('location_from_pickup')
        stock_picking_ids = self.pool.get('stock.picking').search(cr, uid, [('service_id','=',sr_obj.id),('state','!=','cancel')], context=context)
        incoming_move_line_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','in',stock_picking_ids),('location_dest_id','in',[pickup_location_id]),('state','=','done')], context=context)
        outgoing_move_line_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','in',stock_picking_ids),('location_id','in',[pickup_location_id])], context=context)

        incoming_prod_list = self.calculate_total_product_qty(cr, uid, ids, incoming_move_line_ids, context=context).get('product_list')
        outgoing_prod_list = self.calculate_total_product_qty(cr, uid, ids, outgoing_move_line_ids, context=context).get('product_list')

        product_temp = []
        new_move_id = []
        for move_id in incoming_move_line_ids:
            obj = self.pool.get('stock.move').browse(cr, uid, move_id, context=context)
            if obj.product_id.id not in product_temp:
                product_temp.append(obj.product_id.id)
                incoming_prod_qty = incoming_prod_list.get(obj.product_id.id, 0)
                outgoing_prod_qty = outgoing_prod_list.get(obj.product_id.id, 0)
                total_product_qty = incoming_prod_qty - outgoing_prod_qty
                value = {
                    'product_id': obj.product_id.id,
                    'product_uom': obj.product_uom.id,
                    'state': 'draft',
                    'location_id': obj.location_id.id,
                    'prodlot_id': obj.prodlot_id.id,
                    'location_dest_id': obj.location_dest_id.id,
                    'name': obj.name,
                    'has_invoiced': obj.has_invoiced,
                    'total_price': obj.price_unit * total_product_qty,
                    'origin': sr_obj.name,
                    'price_unit': obj.price_unit,
                    'product_qty': total_product_qty,
                    'product_check_qty': total_product_qty,
                }
                if total_product_qty > 0:
                    res = self.pool.get('stock.move.wizard').create(cr, uid, value, context=context)
                    new_move_id.append(res)

        self.pool.get('spare.parts.wizard').write(cr, uid, ids[0], {'stock_move_id': [(6, 0, new_move_id)]}, context=context)

        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_spare_parts_pickup_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Spare Parts Pickup',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'spare.parts.wizard',
            'res_id': ids[0],
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    def refresh_consume(self, cr, uid, ids, context=None):
        sr_obj = self.pool.get('service.request').browse(cr, uid, context.get('active_id'), context=context)
        stock_picking_ids = self.pool.get('stock.picking').search(cr, uid, [('service_id','=',sr_obj.id),('state','!=','cancel')], context=context)
        transit_location_ids = self.pool.get('stock.location').search(cr, uid, [('usage_type','=','transit')], context=context)

        new_move_id = []
        for location in transit_location_ids:
            incoming_move_line_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','in',stock_picking_ids),('location_dest_id','in',[location]),('state','=','done')], context=context)
            outgoing_move_line_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','in',stock_picking_ids),('location_id','in',[location])], context=context)

            incoming_prod_list = self.calculate_total_product_qty(cr, uid, ids, incoming_move_line_ids, context=context).get('product_list')
            outgoing_prod_list = self.calculate_total_product_qty(cr, uid, ids, outgoing_move_line_ids, context=context).get('product_list')

            #for each stock move found, link it into the newly created spare parts wizard object
            product_temp = []
            for move_id in incoming_move_line_ids:
                obj = self.pool.get('stock.move').browse(cr, uid, move_id, context=context)
                if obj.product_id.id not in product_temp:
                    product_temp.append(obj.product_id.id)
                    incoming_prod_qty = incoming_prod_list.get(obj.product_id.id, 0)
                    outgoing_prod_qty = outgoing_prod_list.get(obj.product_id.id, 0)
                    total_product_qty = incoming_prod_qty - outgoing_prod_qty
                    value = {
                        'product_id': obj.product_id.id,
                        'product_uom': obj.product_uom.id,
                        'state': 'draft',
                        'location_id': obj.location_id.id,
                        'prodlot_id': obj.prodlot_id.id,
                        'location_dest_id': location,
                        'name': obj.name,
                        'has_invoiced': obj.has_invoiced,
                        'total_price': obj.price_unit * total_product_qty,
                        'origin': sr_obj.name,
                        'price_unit': obj.price_unit,
                        'product_qty': total_product_qty,
                        'product_check_qty': total_product_qty,
                    }
                    if total_product_qty > 0:
                        res = self.pool.get('stock.move.wizard').create(cr, uid, value, context=context)
                        new_move_id.append(res)

        self.pool.get('spare.parts.wizard').write(cr, uid, ids[0], {'stock_move_id': [(6, 0, new_move_id)]}, context=context)

        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_spare_parts_consume_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Spare Parts Consume',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'spare.parts.wizard',
            'res_id': ids[0],
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    def refresh_return(self, cr, uid, ids, context=None):
        sr_obj = self.pool.get('service.request').browse(cr, uid, context.get('active_id'), context=context)
        stock_picking_ids = self.pool.get('stock.picking').search(cr, uid, [('service_id','=',sr_obj.id),('state','!=','cancel')], context=context)
        pickup_location_ids = self.pool.get('stock.location').search(cr, uid, [('usage_type','=','pickup')], context=context)
        transit_location_ids = self.pool.get('stock.location').search(cr, uid, [('usage_type','=','transit')], context=context)

        new_move_id = []
        for location in pickup_location_ids:
            incoming_move_line_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','in',stock_picking_ids),('location_dest_id','in',[location]),('state','=','done')], context=context)
            outgoing_move_line_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','in',stock_picking_ids),('location_id','in',[location])], context=context)

            incoming_prod_list = self.calculate_total_product_qty(cr, uid, ids, incoming_move_line_ids, context=context).get('product_list')
            outgoing_prod_list = self.calculate_total_product_qty(cr, uid, ids, outgoing_move_line_ids, context=context).get('product_list')

            product_temp = []
            for move_id in incoming_move_line_ids:
                obj = self.pool.get('stock.move').browse(cr, uid, move_id, context=context)
                if obj.product_id.id not in product_temp:
                    product_temp.append(obj.product_id.id)
                    incoming_prod_qty = incoming_prod_list.get(obj.product_id.id, 0)
                    outgoing_prod_qty = outgoing_prod_list.get(obj.product_id.id, 0)
                    total_product_qty = incoming_prod_qty - outgoing_prod_qty
                    value = {
                        'product_id': obj.product_id.id,
                        'product_uom': obj.product_uom.id,
                        'state': 'draft',
                        'location_id': obj.location_id.id,
                        'prodlot_id': obj.prodlot_id.id,
                        'location_dest_id': obj.location_dest_id.id,
                        'name': obj.name,
                        'has_invoiced': obj.has_invoiced,
                        'total_price': obj.price_unit * total_product_qty,
                        'origin': sr_obj.name,
                        'price_unit': obj.price_unit,
                        'product_qty': total_product_qty,
                        'product_check_qty': total_product_qty,
                    }
                    if total_product_qty > 0:
                        res = self.pool.get('stock.move.wizard').create(cr, uid, value, context=context)
                        new_move_id.append(res)

        for location in transit_location_ids:
            incoming_move_line_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','in',stock_picking_ids),('location_dest_id','in',[location]),('state','=','done')], context=context)
            outgoing_move_line_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','in',stock_picking_ids),('location_id','in',[location])], context=context)

            incoming_prod_list = self.calculate_total_product_qty(cr, uid, ids, incoming_move_line_ids, context=context).get('product_list')
            outgoing_prod_list = self.calculate_total_product_qty(cr, uid, ids, outgoing_move_line_ids, context=context).get('product_list')

            product_temp = []
            for move_id in incoming_move_line_ids:
                obj = self.pool.get('stock.move').browse(cr, uid, move_id, context=context)
                if obj.product_id.id not in product_temp:
                    product_temp.append(obj.product_id.id)
                    incoming_prod_qty = incoming_prod_list.get(obj.product_id.id, 0)
                    outgoing_prod_qty = outgoing_prod_list.get(obj.product_id.id, 0)
                    total_product_qty = incoming_prod_qty - outgoing_prod_qty
                    value = {
                        'product_id': obj.product_id.id,
                        'product_uom': obj.product_uom.id,
                        'state': 'draft',
                        'location_id': obj.location_id.id,
                        'prodlot_id': obj.prodlot_id.id,
                        'location_dest_id': obj.location_dest_id.id,
                        'name': obj.name,
                        'has_invoiced': obj.has_invoiced,
                        'total_price': obj.price_unit * total_product_qty,
                        'origin': sr_obj.name,
                        'price_unit': obj.price_unit,
                        'product_qty': total_product_qty,
                        'product_check_qty': total_product_qty,
                    }
                    if total_product_qty > 0:
                        res = self.pool.get('stock.move.wizard').create(cr, uid, value, context=context)
                        new_move_id.append(res)

        self.pool.get('spare.parts.wizard').write(cr, uid, ids[0], {'stock_move_id': [(6, 0, new_move_id)]}, context=context)

        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_spare_parts_return_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Spare Parts Return',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'spare.parts.wizard',
            'res_id': ids[0],
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    # This method is used to create stock move and stock picking, then make the relation between service request and stock picking created
    # and also make relation between service request and stock move created
    def create_request(self, cr, uid, ids, context=None):
        #gather all information required to create stock picking and stock move and link them to sr and srl
        sr_obj = self.pool.get('service.request').browse(cr, uid, context.get('active_id'), context=context)
        wizard_obj = self.browse(cr, uid, ids[0], context=context)
        move_lines_wizard_id = context.get('stock_move_id', [])
        move_wizard_ids = []
        for move_id in move_lines_wizard_id:
            if move_id[1]:
                move_wizard_ids.append(move_id[1])
            else:
                if move_id[2]:
                    new_move_wizard_id = self.pool.get('stock.move.wizard').create(cr, uid, move_id[2], context=context)
                    move_wizard_ids.append(new_move_wizard_id)
        # move_wizard_ids = [move_id[1] for move_id in move_lines_wizard_id]
        move_ids = []
        for move_id in move_wizard_ids:
            obj = self.pool.get('stock.move.wizard').browse(cr, uid, move_id, context=context)
            value = {
                'product_id': obj.product_id.id,
                'product_uom': obj.product_uom.id,
                'state': 'draft',
                'location_id': wizard_obj.location_from_request.id,
                'prodlot_id': obj.prodlot_id.id,
                'location_dest_id': wizard_obj.location_to_request.id,
                'date': obj.date,
                'name': obj.name,
                'has_invoiced': obj.has_invoiced,
                'total_price': obj.price_unit * obj.product_qty,
                'origin': sr_obj.name,
                'price_unit': obj.price_unit,
                'product_qty': obj.product_qty,
            }
            res = self.pool.get('stock.move').create(cr, uid, value, context=context)
            move_ids.append(res)

        vals = {
            'type': 'internal',
            'origin': sr_obj.name,
            'move_lines': [(6, 0, move_ids)],
            'picking_svc_type': 'request',
            'service_id': sr_obj.id,
        }
        # Link stock move into service request
        for move_id in move_ids:
            self.pool.get('service.request').write(cr, uid, [context.get('active_id')], {'spare_parts_planning_move': [(4, move_id)]}, context=context)
        # Link stock picking created into service request
        res = self.pool.get('service.request').write(cr, uid, [context.get('active_id')], {'spare_parts_planning': [(0, 0, vals)]}, context=context)
        return res

    # This method is used to create a new stock move based on the selected stock move and create new stock picking,
    # Then make the relation between service request and stoc picking created
    def create_pickup(self, cr, uid, ids, context=None):
        #gather all information required to create stock picking and stock move and link them to sr and srl
        sr_obj = self.pool.get('service.request').browse(cr, uid, context.get('active_id'), context=context)
        move_wizard_ids = []
        for move_id in context.get('stock_move_id', []):
            if move_id[0] in [0, 1, 4, 6]:
                move_wizard_ids.append(move_id[1])
        # move_wizard_ids = [move_id[1] for move_id in context.get('stock_move_id',[])]
        # move_lines_wizard_id = context.get('stock_move_id', [])[0][2]
        # move_wizard_ids = [move_id for move_id in move_lines_wizard_id]
        move_ids = []
        for move_id in move_wizard_ids:
            obj = self.pool.get('stock.move.wizard').browse(cr, uid, move_id, context=context)
            if obj.product_qty > obj.product_check_qty:
                raise orm.except_orm(_('Error!'), _('Qty to be pickup is greater than qty requested'))
            value = {
                'product_id': obj.product_id.id,
                'product_uom': obj.product_uom.id,
                'state': 'draft',
                'location_id': context.get('location_from_pickup'),
                'prodlot_id': obj.prodlot_id.id,
                'location_dest_id': context.get('location_to_pickup'),
                'date': obj.date,
                'name': obj.name,
                'has_invoiced': obj.has_invoiced,
                'total_price': obj.price_unit * obj.product_qty,
                'origin': sr_obj.name,
                'price_unit': obj.price_unit,
                'product_qty': obj.product_qty,
                'product_check_qty': obj.product_qty,
            }
            res = self.pool.get('stock.move').create(cr, uid, value, context=context)
            move_ids.append(res)

        for wizard in self.browse(cr, uid, ids, context=context):
            vals = {
                'type': 'internal',
                'origin': sr_obj.name,
                'move_lines': [(6, 0, move_ids)],
                'picking_svc_type': 'pickup',
                'user_pickup_spare_part': wizard.user_pickup.id,
                'service_id': sr_obj.id,
            }
            #create stock picking
            new_picking = self.pool.get('stock.picking').create(cr, uid, vals, context=context)

            #automatically confirm and check availability of the stock picking created
            self.pool.get('stock.picking').action_assign(cr, uid, [new_picking], (context))

            #link stock picking created into service request
            res = self.pool.get('service.request').write(cr, uid, [context.get('active_id')], {'spare_parts_planning': [(4, new_picking)]}, context=context)

        #link stock move into service request
        for move_id in move_ids:
            self.pool.get('service.request').write(cr, uid, [context.get('active_id')], {'spare_parts_planning_move': [(4, move_id)]}, context=context)
        return res

    def create_pickup_print(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        self.create_pickup(cr, uid, ids, context=context)
        service = self.pool.get('service.request').browse(cr, uid, context.get('active_id'), context=context)
        service_data = self.pool.get('service.request').copy_data(cr, uid, context.get('active_id'), context=context)
        _taken_id = max([item.id for item in service.spare_parts_planning])
        picking = self.pool.get('stock.picking').browse(cr, uid, _taken_id, context=context)

        try:
            # _template = self.pool.get('ir.model.data').get_object(cr, uid, 'via_account_taxform', 'via_account_taxform_form_template', context=context)
            # _template = _template and _template.act_report_id and self.pool.get('ir.actions.report.xml').copy_data(cr, uid, _template.act_report_id.id, context=context) or False
            _template = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'pickup_sparepart_form_template', context=context)
            _template = _template and _template.act_report_id and self.pool.get('ir.actions.report.xml').copy_data(cr, uid, _template.act_report_id.id, context=context) or False

            _datas = {
                'ids': [picking.id],
            }
            ctx.update({'service_request': service_data})
            _template.update({'datas': _datas, 'context': ctx})
            return _template
        except:
            raise orm.except_orm(_('Error !'), _('Cannot load form. Please contact your administrator'))


    # This method is used to create a new stock move based on the selected stock move and create new stock picking out,
    # Then make the relation between service request and stoc picking out created
    def create_consume(self, cr, uid, ids, context=None):
        #gather all information required to create stock picking and stock move and link them to sr and srl
        sr_obj = self.pool.get('service.request').browse(cr, uid, context.get('active_id'), context=context)
        move_wizard_ids = []
        for move_id in context.get('stock_move_id',[]):
            if move_id[0] in [0,1,4,6]:
                move_wizard_ids.append(move_id[1])
        # move_wizard_ids = [move_id[1] for move_id in context.get('stock_move_id',[])]
        # move_lines_wizard_id = context.get('stock_move_id', [])[0][2]
        # move_wizard_ids = [move_id for move_id in move_lines_wizard_id]
        move_ids = []
        for move_id in move_wizard_ids:
            obj = self.pool.get('stock.move.wizard').browse(cr, uid, move_id, context=context)
            if obj.product_qty > obj.product_check_qty:
                raise orm.except_orm(_('Error!'), _('Qty to be consumed is greater than qty pickup'))
            value = {
                'product_id': obj.product_id.id,
                'product_uom': obj.product_uom.id,
                'state': 'draft',
                'location_id': context.get('location_from_consume'),
                'prodlot_id': obj.prodlot_id.id,
                'location_dest_id': context.get('location_to_consume'),
                'date': obj.date,
                'name': obj.name,
                'has_invoiced': obj.has_invoiced,
                'total_price': obj.price_unit * obj.product_qty,
                'origin': sr_obj.name,
                'price_unit': obj.price_unit,
                'product_qty': obj.product_qty,
                'product_check_qty': obj.product_qty,
            }
            res = self.pool.get('stock.move').create(cr, uid, value, context=context)
            move_ids.append(res)

        vals = {
            'type': 'out',
            'origin': sr_obj.name,
            'move_lines': [(6, 0, move_ids)],
            'picking_svc_type': 'consume',
            'service_id': sr_obj.id,
        }
        #create stock picking
        new_picking = self.pool.get('stock.picking').create(cr, uid, vals, context=context)

        #automatically confirm and check availability of the stock picking created
        self.pool.get('stock.picking').action_assign(cr, uid, [new_picking], (context))

        #link stock picking created into service request
        res = self.pool.get('service.request').write(cr, uid, [context.get('active_id')], {'spare_parts_consume': [(4, new_picking)]}, context=context)

        #link stock move into service request
        for move_id in move_ids:
            self.pool.get('service.request').write(cr, uid, [context.get('active_id')], {'spare_parts_consume_move': [(4, move_id)]}, context=context)

        #pop up the delivery wizard
        self.pool.get('stock.picking').write(cr, uid, [new_picking], {'ready_for_transfer': True}, context=context)
        return self.pool.get('stock.picking').action_process(cr, uid, [new_picking], context=context)

    # This method is used to create a new stock move based on the selected stock move and create new stock picking,
    # Then make the relation between service request and stoc picking created
    def create_return(self, cr, uid, ids, context=None):
        #gather all information required to create stock picking and stock move and link them to sr and srl
        sr_obj = self.pool.get('service.request').browse(cr, uid, context.get('active_id'), context=context)
        move_wizard_ids = []
        for move_id in context.get('stock_move_id',[]):
            if move_id[0] in [0,1,4,6]:
                move_wizard_ids.append(move_id[1])
        # move_wizard_ids = [move_id[1] for move_id in context.get('stock_move_id',[])]
        # move_lines_wizard_id = context.get('stock_move_id', [])[0][2]
        # move_wizard_ids = [move_id for move_id in move_lines_wizard_id]
        move_ids = []
        for move_id in move_wizard_ids:
            obj = self.pool.get('stock.move.wizard').browse(cr, uid, move_id, context=context)
            if obj.product_qty > obj.product_check_qty:
                raise orm.except_orm(_('Error!'), _('Qty to be returned is greater than qty given'))
            value = {
                'product_id': obj.product_id.id,
                'product_uom': obj.product_uom.id,
                'state': 'draft',
                'location_id': obj.location_dest_id.id,
                'prodlot_id': obj.prodlot_id.id,
                'location_dest_id': context.get('location_to'),
                'date': obj.date,
                'name': obj.name,
                'has_invoiced': obj.has_invoiced,
                'total_price': obj.price_unit * obj.product_qty,
                'origin': sr_obj.name,
                'price_unit': obj.price_unit,
                'product_qty': obj.product_qty,
                'product_check_qty': obj.product_qty,
            }
            res = self.pool.get('stock.move').create(cr, uid, value, context=context)
            move_ids.append(res)

        for wizard in self.browse(cr, uid, ids, context=context):
            vals = {
                'type': 'internal',
                'origin': sr_obj.name,
                'move_lines': [(6, 0, move_ids)],
                'picking_svc_type': 'return',
                'user_pickup_spare_part': wizard.user_pickup.id,
                'service_id': sr_obj.id,
            }
            #create stock picking
            new_picking = self.pool.get('stock.picking').create(cr, uid, vals, context=context)

            #automatically confirm and check availability of the stock picking created
            self.pool.get('stock.picking').action_assign(cr, uid, [new_picking], (context))

            #link stock picking created into service request
            res = self.pool.get('service.request').write(cr, uid, [context.get('active_id')], {'spare_parts_planning': [(4, new_picking)]}, context=context)

        # Link stock move into service request
        for move_id in move_ids:
            self.pool.get('service.request').write(cr, uid, [context.get('active_id')], {'spare_parts_planning_move': [(4, move_id)]}, context=context)
        return res

    def stock_by_location(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        if not context.get('product_id'):
            raise orm.except_orm(_('Error!'), _('There Is No Product Selected !!!'))

        stock_loc_ids = []
        wizard_data = self.pool.get('spare.parts.wizard').browse(cr, uid, ids and ids[0], context=context)
        sl_id = wizard_data.id
        stock_location_ids = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')], context=context)
        stock_location_obj = self.pool.get('stock.location').browse(cr, uid, stock_location_ids, context=context)

        for stock_location in stock_location_obj:
            if stock_location.stock_real > 0 or stock_location.stock_virtual > 0:
                stock_loc_ids.append(stock_location.id)

        if len(stock_loc_ids) > 0:
            self.pool.get('spare.parts.wizard').write(cr, uid, sl_id, {'stock_location': [(6, 0, stock_loc_ids)]}, context=context)

        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_stock_location_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Location of %s' % (self.pool.get('product.product').browse(cr, uid, context.get('product_id'), context=context).name),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'spare.parts.wizard',
            'res_id': sl_id,
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    def back_to_request(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        wizard_data = self.pool.get('spare.parts.wizard').browse(cr, uid, ids and ids[0], context=context)
        sl_id = wizard_data.id

        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_spare_parts_request_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Spare Parts Request',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'spare.parts.wizard',
            'res_id': sl_id,
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

spare_parts_wizard()
