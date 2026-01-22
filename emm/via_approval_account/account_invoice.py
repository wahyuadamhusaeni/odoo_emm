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


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res_return = {}
        try:
            for obj in self.pool.get('account.invoice').browse(cr, uid, ids, context=context):
                approval_list = obj.approval_list
                for approval in approval_list:
                    if approval.approval_type == 'auto':
                        if not obj.auto_approval:
                            res_return = self.pool.get('account.invoice').write(cr, uid, obj.id, {'auto_approval': True}, context=context)
                        elif obj.auto_approval:
                            res_return = self.pool.get('account.invoice').write(cr, uid, obj.id, {'auto_approval': False}, context=context)
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
        return super(account_invoice, self).copy_data(cr, uid, id, default=std_default, context=context)

    _columns = {
        'approval_list': fields.one2many('approval.list', 'doc_id', 'Approval List', domain=[('model', '=', 'account.invoice')]),
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

    #this method is used when the document is being created
    def create(self, cr, uid, vals, context=None):
        res = super(account_invoice, self).create(cr, uid, vals, context=context)
        obj = self.pool.get('account.invoice').browse(cr, uid, res, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'account.invoice')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Account Invoice model cannot be found !!!'))

        value = {
            'doc_id': res,
            'doc_name': obj.name,
            'model': model[0],
        }

        self.pool.get('approval.list').create_obj(cr, uid, value, context=context)

        return res

    #this method is used when the document is being edited
    def write(self, cr, uid, ids, vals, context=None):
        res = super(account_invoice, self).write(cr, uid, ids, vals, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'account.invoice')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Account Invoice model cannot be found !!!'))

        self.pool.get('approval.list').write_obj(cr, uid, ids, model, vals, context=context)

        return res

    #this method is used to initially create a record in approval_hook when the module is being installed / upgraded
    def init(self, cr):
        model = self.pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', 'account.invoice')])

        if not model:
            raise orm.except_orm(_('Error!'), _('Account Invoice model cannot be found !!!'))

        value = [
            ['action_invoice_sent', 'Send by Email'],
            ['invoice_print', 'Print'],
            ['invoice_print', 'Print Invoice'],
            ['invoice_open', 'Validate'],
            ['invoice_cancel', 'Cancel Invoice'],
            ['action_cancel_draft', 'Reset to Draft'],
            ['invoice_pay_customer', 'Register Payment'],
            ['account_invoice_refund', 'Ask Refund'],
            ['account_state_open', 'Re-Open'],
            ['invoice_proforma2', 'PRO-FORMA'],
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

    def action_invoice_sent(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_invoice_sent', context=context)
        return super(account_invoice, self).action_invoice_sent(cr, uid, ids, context=context)

    def invoice_print(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'invoice_print', context=context)
        return super(account_invoice, self).invoice_print(cr, uid, ids, context=context)

    def invoice_open(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'invoice_open', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'account.invoice', id, 'invoice_open', cr)

    def invoice_cancel(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'invoice_cancel', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'account.invoice', id, 'invoice_cancel', cr)

    def action_cancel_draft(self, cr, uid, ids, *args):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_cancel_draft', context=args[0])
        return super(account_invoice, self).action_cancel_draft(cr, uid, ids, *args)

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'invoice_pay_customer', context=context)
        return super(account_invoice, self).invoice_pay_customer(cr, uid, ids, context=context)

    def account_invoice_refund(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'account_invoice_refund', context=context)
        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'account', 'view_account_invoice_refund', context=context).id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Refund Invoice',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'account.invoice.refund',
            'target': 'new',
            'view_id': view_id,
        }

    def account_state_open(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'account_invoice_refund', context=context)
        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'account', 'view_account_state_open', context=context).id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Account State Open',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'account.state.open',
            'target': 'new',
            'view_id': view_id,
            'context': {},
        }

    def invoice_proforma2(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'invoice_proforma2', context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            return wf_service.trg_validate(uid, 'account.invoice', id, 'invoice_proforma2', cr)

account_invoice()


class account_period(orm.Model):
    _inherit = 'account.period'

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res_return = {}
        try:
            for obj in self.pool.get('account.period').browse(cr, uid, ids, context=context):
                approval_list = obj.approval_list
                for approval in approval_list:
                    if approval.approval_type == 'auto':
                        if not obj.auto_approval:
                            res_return = self.pool.get('account.period').write(cr, uid, obj.id, {'auto_approval': True}, context=context)
                        elif obj.auto_approval:
                            res_return = self.pool.get('account.period').write(cr, uid, obj.id, {'auto_approval': False}, context=context)
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
        return super(account_period, self).copy_data(cr, uid, id, default=std_default, context=context)

    _columns = {
        'approval_list': fields.one2many('approval.list', 'doc_id', 'Approval List', domain=[('model', '=', 'account.period')]),
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

    #this method is used when the document is being created
    def create(self, cr, uid, vals, context=None):
        res = super(account_period, self).create(cr, uid, vals, context=context)
        obj = self.pool.get('account.period').browse(cr, uid, res, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'account.period')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Account Period model cannot be found !!!'))

        value = {
            'doc_id': res,
            'doc_name': obj.name,
            'model': model[0],
        }

        self.pool.get('approval.list').create_obj(cr, uid, value, context=context)

        return res

    #this method is used when the document is being edited
    def write(self, cr, uid, ids, vals, context=None):
        res = super(account_period, self).write(cr, uid, ids, vals, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'account.period')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Account Period model cannot be found !!!'))

        self.pool.get('approval.list').write_obj(cr, uid, ids, model, vals, context=context)
        return res

    #this method is used to initially create a record in approval_hook when the module is being installed / upgraded
    def init(self, cr):
        model = self.pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', 'account.period')])

        if not model:
            raise orm.except_orm(_('Error!'), _('Account Period model cannot be found !!!'))

        value = [
            ['action_draft', 'Re-Open Period'],
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

    def action_draft(self, cr, uid, ids, *args):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'action_draft', context=args[0])
        return super(account_period, self).action_draft(cr, uid, ids, *args)

account_period()
