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
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _


class service_request_keyword(orm.Model):
    _name = 'service.request.keyword'
    _description = 'Service Request Keyword'

    _columns = {
        'name': fields.char('Name', required=True),
        'is_active': fields.boolean('Active'),
    }

service_request_keyword()


class service_request_skill_set(orm.Model):
    _name = 'service.request.skill.set'
    _description = 'Service Request Skill Set'
    _parent_name = "skill_parent_id"
    _parent_store = True

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'skill_parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['skill_parent_id']:
                name = record['skill_parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {
        'name': fields.char('Name', required=True),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
        'is_active': fields.boolean('Active'),
        'model': fields.many2one('ir.model', 'Model'),
        'doc_id': fields.integer('Document ID'),
        'skill_parent_id': fields.many2one('service.request.skill.set', 'Parent Skill Set', select=True, ondelete='cascade'),
        'skill_child_id': fields.one2many('service.request.skill.set', 'skill_parent_id', string='Child Skill Set'),
        'parent_left': fields.integer('Left Parent', select=1),
        'parent_right': fields.integer('Right Parent', select=1),
    }

service_request_skill_set()


class service_state(orm.Model):
    _name = "service.state"
    _description = "service State"

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
    }

service_state()


class service_request(orm.Model):
    _name = 'service.request'
    _description = 'Service Request'
    _inherit = ['mail.thread']

    #this method is called whenever service_request class is being called.
    #this method will calculate the differences of days between the date specified in the document and the date when the document is being viewed by user.
    def elapsed_time_function(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for obj in self.pool.get('service.request').browse(cr, uid, ids, context=context):
            date = obj.date
            if date:
                date = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)
            else:
                date = datetime.now()
            res[obj.id] = (datetime.now() - date).days
        return res

    #this method is called whenever service_request class is being called.
    #this method will calculate the differences of days between the warranty start date specified in the document and the date when the document is being viewed by user.
    def elapsed_warranty_time_function(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for obj in self.pool.get('service.request').browse(cr, uid, ids, context=context):
            date = obj.warranty_start
            if date:
                date = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
            else:
                date = datetime.now()
            res[obj.id] = (datetime.now() - date).days
        return res

    def warranty_time_function(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for obj in self.pool.get('service.request').browse(cr, uid, ids, context=context):
            requested_date = obj.date
            warranty_start = obj.warranty_start
            if not requested_date or not warranty_start:
                res[obj.id] = 0
            else:
                requested_date = datetime.strptime(requested_date, DEFAULT_SERVER_DATETIME_FORMAT)
                warranty_start = datetime.strptime(warranty_start, DEFAULT_SERVER_DATE_FORMAT)
                res[obj.id] = (requested_date.date() - warranty_start.date()).days
        return res

    def warranty_warning_function(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for obj in self.pool.get('service.request').browse(cr, uid, ids, context=context):
            if obj.warranty_end:
                warranty_end = datetime.strptime(obj.warranty_end, DEFAULT_SERVER_DATE_FORMAT)
                requested_date = datetime.strptime(obj.date, DEFAULT_SERVER_DATETIME_FORMAT)
                if warranty_end > requested_date:
                    res[obj.id] = False
                else:
                    res[obj.id] = True
            else:
                res[obj.id] = True
        return res

    def serial_number_validation(self, cr, uid, ids, vals, context=None):
        serial_number_product_id = 0
        product_id = 0

        if ids:
            if not isinstance(ids, (list)):
                ids = [ids]

        if vals.get('serial_number'):
            serial_number = self.pool.get('stock.production.lot').browse(cr, uid, vals.get('serial_number'), context=context)
            serial_number_product_id = serial_number.product_id.id
        elif ids:
            serial_number = self.browse(cr, uid, ids[0], context=context).serial_number
            if serial_number:
                serial_number_product_id = serial_number.product_id.id

        if vals.get('product_id'):
            product_id = self.pool.get('product.product').browse(cr, uid, vals.get('product_id'), context=context).id
        elif ids:
            product_id = self.browse(cr, uid, ids[0], context=context).product_id.id

        if serial_number_product_id == 0 or product_id == 0:
            return True
        elif serial_number_product_id != product_id:
            raise orm.except_orm(_('Warning !!!'), _('Serial number does not match with the product'))
        else:
            return True

    #this method is called when a new record is being created.
    # This method will get field 'name', and return the field based on the prefix in ir_sequence.
    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'service.request') or '/'

        #to get the value from on_change_partner function and store it
        partner_type_val = self.on_change_partner(cr, uid, [], vals.get('partner'), context=context)
        partner_type = partner_type_val.get('value', '').get('partner_type', '')
        vals.update({
            'partner_type': partner_type,
        })

        if vals.get('delivery_order'):
            delivery_order_date = self.pool.get('stock.picking.out').browse(cr, uid, vals.get('delivery_order'), context=context).date
            vals.update({
                'delivery_order_date': delivery_order_date,
            })

        if vals.get('product_id'):
            vals.update({
                'warranty_duration': self.pool.get('product.product').browse(cr, uid, vals.get('product_id'), context=context).warranty,
            })

        self.serial_number_validation(cr, uid, False, vals, context=context)

        return super(service_request, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('delivery_order'):
            delivery_order_date = self.pool.get('stock.picking.out').browse(cr, uid, vals.get('delivery_order'), context=context).date
            vals.update({
                'delivery_order_date': delivery_order_date,
            })

        self.serial_number_validation(cr, uid, ids, vals, context=context)

        return super(service_request, self).write(cr, uid, ids, vals, context=context)

    # This method will called code.decode and then return the selection inside the related category (service_request_state)
    def _get_selection(self, cr, uid, context=None):
        res = self.pool.get('code.decode').get_selection_for_category(cr, uid, 'via_service', 'service_request_state', context=None)
        return res

    # This method will reset some field when the currect document is being duplicated
    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'name': '/',
            'state': 'draft',
            'spare_parts_planning': False,
            'spare_parts_consume': False,
            'spare_parts_planning_move': False,
            'spare_parts_consume_move': False,
            'service_request': False,
            'service_execute': False,
            'service_task': False,
            'service_invoice': False,
        }
        std_default.update(default)
        return super(service_request, self).copy_data(cr, uid, id, default=std_default, context=context)

    _columns = {
        'name': fields.char('Service Request No', size=64, readonly=True, required=True),
        'sr_name': fields.char('Name', required=False),
        'sr_keyword': fields.many2many('service.request.keyword', 'service_request_keyword_rel', 'service_request_id', 'service_request_keyword_id', 'Keyword'),
        'partner': fields.many2one('res.partner', 'Requested By', required=True),
        'partner_type': fields.char('Requester Type', readonly=True),
        'date': fields.datetime('Requested On', required=True),
        'elapsed_time': fields.function(elapsed_time_function, string='SR Elapsed Day(s)', method=True, type='integer', readonly=True, help="Requested Date until Date Now"),
        'partner_assign': fields.many2one('res.users', 'Assigned To', required=True),
        'location_from': fields.many2one('stock.location', 'From Location', required=False),
        'description': fields.text('Description'),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'serial_number': fields.many2one('stock.production.lot', 'Serial Number'),
        'delivery_order': fields.many2one('stock.picking.out', 'Delivery Order', domain=[('type', '=', 'out')]),
        'delivery_order_date': fields.date('Delivery Order Date', readonly=True),
        'sr_skill_set': fields.many2many('service.request.skill.set', 'service_request_skill_set_rel', 'service_request_id', 'service_request_skill_set_id', 'Skill Set'),
        'warranty_start': fields.date('Warranty Start', help="Delivery Order Date"),
        'warranty_end': fields.date('Warranty End', readonly=True, help="Warranty Start + Warranty Duration"),
        'warranty_duration': fields.float('Warranty Duration Month(s)', readonly=True),
        'warranty_elapsed_time': fields.function(elapsed_warranty_time_function, string='Warranty Elapsed Day(s)', method=True, type='integer', readonly=True, help="Warranty Start until Date Now"),
        'warranty_time': fields.function(warranty_time_function, string="Warranty Time", method=True, type='integer', readonly=True, help="Warranty Start until Requested Date"),
        'state': fields.selection([('draft', 'Draft'), ('inprogress', 'In Progress'), ('pending',  'Pending'), ('cancel', 'Cancelled'), ('done', 'Done')], 'State'),
        'change_view': fields.boolean('Change View'),
        'spare_parts_planning': fields.many2many('stock.picking', 'service_request_stock_picking_rel', 'service_request_id', 'stock_picking_id', 'Planning'),
        'spare_parts_planning_move': fields.many2many('stock.move', 'service_request_stock_move_rel', 'service_request_id', 'stock_move_id', 'Planning', domain=[('picking_id.type', '=', 'internal')]),
        'spare_parts_consume': fields.many2many('stock.picking.out', 'service_request_stock_picking_out_rel', 'service_request_id', 'stock_picking_out_id', 'Consumed'),
        'spare_parts_consume_move': fields.many2many('stock.move', 'service_request_stock_move_rel', 'service_request_id', 'stock_move_id', 'Consumed', domain=[('picking_id.type', '=', 'out')]),
        'service_request': fields.one2many('service.fee', 'sr_id', 'Request', domain=[('service_type', '=', 'request')]),
        'service_execute': fields.one2many('service.fee', 'sr_id', 'Executed', domain=[('service_type', '=', 'execute')]),
        'service_task': fields.many2many('project.task', 'service_request_project_task_rel', 'service_request_id', 'project_task_id', 'Task'),
        'service_invoice': fields.many2many('account.invoice', 'service_request_account_invoice_rel', 'service_request_id', 'account_invoice_id', 'Service Invoice'),
        'warranty_warning': fields.function(warranty_warning_function, string='Warranty Warning', method=True, type='boolean', readonly=True),
        'service_information_visibility': fields.boolean('Service Information Visibility'),
        'service_information': fields.char('Service Information', readonly=True),
        'company_id': fields.many2one('res.company', 'Company'),
    }

    _defaults = {
        'name': lambda obj, cr, uid, context: '/',
        'date': fields.datetime.now,
        'partner_assign': lambda obj, cr, uid, context: uid,
        'state': 'draft',
        'change_view': True,
        'location_from': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid).company_id.spare_parts_location.id,
        'service_information_visibility': False,
        'service_information': _('Default service fee added for product with expired warranty'),
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'service.request', context=c)
    }

    def confirm_sr(self, cr, uid, ids, context=None):
        for service in self.browse(cr, uid, ids, context=context):
            temp_ids = []
            if service.warranty_warning:
                if service.service_request:
                    for service_fee in service.service_request:
                        if service_fee.additional is True:
                            temp_ids.append(service_fee.id)
                if not temp_ids:
                    additional_fee = service.product_id.additional_service_fee
                    if not additional_fee:
                        additional_fee = self.pool.get('res.users').browse(cr, uid, uid).company_id.additional_service_fee

                    if additional_fee:
                        value = {
                            'sr_id': service.id,
                            'service_id': additional_fee.id,
                            'service_qty': 1.00,
                            'service_uom': additional_fee.uom_id,
                            'service_price': additional_fee.list_price,
                            'service_total': additional_fee.list_price,
                            'additional': True,
                        }
                        self.pool.get('service.fee').create(cr, uid, value, context=context)
                        self.write(cr, uid, ids, {'service_information': _('Default service fee added for product with expired warranty')}, context=context)
                    else:
                        self.write(cr, uid, ids, {'service_information': _('No service fee defaulted for product with expired warranty')}, context=context)
                self.write(cr, uid, ids, {'service_information_visibility': True}, context=context)
            self.write(cr, uid, ids, {'state': 'inprogress'}, context=context)

    def pending_sr(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'pending'}, context=context)

    def cancel_sr(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)

    def done_sr(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done'}, context=context)

    # This method will change the value of change_view field from true to false, vice versa
    def toggle_view_true(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'change_view': True}, context=context)

    def toggle_view_false(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'change_view': False}, context=context)

    def dummy_button(self, cr, uid, ids, context=None):
        return True

    # This method is called when there is any changes with 'partner' field
    # This method will check whether the partner selected is a Supplier, Customer or Employee
    def on_change_partner(self, cr, uid, ids, partner_id, context=None):
        result = {}
        partner_temp = []
        if partner_id:
            for partner in self.pool.get('res.partner').browse(cr, uid, [partner_id], context=context):
                is_customer = partner.customer
                is_employee = partner.employee
                is_supplier = partner.supplier
                if is_customer:
                    partner_temp.append('Customer')
                elif is_employee:
                    partner_temp.append('Employee')
                elif is_supplier:
                    partner_temp.append('Supplier')
            result['partner_type'] = ", ".join(str(n) for n in partner_temp)
            return {'value': result}
        else:
            return True

    # This method is called when there is any changes with 'serial_number' field
    # This method will fill out 'product_id' field based on the 'serial_number' chosen
    # This method will assign default value for 'delivery_order' and put the domain in 'deliver_order'
    def on_change_serial_number(self, cr, uid, ids, serial_number, context=None):
        if not serial_number:
            return True

        prod_id = self.pool.get('stock.production.lot').browse(cr, uid, serial_number, context=context).product_id
        move_ids = self.pool.get('stock.move').search(cr, uid, [('prodlot_id', '=', serial_number)], context=context)
        temp_picking_ids = []
        for move in self.pool.get('stock.move').browse(cr, uid, move_ids, context=context):
            temp_picking_ids.append(move.picking_id.id)
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('id', 'in', temp_picking_ids), ('type', '=', 'out'),  ('state', '=', 'done')], context=context)
        if not picking_ids:
            picking_id = False
        else:
            picking_id = picking_ids[0]

        return {
            'domain': {'delivery_order': [('id', 'in', picking_ids), ('state', '=', 'done')]},
            'value': {'delivery_order': picking_id, 'product_id': prod_id.id},
        }

    # This method is called when there is any changes with 'product_id' field
    # This method will:
    #   1. will put the domain for 'serial_number' field based on the product_id selected
    #   2. reset the serial_number
    #   3. automatically fill the sr_skill_set field based on the registered tag for certain product
    def on_change_product_id(self, cr, uid, ids, product_id, context=None):
        if not product_id:
            return True
        product_name = self.pool.get('product.product').browse(cr, uid, product_id, context=context).name
        skill_set_ids = self.pool.get('service.request.skill.set').search(cr, uid, [('name', '=', product_name)], context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'product.product')], context=context)[0]
        if not skill_set_ids:
            temp = self.pool.get('service.request.skill.set').create(cr, uid, {'name': product_name, 'model': model, 'doc_id': product_id}, context=context)
            skill_set_ids.append(temp)

        return {
            # 'domain': {'serial_number': [('product_id', '=', product_id)]},
            # 'value': {'sr_skill_set': [(6, 0, skill_set_ids)], 'serial_number': False, 'delivery_order': False},
            'value': {'sr_skill_set': [(6, 0, skill_set_ids)]},
        }

    # This method is called when there is any changes with 'delivery_order' field
    # This method will assign default value for 'warranty_start' based on the latest stock move related
    def on_change_delivery_order(self, cr, uid, ids, delivery_order, context=None):
        if not delivery_order:
            return True
        result = {}
        stock_move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', delivery_order), ('state', '=', 'done')], context=context)
        stock_move = self.pool.get('stock.move').browse(cr, uid, stock_move_ids, context=context)
        if not stock_move:
            return True
        date = stock_move[0].date
        for move in stock_move:
            if date > move.date:
                date = move.date
        order_date = self.pool.get('stock.picking.out').browse(cr, uid, delivery_order, context=context).date
        order_date = datetime.strptime(order_date, DEFAULT_SERVER_DATETIME_FORMAT)
        order_date = order_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        if order_date:
            result['delivery_order_date'] = order_date
        else:
            result['delivery_order_date'] = False
        return {'value': result}

    def Copy(self, cr, uid, ids, context=None):
        res = {}
        if not context.get('delivery_order_date'):
                return True
        else:
            obj = self.browse(cr, uid, ids, context=context)
            date = context.get('delivery_order_date')
            for service in obj:
                date_end = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=int(service.warranty_duration))
                res = self.write(cr, uid, ids, {'warranty_start': date, 'warranty_end': date_end})
            return res

    #this method is used to called action window with model = sr.summary
    def summary(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        obj = self.browse(cr, uid, ids, context=context)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Summary of %s') % (obj[0].name),
            'view_mode': 'tree',
            'view_type': 'form',
            'res_model': 'sr.summary',
            'nodestroy': True,
            'target': 'new',
            'domain': [('origin', '=', obj[0].name)],
            'context': context,
        }

    def knowledge_base(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        obj = self.browse(cr, uid, ids, context=context)[0]
        sr_skill_set = [sr_skill_set.id for sr_skill_set in obj.sr_skill_set]

        return {
            'type': 'ir.actions.act_window',
            'name': _('Knowledge of %s') % (obj.name),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'document.page',
            'nodestroy': True,
            'target': 'current',
            'domain': [('sr_skill_set', 'in', sr_skill_set)],
            'context': context,
        }

    def history_1(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        obj = self.browse(cr, uid, ids, context=context)[0]
        partner = obj.partner and obj.partner.parent_id or obj.partner or False

        return {
            'type': 'ir.actions.act_window',
            'name': _('History of %s') % (partner.name),
            'view_mode': 'tree,form',
            'res_model': 'service.request',
            'nodestroy': True,
            'target': 'current',
            'domain': [('partner', '=', partner.id)],
            'context': context,
        }

    def history_2(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        obj = self.browse(cr, uid, ids, context=context)[0]
        partner = obj.partner and obj.partner.parent_id or obj.partner or False
        product = obj.product_id
        prodlot = obj.serial_number and obj.serial_number.id or -1

        return {
            'type': 'ir.actions.act_window',
            'name': _('History of %s') % (product.name),
            'view_mode': 'tree,form',
            'res_model': 'service.request',
            'nodestroy': True,
            'target': 'current',
            'domain': [('partner', '=', partner.id), '|', ('product_id', '=', product.id), ('serial_number', '=', prodlot)],
            'context': context,
        }

    #this method is used to called action window with xml id = view_spare_parts_request_form
    def spare_parts_request(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_spare_parts_request_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Spare Parts Request'),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'spare.parts.wizard',
            'nodestroy': True,
            'target': 'new',
            'context': context,
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

    #this method is used to called action window with xml id = view_spare_parts_pickup_form
    #this method will create object called spare parts wizard and link it with the stock move which the state = done
    def spare_parts_pickup(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for sr_id in ids:
            sr_obj = self.pool.get('service.request').browse(cr, uid, sr_id, context=context)
            pickup_location_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.pickup_location.id
            stock_picking_ids = self.pool.get('stock.picking').search(cr, uid, [('service_id','=',sr_id),('state','!=','cancel')], context=context)
            incoming_move_line_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','in',stock_picking_ids),('location_dest_id','in',[pickup_location_id]),('state','=','done')], context=context)
            outgoing_move_line_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','in',stock_picking_ids),('location_id','in',[pickup_location_id])], context=context)

        #create spare parts wizard
        sp_id = self.pool.get('spare.parts.wizard').create(cr, uid, {}, context=context)

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
                    self.pool.get('spare.parts.wizard').write(cr, uid, sp_id, {'stock_move_id': [(4, res)]}, context=context)

        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_spare_parts_pickup_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Spare Parts Pickup'),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'spare.parts.wizard',
            'res_id': sp_id,
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    #this method is used to called action window with xml id = view_spare_parts_consume_form
    #this method will create object called spare parts wizard and link it with the stock move which the state = done
    def spare_parts_consume(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for sr_id in ids:
            sr_obj = self.pool.get('service.request').browse(cr, uid, sr_id, context=context)
            stock_picking_ids = self.pool.get('stock.picking').search(cr, uid, [('service_id','=',sr_id),('state','!=','cancel')], context=context)
            transit_location_ids = self.pool.get('stock.location').search(cr, uid, [('usage_type','=','transit')], context=context)

        #create spare parts wizard
        sp_id = self.pool.get('spare.parts.wizard').create(cr, uid, {}, context=context)

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
                        self.pool.get('spare.parts.wizard').write(cr, uid, sp_id, {'stock_move_id': [(4, res)]}, context=context)

        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_spare_parts_consume_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Spare Parts Consume'),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'spare.parts.wizard',
            'res_id': sp_id,
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    #this method is used to called action window with xml id = view_spare_parts_return_form
    #this method will create object called spare parts wizard and link it with the stock move which the state = done
    def spare_parts_return(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for sr_id in ids:
            sr_obj = self.pool.get('service.request').browse(cr, uid, sr_id, context=context)
            stock_picking_ids = self.pool.get('stock.picking').search(cr, uid, [('service_id','=',sr_id),('state','!=','cancel')], context=context)
            pickup_location_ids = self.pool.get('stock.location').search(cr, uid, [('usage_type','=','pickup')], context=context)
            transit_location_ids = self.pool.get('stock.location').search(cr, uid, [('usage_type','=','transit')], context=context)

        #create spare parts wizard
        sp_id = self.pool.get('spare.parts.wizard').create(cr, uid, {}, context=context)

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
                        self.pool.get('spare.parts.wizard').write(cr, uid, sp_id, {'stock_move_id': [(4, res)]}, context=context)

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
                        self.pool.get('spare.parts.wizard').write(cr, uid, sp_id, {'stock_move_id': [(4, res)]}, context=context)

        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_spare_parts_return_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Spare Parts Return'),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'spare.parts.wizard',
            'res_id': sp_id,
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    #this method is used to called action window with xml id = view_service_fee_execute_form
    def service_fee_execute(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for sr_id in ids:
            service_fee_ids = self.pool.get('service.fee').search(cr, uid, [('sr_id', '=', sr_id), ('service_type', '=', 'request')], context=context)

        #create service fee wizard
        sf_id = self.pool.get('service.fee.wizard').create(cr, uid, {}, context=context)
        #for each stock move found, link it into the newly created spare parts wizard object
        self.pool.get('service.fee.wizard').write(cr, uid, sf_id, {'service_fee_id': [(6, 0, service_fee_ids)]}, context=context)
        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_service_fee_execute_form', context=context).id
        context.update({'service_request_id': ids[0]})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Service Fee Execute'),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'service.fee.wizard',
            'res_id': sf_id,
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    #this method is used to called action window with xml id = view_assign_service_task_form
    def assign_task(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        skill_set = []
        parent_skill_set = []
        for sr_id in ids:
            sr_obj = self.pool.get('service.request').browse(cr, uid, sr_id, context=context)
            skill_set = [skill_set.id for skill_set in sr_obj.sr_skill_set]
            for skill_set_obj in self.pool.get('service.request.skill.set').browse(cr, uid, skill_set, context=context):
                parent_ids = self.pool.get('service.request.skill.set').search(cr, uid, [('parent_left', '<', skill_set_obj.parent_left), ('parent_right', '>', skill_set_obj.parent_right)], context=context)
                for parent_id in parent_ids:
                    parent_skill_set.append(parent_id)
            hr_employee_id = self.pool.get('hr.employee').search(cr, uid, ['|', ('hr_employee_skills', 'in', skill_set), ('hr_employee_skills', 'in', parent_skill_set)], context=context)

        #create service task wizard
        st_id = self.pool.get('service.task.wizard').create(cr, uid, {}, context=context)

        #reset all the hit in each employee
        default_employee_ids = self.pool.get('hr.employee').search(cr, uid, [], context=context)
        for hr_employee in default_employee_ids:
            self.pool.get('hr.employee').write(cr, uid, hr_employee, {'hit': 0}, context=context)

        #for each employee, write no of hit based on the employee skills over sr skill set
        for hr_employee in hr_employee_id:
            employee_skill_set = [employee_skill_set.id for employee_skill_set in self.pool.get('hr.employee').browse(cr, uid, hr_employee, context=context).hr_employee_skills]
            counter = 0
            for skill in employee_skill_set:
                if skill in skill_set:
                    counter = counter + 2
                elif skill in parent_skill_set:
                    counter = counter + 1
            self.pool.get('hr.employee').write(cr, uid, hr_employee, {'hit': counter}, context=context)

        #find which company id that user belonged to
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        company_hit = self.pool.get('res.company').browse(cr, uid, company_id, context=context).hit
        company_limit = self.pool.get('res.company').browse(cr, uid, company_id, context=context).limit

        #search employee where no of hit equals or greater than no of hit specified in the company configuration
        #and also search employee where category_ids related to category_ids which is defaulted in company
        company_employee_category = [cat.id for cat in self.pool.get('res.company').browse(cr, uid, company_id, context=context).hr_employee_category]
        employee_hit_ids = self.pool.get('hr.employee').search(cr, uid, [('hit', '>=', company_hit), ('category_ids', 'in', company_employee_category), ('user_id', '!=', False)], context=context, limit=company_limit, order='hit DESC')

        #make relation between service task wizard and employee that has been filtered
        if employee_hit_ids:
            for employee in employee_hit_ids:
                self.pool.get('service.task.wizard').write(cr, uid, st_id, {'service_employee_id': [(4, employee)]}, context=context)

        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_assign_service_task_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Task'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'service.task.wizard',
            'res_id': st_id,
            'view_id': view_id,
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    #this method is used to called action window with xml id = view_service_invoice_form
    def create_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        sp_consume_temp = []
        service_temp = []
        for sr_id in ids:
            sr_obj = self.pool.get('service.request').browse(cr, uid, sr_id, context=context)
            spare_parts_consumed = sr_obj.spare_parts_consume
            service_fee = sr_obj.service_execute
            for sp_consume in spare_parts_consumed:
                if sp_consume.state == 'done':
                    sp_consume_temp.append(sp_consume.id)
            for service in service_fee:
                if service.service_type == 'execute':
                    service_temp.append(service.id)
        stock_move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', 'in', sp_consume_temp), ('has_invoiced', '=', False)], context=context)
        service_fee_ids = self.pool.get('service.fee').search(cr, uid, [('id', 'in', service_temp), ('has_invoiced', '=', False)], context=context)
        si_id = self.pool.get('service.invoice').create(cr, uid, {'sr_id': sr_id, 'stock_move_ids': [(6, 0, stock_move_ids)]}, context=context)
        self.pool.get('service.invoice').write(cr, uid, si_id, {'stock_move': [(6, 0, stock_move_ids)], 'service_fee': [(6, 0, service_fee_ids)]}, context=context)

        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_service_invoice_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Service Invoice'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'service.invoice',
            'res_id': si_id,
            'view_id': view_id,
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

service_request()
