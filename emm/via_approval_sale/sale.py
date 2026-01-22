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


class sale_order(orm.Model):
    _inherit = 'sale.order'

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res_return = {}
        try:
            for obj in self.pool.get('sale.order').browse(cr, uid, ids, context=context):
                approval_list = obj.approval_list
                for approval in approval_list:
                    if approval.approval_type == 'auto':
                        if not obj.auto_approval:
                            res_return = self.pool.get('sale.order').write(cr, uid, obj.id, {'auto_approval': True}, context=context)
                        elif obj.auto_approval:
                            res_return = self.pool.get('sale.order').write(cr, uid, obj.id, {'auto_approval': False}, context=context)
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
        return super(sale_order, self).copy_data(cr, uid, id, default=std_default, context=context)

    _columns = {
        'approval_list': fields.one2many('approval.list', 'doc_id', 'Approval List', domain=[('model', '=', 'sale.order')]),
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

    # This method is used when the document is being created
    def create(self, cr, uid, vals, context=None):
        res = super(sale_order, self).create(cr, uid, vals, context=context)
        obj = self.pool.get('sale.order').browse(cr, uid, res, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'sale.order')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Sale Order model cannot be found !!!'))

        value = {
            'doc_id': res,
            'doc_name': obj.name,
            'model': model[0],
        }

        self.pool.get('approval.list').create_obj(cr, uid, value, context=context)

        return res

    # This method is used when the document is being edited
    def write(self, cr, uid, ids, vals, context=None):
        res = super(sale_order, self).write(cr, uid, ids, vals, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'sale.order')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Sale Order model cannot be found !!!'))

        self.pool.get('approval.list').write_obj(cr, uid, ids, model, vals, context=context)
        return res

    # This method is used to initially create a record in approval_hook when the module is being installed / upgraded
    def init(self, cr):
        model = self.pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', 'sale.order')])
        value = [
            ['action_quotation_send', 'Send by Email'],
            ['print_quotation', 'Print'],
            ['action_button_confirm', 'Confirm Sale'],
            ['action_view_invoice', 'View Invoice'],
            ['copy_quotation', 'New Copy of Quotation'],
            ['cancel', 'Cancel Quotation'],
            ['action_cancel', 'Cancel Quotation/Order'],
            ['ship_corrected', 'Ignore Exception'],
            ['invoice_corrected', 'Ignore Exception'],
            ['invoice_recreate', 'Recreate Invoice'],
            ['view_sale_advance_payment_inv', 'Create Invoice'],
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

    #==========================================================================================#
    # These method is re-defined to add hook_validation method when the method is being called #
    #==========================================================================================#

    def action_quotation_send(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_quotation_send', context=context)
        return super(sale_order, self).action_quotation_send(cr, uid, ids, context=context)

    def print_quotation(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'print_quotation', context=context)
        return super(sale_order, self).print_quotation(cr, uid, ids, context=context)

    def action_button_confirm(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_button_confirm', context=context)
        return super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)

    def action_view_invoice(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_view_invoice', context=context)
        return super(sale_order, self).action_view_invoice(cr, uid, ids, context=context)

    def copy_quotation(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'copy_quotation', context=context)
        return super(sale_order, self).copy_quotation(cr, uid, ids, context=context)

    def cancel(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'cancel', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'sale.order', id, 'cancel', cr)

    def action_cancel(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_cancel', context=context)
        return super(sale_order, self).action_cancel(cr, uid, ids, context=context)

    def ship_corrected(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'ship_corrected', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'sale.order', id, 'ship_corrected', cr)

    def invoice_corrected(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'invoice_corrected', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'sale.order', id, 'invoice_corrected', cr)

    def invoice_recreate(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'invoice_recreate', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'sale.order', id, 'invoice_recreate', cr)

    def view_sale_advance_payment_inv(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'view_sale_advance_payment_inv', context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice Order',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sale.advance.payment.inv',
            'target': 'new',
        }

sale_order()
