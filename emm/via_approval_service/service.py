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
from openerp import SUPERUSER_ID
from openerp.tools.translate import _


class service_request(orm.Model):
    _inherit = 'service.request'

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res_return = {}
        try:
            for obj in self.pool.get('service.request').browse(cr, uid, ids, context=context):
                approval_list = obj.approval_list
                for approval in approval_list:
                    if approval.approval_type == 'auto':
                        if not obj.auto_approval:
                            res_return = self.pool.get('service.request').write(cr, uid, obj.id, {'auto_approval': True}, context=context)
                        elif obj.auto_approval:
                            res_return = self.pool.get('service.request').write(cr, uid, obj.id, {'auto_approval': False}, context=context)
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
        return super(service_request, self).copy_data(cr, uid, id, default=std_default, context=context)

    _columns = {
        'approval_list': fields.one2many('approval.list', 'doc_id', 'Approval List', domain=[('model', '=', 'service.request')]),
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

    # This method is used when the document is being created
    def create(self, cr, uid, vals, context=None):
        res = super(service_request, self).create(cr, uid, vals, context=context)
        obj = self.pool.get('service.request').browse(cr, uid, res, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'service.request')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Service Request model cannot be found !!!'))

        value = {
            'doc_id': res,
            'doc_name': obj.name,
            'model': model[0],
        }

        self.pool.get('approval.list').create_obj(cr, uid, value, context=context)

        return res

    # This method is used when the document is being edited
    def write(self, cr, uid, ids, vals, context=None):
        res = super(service_request, self).write(cr, uid, ids, vals, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'service.request')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Service Request model cannot be found !!!'))

        self.pool.get('approval.list').write_obj(cr, uid, ids, model, vals, context=context)
        return res

    # This method is used to initially create a record in approval_hook when the module is being installed / upgraded
    def init(self, cr):
        model = self.pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', 'service.request')])

        if not model:
            raise orm.except_orm(_('Error!'), _('Service Request model cannot be found !!!'))

        value = [
            ['confirm_sr', 'Confirm'],
            ['pending_sr', 'Pending'],
            ['cancel_sr', 'Cancel'],
            ['done_sr', 'Done'],
            ['assign_task', 'Create Task'],
            ['spare_parts_request', 'Request'],
            ['spare_parts_pickup', 'Pickup'],
            ['spare_parts_consume', 'Consume'],
            ['spare_parts_return', 'Return'],
            ['service_fee_execute', 'Execute'],
            ['create_invoice', 'Create Invoice'],
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

    def confirm_sr(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'confirm_sr', context=context)
        return super(service_request, self).confirm_sr(cr, uid, ids, context=context)

    def pending_sr(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'pending_sr', context=context)
        return super(service_request, self).pending_sr(cr, uid, ids, context=context)

    def cancel_sr(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'cancel_sr', context=context)
        return super(service_request, self).cancel_sr(cr, uid, ids, context=context)

    def done_sr(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'done_sr', context=context)
        return super(service_request, self).done_sr(cr, uid, ids, context=context)

    def assign_task(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'assign_task', context=context)
        return super(service_request, self).assign_task(cr, uid, ids, context=context)

    def spare_parts_request(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'spare_parts_request', context=context)
        return super(service_request, self).spare_parts_request(cr, uid, ids, context=context)

    def spare_parts_pickup(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'spare_parts_pickup', context=context)
        return super(service_request, self).spare_parts_pickup(cr, uid, ids, context=context)

    def spare_parts_consume(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'spare_parts_consume', context=context)
        return super(service_request, self).spare_parts_consume(cr, uid, ids, context=context)

    def spare_parts_return(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'spare_parts_return', context=context)
        return super(service_request, self).spare_parts_return(cr, uid, ids, context=context)

    def service_fee_execute(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'service_fee_execute', context=context)
        return super(service_request, self).service_fee_execute(cr, uid, ids, context=context)

    def create_invoice(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'create_invoice', context=context)
        return super(service_request, self).create_invoice(cr, uid, ids, context=context)

service_request()
