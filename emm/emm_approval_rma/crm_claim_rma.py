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

class crm_claim(orm.Model):
    _inherit = 'crm.claim'

    def auto_approval_func(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res_return = {}
        try:
            for obj in self.pool.get('crm.claim').browse(cr, uid, ids, context=context):
                approval_list = obj.approval_list
                for approval in approval_list:
                    if approval.approval_type == 'auto':
                        if obj.auto_approval == False:
                            res_return = self.pool.get('crm.claim').write(cr, uid, obj.id, {'auto_approval': True}, context=context)
                        elif obj.auto_approval == True:
                            res_return = self.pool.get('crm.claim').write(cr, uid, obj.id, {'auto_approval': False}, context=context)
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
        return super(crm_claim, self).copy_data(cr, uid, id, default=std_default, context=context)

    _columns = {
        'approval_list': fields.one2many('approval.list', 'doc_id', 'Approval List', domain=[('model', '=', 'crm.claim')]),
        'auto_approval_func': fields.function(auto_approval_func, string='Auto Approval Function', method=True, type='boolean', readonly=True),
        'auto_approval': fields.boolean('Auto Approval', readonly=True),
    }

    _defaults = {
        'auto_approval': False,
    }

    #this method is used when the document is being created
    def create(self, cr, uid, vals, context=None):
        res =  super(crm_claim, self).create(cr, uid, vals, context=context)
        obj = self.pool.get('crm.claim').browse(cr, uid, res, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model','=','crm.claim')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Claim RMA model cannot be found !!!'))

        value = {
            'doc_id': res,
            'doc_name': obj.name,
            'model': model[0],
        }

        self.pool.get('approval.list').create_obj(cr, uid, value, context=context)

        return res

    #this method is used when the document is being edited
    def write(self, cr, uid, ids, vals, context=None):
        res = super(crm_claim, self).write(cr, uid, ids, vals, context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model','=','crm.claim')], context=context)

        if not model:
            raise orm.except_orm(_('Error!'), _('Claim RMA model cannot be found !!!'))

        self.pool.get('approval.list').write_obj(cr, uid, ids, model, vals, context=context)

        return res

    #this method is used to initially create a record in approval_hook when the module is being installed / upgraded
    def init(self, cr):
        model = self.pool.get('ir.model').search(cr, SUPERUSER_ID, [('model','=','crm.claim')])

        if not model:
            raise orm.except_orm(_('Error!'), _('Claim RMA model cannot be found !!!'))

        value = [
            ['case_close','Settle'],
            ['case_cancel','Reject'],
            ['case_open','Submit'],
            ['generate_rma', 'Generate RMA'],
            ['create_delivery','Create Delivery'],
            ['create_return', 'Create Return'],
            ['create_refund', 'Create Refund'],
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

    def case_close(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'case_close', context=None)
        return super(crm_claim, self).case_close(cr, uid, ids, context=context)

    def case_cancel(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'case_cancel', context=None)
        return super(crm_claim, self).case_cancel(cr, uid, ids, context=context)

    def case_open(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'case_open', context=None)
        return super(crm_claim, self).case_open(cr, uid, ids, context=context)

    def generate_rma(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'generate_rma', context=None)
        return super(crm_claim, self).generate_rma(cr, uid, ids, context=context)

    def create_delivery(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'create_delivery', context=None)
        return super(crm_claim, self).create_delivery(cr, uid, ids, context=context)

    def create_return(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'create_return', context=None)
        return super(crm_claim, self).create_return(cr, uid, ids, context=context)

    def create_refund(self, cr, uid, ids, context=None):
        self.pool.get('approval.list').hook_validation(cr, uid, ids, 'create_refund', context=None)
        return super(crm_claim, self).create_refund(cr, uid, ids, context=context)

crm_claim()

class claim_create_picking(orm.TransientModel):
    _inherit = 'claim.create.picking'

    def action_create_picking(self, cr, uid, ids, context=None):
        context.update({'force_to_pass': True})
        return super(claim_create_picking, self).action_create_picking(cr, uid, ids, context=context)

claim_create_picking()
