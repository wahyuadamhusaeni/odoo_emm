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

from lxml import etree
import json

from osv import orm, fields
from openerp import netsvc
from openerp import SUPERUSER_ID

class stock_picking_in(orm.Model):
    _inherit = 'stock.picking.in'

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res = self.pool.get('stock.picking').auto_approval_func(cr, uid, ids, name, arg, context=context)
        return res

    _columns = {
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

    #this method is used to initially create a record in approval_hook when the module is being installed / upgraded
    def init(self, cr):
        model = self.pool.get('ir.model').search(cr, SUPERUSER_ID, [('model','=','stock.picking')])
        value = [
            ['action_prodlot_assign','Assign Serial Number (IS)'],
            ['print_serial_barcode','Print Barcode (IS)'],
            ['ready_for_transfer','Ready for Transfer Field (DO)'],
        ]
        for obj in value:
            vals = {
                'name': obj[1],
                'model': model[0],
                'method_name': obj[0],
            }

            valid = self.pool.get('approval.hook').search(cr, SUPERUSER_ID, [('name','=',obj[1]),('method_name','=',obj[0]),('model','=',model[0])])
            if not valid:
                self.pool.get('approval.hook').create(cr, SUPERUSER_ID, vals, context=None)

    #========================================================================================#
    #these method is re-defined to add hook_validation method when the method is being called#
    #========================================================================================#

    def action_prodlot_assign(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_prodlot_assign', context=None)
        return {
           'type': 'ir.actions.act_window',
           'name': 'Select Production Lots',
           'view_mode': 'form',
           'res_model': 'stock.picking.prodlot.assign',
           'target': 'new',
        }

    def print_serial_barcode(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'print_serial_barcode', context=None)
        return super(stock_picking_in, self).print_serial_barcode(cr, uid, ids, context=context)

stock_picking_in()

class stock_picking_out(orm.Model):
    _inherit = 'stock.picking.out'

    def hide_ready_for_transfer(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res = self.pool.get('stock.picking').hide_ready_for_transfer(cr, uid, ids, name, arg, context=context)
        return res

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res = self.pool.get('stock.picking').auto_approval_func(cr, uid, ids, name, arg, context=context)
        return res

    _columns = {
        'ready_for_transfer_visibility': fields.function(hide_ready_for_transfer, string='Ready For Transfer Visibility', method=True, type='boolean', readonly=True),
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

stock_picking_out()

class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    def hide_ready_for_transfer(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for obj in self.pool.get('stock.picking.out').browse(cr, uid, ids, context=context):
            approval_list = obj.approval_list
            for approval in approval_list:
                if approval.approval_items_id.name == 'DO 004 - Siap Kirim':
                    if approval.state in ['approved','ignore']:
                        res[obj.id] = False
                    else:
                        res[obj.id] = True
        return res

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res_return = {}
        for obj in self.pool.get('stock.picking.out').browse(cr, uid, ids, context=context):
            approval_list = obj.approval_list
            for approval in approval_list:
                if approval.approval_type == 'auto':
                    if obj.auto_approval == False:
                        res_return = self.pool.get('stock.picking.out').write(cr, uid, obj.id, {'auto_approval': True}, context=context)
                    elif obj.auto_approval == True:
                        res_return = self.pool.get('stock.picking.out').write(cr, uid, obj.id, {'auto_approval': False}, context=context)
            res[obj.id] = res_return
        return res

    _columns = {
        'ready_for_transfer_visibility': fields.function(hide_ready_for_transfer, string='Ready For Transfer Visibility', method=True, type='boolean', readonly=True),
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

    def action_prodlot_assign(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_prodlot_assign', context=None)
        return {
           'type': 'ir.actions.act_window',
           'name': 'Select Production Lots',
           'view_mode': 'form',
           'res_model': 'stock.picking.prodlot.assign',
           'target': 'new',
        }

    def print_serial_barcode(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'print_serial_barcode', context=None)
        return super(stock_picking, self).print_serial_barcode(cr, uid, ids, context=context)

stock_picking()
