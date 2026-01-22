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
from openerp import netsvc
from openerp import SUPERUSER_ID
from openerp.tools.translate import _


class stock_inventory(orm.Model):
    _inherit = 'stock.inventory'

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res_return = {}
        try:
            for obj in self.pool.get('stock.inventory').browse(cr, uid, ids, context=context):
                approval_list = obj.approval_list
                for approval in approval_list:
                    if approval.approval_type == 'auto':
                        if not obj.auto_approval:
                            res_return = self.pool.get('stock.inventory').write(cr, uid, obj.id, {'auto_approval': True}, context=context)
                        elif obj.auto_approval:
                            res_return = self.pool.get('stock.inventory').write(cr, uid, obj.id, {'auto_approval': False}, context=context)
                res[obj.id] = res_return
        except:
            pass
        return res

    # This method will reset some field when the currect document is being duplicated
    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'approval_list': False,
        }
        std_default.update(default)
        return super(stock_inventory, self).copy_data(cr, uid, id, default=std_default, context=context)

    _columns = {
        'approval_list': fields.one2many('approval.list', 'doc_id', 'Approval List', domain=[('model', '=', 'stock.inventory')]),
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

    #this method is used when the document is being created
    def create(self, cr, uid, vals, context=None):
        res = super(stock_inventory, self).create(cr, uid, vals, context=context)
        obj = self.pool.get('stock.inventory').browse(cr, uid, res, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'stock.inventory')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Stock Inventory model cannot be found !!!'))

        value = {
            'doc_id': res,
            'doc_name': obj.name,
            'model': model[0],
        }

        self.pool.get('approval.list').create_obj(cr, uid, value, context=context)

        return res

    #this method is used when the document is being edited
    def write(self, cr, uid, ids, vals, context=None):
        res = super(stock_inventory, self).write(cr, uid, ids, vals, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'stock.inventory')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Stock Inventory model cannot be found !!!'))

        self.pool.get('approval.list').write_obj(cr, uid, ids, model, vals, context=context)
        return res

    #this method is used to initially create a record in approval_hook when the module is being installed / upgraded
    def init(self, cr):
        model = self.pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', 'stock.inventory')])

        if not model:
            raise orm.except_orm(_('Error!'), _('Stock Inventory model cannot be found !!!'))

        value = [
            ['action_confirm', 'Confirm Inventory'],
            ['action_done', 'Validate Inventory'],
            ['action_cancel_draft', 'Set to Draft'],
            ['action_cancel_inventory', 'Cancel Inventory'],
        ]
        for obj in value:
            vals = {
                'name': obj[1],
                'model': model[0],
                'method_name': obj[0],
            }

            valid = self.pool.get('approval.hook').search(cr, SUPERUSER_ID, [('name', '=', obj[1]), ('method_name', '=', obj[0]), ('model', '=', model[0])])
            if not valid:
                self.pool.get('approval.hook').create(cr, SUPERUSER_ID, vals, context=None)

    #========================================================================================#
    #these method is re-defined to add hook_validation method when the method is being called#
    #========================================================================================#

    def action_confirm(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_confirm', context=context)
        return super(stock_inventory, self).action_confirm(cr, uid, ids, context=context)

    def action_done(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_done', context=context)
        return super(stock_inventory, self).action_done(cr, uid, ids, context=context)

    def action_cancel_draft(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_cancel_draft', context=context)
        return super(stock_inventory, self).action_cancel_draft(cr, uid, ids, context=context)

    def action_cancel_inventory(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_cancel_inventory', context=context)
        return super(stock_inventory, self).action_cancel_inventory(cr, uid, ids, context=context)

stock_inventory()


class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res_return = {}
        try:
            for obj in self.pool.get('stock.picking').browse(cr, uid, ids, context=context):
                approval_list = obj.approval_list
                for approval in approval_list:
                    if approval.approval_type == 'auto':
                        if not obj.auto_approval:
                            res_return = self.pool.get('stock.picking').write(cr, uid, obj.id, {'auto_approval': True}, context=context)
                        elif obj.auto_approval:
                            res_return = self.pool.get('stock.picking').write(cr, uid, obj.id, {'auto_approval': False}, context=context)
                res[obj.id] = res_return
        except:
            pass
        return res

    # This method will reset some field when the currect document is being duplicated
    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'approval_list': False,
        }
        std_default.update(default)
        return super(stock_picking, self).copy_data(cr, uid, id, default=std_default, context=context)

    _columns = {
        'approval_list': fields.one2many('approval.list', 'doc_id', 'Approval List', domain=[('model', 'in', ['stock.picking', 'stock.picking.in', 'stock.picking.out'])]),
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

    #this method is used when the document is being created
    def create(self, cr, uid, vals, context=None):
        res = super(stock_picking, self).create(cr, uid, vals, context=context)
        obj = self.pool.get('stock.picking').browse(cr, uid, res, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'stock.picking')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Stock Picking model cannot be found !!!'))

        value = {
            'doc_id': res,
            'doc_name': obj.name,
            'model': model[0],
        }

        self.pool.get('approval.list').create_obj(cr, uid, value, context=context)

        return res

    #this method is used when the document is being edited
    def write(self, cr, uid, ids, vals, context=None):
        res = super(stock_picking, self).write(cr, uid, ids, vals, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'stock.picking')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Stock Picking model cannot be found !!!'))

        self.pool.get('approval.list').write_obj(cr, uid, ids, model, vals, context=context)
        return res

    #this method is used to initially create a record in approval_hook when the module is being installed / upgraded
    def init(self, cr):
        model = self.pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', 'stock.picking')])
        value = [
            ['draft_force_assign', 'Confirm (IM)'],
            ['draft_validate', 'Confirm & Transfer (IM)'],
            ['force_assign', 'Force Availability (IM)'],
            ['action_process', 'Confirm & Transfer (IM)'],
            ['button_cancel', 'Cancel Transfer (IM)'],
            ['draft_validate', 'Confirm & Receive (IS)'],
            ['action_process', 'Receive (IS)'],
            ['button_cancel', 'Cancel Transfer (IS)'],
            ['stock_return_picking', 'Return Products (IS)'],
            ['draft_validate', 'Confirm & Deliver (DO)'],
            ['action_assign', 'Check Availability (DO)'],
            ['action_process', 'Deliver (DO)'],
            ['force_assign', 'Force Availability (DO)'],
            ['stock_return_picking', 'Return Products (DO)'],
            ['button_cancel', 'Cancel Transfer (DO)'],
            ['split_process', 'Split (DO)'],
            ['stock_invoice_onshipping', 'Create Invoice/Refund'],
            ['stock_return_picking', 'Reverse Transfer (IM)'],
        ]
        for obj in value:
            vals = {
                'name': obj[1],
                'model': model[0],
                'method_name': obj[0],
            }

            valid = self.pool.get('approval.hook').search(cr, SUPERUSER_ID, [('name', '=', obj[1]), ('method_name', '=', obj[0]), ('model', '=', model[0])])
            if not valid:
                self.pool.get('approval.hook').create(cr, SUPERUSER_ID, vals, context=None)

    #========================================================================================#
    #these method is re-defined to add hook_validation method when the method is being called#
    #========================================================================================#

    def draft_force_assign(self, cr, uid, ids, *args):
        if args:
            context = args[0]
        else:
            context = {}
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'draft_force_assign', context=context)
        return super(stock_picking, self).draft_force_assign(cr, uid, ids, *args)

    def draft_validate(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'draft_validate', context=context)
        return super(stock_picking, self).draft_validate(cr, uid, ids, context=context)

    def force_assign(self, cr, uid, ids, *args):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'force_assign', context=args[0])
        return super(stock_picking, self).force_assign(cr, uid, ids, *args)

    def action_process(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_process', context=context)
        return super(stock_picking, self).action_process(cr, uid, ids, context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'stock.picking', id, 'action_process', cr)

    def button_cancel(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'button_cancel', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'stock.picking', id, 'button_cancel', cr)

    def stock_return_picking(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'stock_return_picking', context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Return Shipment',
            'view_mode': 'form',
            'res_model': 'stock.return.picking',
            'src_model': 'stock.picking',
            'target': 'new',
            'key2': 'client_action_multi',
            'multi': True,
        }

    def action_assign(self, cr, uid, ids, *args):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_assign', context=args[0])
        return super(stock_picking, self).action_assign(cr, uid, ids, *args)

    def split_process(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'split_process', context=context)
        return super(stock_picking, self).split_process(cr, uid, ids, context=context)

stock_picking()


class stock_picking_in(orm.Model):
    _inherit = 'stock.picking.in'

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res_return = {}
        try:
            for obj in self.pool.get('stock.picking').browse(cr, uid, ids, context=context):
                approval_list = obj.approval_list
                for approval in approval_list:
                    if approval.approval_type == 'auto':
                        if not obj.auto_approval:
                            res_return = self.pool.get('stock.picking').write(cr, uid, obj.id, {'auto_approval': True}, context=context)
                        elif obj.auto_approval:
                            res_return = self.pool.get('stock.picking').write(cr, uid, obj.id, {'auto_approval': False}, context=context)
                res[obj.id] = res_return
        except:
            pass
        return res

    # This method will reset some field when the currect document is being duplicated
    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'approval_list': False,
        }
        std_default.update(default)
        return super(stock_picking_in, self).copy_data(cr, uid, id, default=std_default, context=context)

    _columns = {
        'approval_list': fields.one2many('approval.list', 'doc_id', 'Approval List'),
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

    #this method is used when the document is being created
    def create(self, cr, uid, vals, context=None):
        res = super(stock_picking_in, self).create(cr, uid, vals, context=context)
        obj = self.pool.get('stock.picking.in').browse(cr, uid, res, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'stock.picking')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Stock Picking In model cannot be found !!!'))

        value = {
            'doc_id': res,
            'doc_name': obj.name,
            'model': model[0],
        }

        self.pool.get('approval.list').create_obj(cr, uid, value, context=context)

        return res

    #this method is used when the document is being edited
    def write(self, cr, uid, ids, vals, context=None):
        res = super(stock_picking_in, self).write(cr, uid, ids, vals, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'stock.picking')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Stock Picking In model cannot be found !!!'))

        self.pool.get('approval.list').write_obj(cr, uid, ids, model, vals, context=context)
        return res

    #========================================================================================#
    #these method is re-defined to add hook_validation method when the method is being called#
    #========================================================================================#

    def draft_validate(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'draft_validate', context=context)
        return super(stock_picking_in, self).draft_validate(cr, uid, ids, context=context)

    def action_process(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_process', context=context)
        return super(stock_picking_in, self).action_process(cr, uid, ids, context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'stock.picking.in', id, 'action_process', cr)

    def button_cancel(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'button_cancel', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'stock.picking', id, 'button_cancel', cr)

    def stock_return_picking(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'stock_return_picking', context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Return Shipment',
            'view_mode': 'form',
            'res_model': 'stock.return.picking',
            'src_model': 'stock.picking.in',
            'target': 'new',
            'key2': 'client_action_multi',
            'multi': True,
        }

    def stock_invoice_onshipping(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'stock_invoice_onshipping', context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Draft Invoices',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'stock.invoice.onshipping',
            'src_model': 'stock.picking.in',
            'target': 'new',
            'key2': 'client_action_multi',
            'multi': True,
        }

stock_picking_in()


class stock_picking_out(orm.Model):
    _inherit = 'stock.picking.out'

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res_return = {}
        try:
            for obj in self.pool.get('stock.picking').browse(cr, uid, ids, context=context):
                approval_list = obj.approval_list
                for approval in approval_list:
                    if approval.approval_type == 'auto':
                        if not obj.auto_approval:
                            res_return = self.pool.get('stock.picking').write(cr, uid, obj.id, {'auto_approval': True}, context=context)
                        elif obj.auto_approval:
                            res_return = self.pool.get('stock.picking').write(cr, uid, obj.id, {'auto_approval': False}, context=context)
                res[obj.id] = res_return
        except:
            pass
        return res

    # This method will reset some field when the currect document is being duplicated
    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'approval_list': False,
        }
        std_default.update(default)
        return super(stock_picking_out, self).copy_data(cr, uid, id, default=std_default, context=context)

    _columns = {
        'approval_list': fields.one2many('approval.list', 'doc_id', 'Approval List'),
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

    #this method is used when the document is being created
    def create(self, cr, uid, vals, context=None):
        res = super(stock_picking_out, self).create(cr, uid, vals, context=context)
        obj = self.pool.get('stock.picking.out').browse(cr, uid, res, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'stock.picking')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Stock Picking Out model cannot be found !!!'))

        value = {
            'doc_id': res,
            'doc_name': obj.name,
            'model': model[0],
        }

        self.pool.get('approval.list').create_obj(cr, uid, value, context=context)

        return res

    #this method is used when the document is being edited
    def write(self, cr, uid, ids, vals, context=None):
        res = super(stock_picking_out, self).write(cr, uid, ids, vals, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'stock.picking')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Stock Picking Out model cannot be found !!!'))

        self.pool.get('approval.list').write_obj(cr, uid, ids, model, vals, context=context)
        return res

    #========================================================================================#
    #these method is re-defined to add hook_validation method when the method is being called#
    #========================================================================================#

    def draft_validate(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'draft_validate', context=context)
        return super(stock_picking_out, self).draft_validate(cr, uid, ids, context=context)

    def action_assign(self, cr, uid, ids, *args):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_assign', context=args[0])
        return super(stock_picking_out, self).action_assign(cr, uid, ids, *args)

    def action_process(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_process', context=context)
        return super(stock_picking_out, self).action_process(cr, uid, ids, context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'stock.picking.out', id, 'action_process', cr)

    def force_assign(self, cr, uid, ids, *args):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'force_assign', context=args[0])
        return super(stock_picking_out, self).force_assign(cr, uid, ids, *args)

    def button_cancel(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'button_cancel', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'stock.picking', id, 'button_cancel', cr)

    def stock_return_picking(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'stock_return_picking', context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Return Shipment',
            'view_mode': 'form',
            'res_model': 'stock.return.picking',
            'src_model': 'stock.picking.out',
            'target': 'new',
            'key2': 'client_action_multi',
            'multi': True,
        }

    def split_process(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'split_process', context=context)
        return super(stock_picking_out, self).split_process(cr, uid, ids, context=context)

    def stock_invoice_onshipping(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'stock_invoice_onshipping', context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Draft Invoices',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'stock.invoice.onshipping',
            'src_model': 'stock.picking.out',
            'target': 'new',
            'key2': 'client_action_multi',
            'multi': True,
        }

stock_picking_out()


class stock_return_picking(orm.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self, cr, uid, ids, context=None):
        context.update({'force_to_pass': True})
        return super(stock_return_picking, self).create_returns(cr, uid, ids, context=context)

stock_return_picking()
