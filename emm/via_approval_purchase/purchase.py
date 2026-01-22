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


class purchase_order(orm.Model):
    _inherit = 'purchase.order'

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res_return = {}
        try:
            for obj in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
                approval_list = obj.approval_list
                for approval in approval_list:
                    if approval.approval_type == 'auto':
                        if not obj.auto_approval:
                            res_return = self.pool.get('purchase.order').write(cr, uid, obj.id, {'auto_approval': True}, context=context)
                        elif obj.auto_approval:
                            res_return = self.pool.get('purchase.order').write(cr, uid, obj.id, {'auto_approval': False}, context=context)
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
        return super(purchase_order, self).copy_data(cr, uid, id, default=std_default, context=context)

    _columns = {
        'approval_list': fields.one2many('approval.list', 'doc_id', 'Approval List', domain=[('model', '=', 'purchase.order')]),
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

    #this method is used when the document is being created
    def create(self, cr, uid, vals, context=None):
        res = super(purchase_order, self).create(cr, uid, vals, context=context)
        obj = self.pool.get('purchase.order').browse(cr, uid, res, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'purchase.order')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Purchase Order model cannot be found !!!'))

        value = {
            'doc_id': res,
            'doc_name': obj.name,
            'model': model[0],
        }

        self.pool.get('approval.list').create_obj(cr, uid, value, context=context)

        return res

    #this method is used when the document is being edited
    def write(self, cr, uid, ids, vals, context=None):
        res = super(purchase_order, self).write(cr, uid, ids, vals, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'purchase.order')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Purchase Order model cannot be found !!!'))

        self.pool.get('approval.list').write_obj(cr, uid, ids, model, vals, context=context)
        return res

    #this method is used to initially create a record in approval_hook when the module is being installed / upgraded
    def init(self, cr):
        model = self.pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', 'purchase.order')])

        if not model:
            raise orm.except_orm(_('Error!'), _('Purchase Order model cannot be found !!!'))

        value = [
            ['wkf_send_rfq', 'Send by Email'],
            ['print_quotation', 'Print'],
            ['wkf_confirm_order', 'Confirm Order'],
            ['action_cancel_draft', 'Set to Draft'],
            ['action_cancel', 'Cancel Order'],
            ['purchase_cancel', 'Cancel Order'],
            ['picking_ok', 'Manually Corrected'],
            ['invoice_ok', 'Manually Corrected'],
            ['purchase_confirm', 'Confirm Order'],
            ['purchase_approve', 'Approve Order'],
            ['view_picking', 'Receive Products'],
            ['view_invoice', 'Receive Invoice'],
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

    def wkf_send_rfq(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'wkf_send_rfq', context=context)
        return super(purchase_order, self).wkf_send_rfq(cr, uid, ids, context=context)

    def print_quotation(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'print_quotation', context=context)
        return super(purchase_order, self).print_quotation(cr, uid, ids, context=context)

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'wkf_confirm_order', context=context)
        return super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)

    def action_cancel_draft(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_cancel_draft', context=context)
        return super(purchase_order, self).action_cancel_draft(cr, uid, ids, context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_cancel', context=context)
        return super(purchase_order, self).action_cancel(cr, uid, ids, context=context)

    def purchase_cancel(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'purchase_cancel', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_cancel', cr)

    def picking_ok(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'picking_ok', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'purchase.order', id, 'picking_ok', cr)

    def invoice_ok(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'invoice_ok', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'purchase.order', id, 'invoice_ok', cr)

    def purchase_confirm(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'purchase_confirm', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_confirm', cr)

    def purchase_approve(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'purchase_approve', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_approve', cr)

    def view_picking(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'view_picking', context=context)
        return super(purchase_order, self).view_picking(cr, uid, ids, context=context)

    def view_invoice(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'view_invoice', context=context)
        return super(purchase_order, self).view_invoice(cr, uid, ids, context=context)

purchase_order()
