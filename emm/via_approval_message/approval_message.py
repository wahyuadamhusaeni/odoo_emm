# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 - 2015 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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
from via_approval.via_approval import get_local_dict, formula_eval
from openerp import SUPERUSER_ID


class approval_items(orm.Model):
    _inherit = 'approval.items'

    _columns = {
        'notification': fields.boolean('Notification'),
        'notification_approved': fields.boolean('Approved'),
        'notification_rejected': fields.boolean('Rejected'),
        'notification_ignored': fields.boolean('Ignored'),
        'notification_reset': fields.boolean('Reset'),
    }

    _defaults = {
        'notification': False,
    }

approval_items()


class approval_list(orm.Model):
    _inherit = 'approval.list'

    def write_obj(self, cr, uid, ids, model, vals, old_value=None, new_value=None, context=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        else:
            pass

        approval_list_ids = self.pool.get('approval.list').search(cr, uid, [('doc_id', 'in', ids), ('model', 'in', model)], context=context)
        for approval in self.pool.get('approval.list').browse(cr, uid, approval_list_ids, context=context):
            locals_dict = get_local_dict(self, cr, uid, approval.doc_id, approval.model.id, context=context)
            locals_dict.update({
                'old_value': old_value and old_value.get(approval.doc_id, {}) or {},
                'new_value': new_value and new_value.get(approval.doc_id, {}) or {},
                'approval_obj': approval,
            })
            visibility_bool = formula_eval(approval.approval_rule, datatype='bool', locals_dict=locals_dict, mode="eval")
            hash_value = str(formula_eval(approval.hash_code, datatype='str', locals_dict=locals_dict, mode="eval"))

            message = {}

            if approval.hash_value != hash_value and approval.approval_type == 'standard':
                if visibility_bool:
                    message = {'state': 'pending'}
                else:
                    message = {'state': 'na'}
            else:
                pass

            # Create a message when variable message is not False
            if message.get('state', False):
                self.create_message(cr, SUPERUSER_ID, [approval.id], message.get('state'), context=context)
            else:
                pass

        return super(approval_list, self).write_obj(cr, uid, ids, model, vals, old_value=old_value, new_value=new_value, context=context)

    # This method will automatically create message regarding the action of the user on the approval
    def create_message(self, cr, uid, ids, action, context=None):
        res = {}
        body = ""
        for approval_list in self.browse(cr, uid, ids, context=context):
            if approval_list.approval_items_id.notification:
                if action in ['pending', 'na'] and approval_list.approval_items_id.notification_reset:
                    if approval_list.state in ['approved', 'reject', 'ignore']:
                        body = _("<p>Approval " + str(approval_list.approval_items_id.name) + " state has been reset due to different hash value.</p>")
                    else:
                        return True
                elif action == 'approved' and approval_list.approval_items_id.notification_approved or action == 'rejected' and approval_list.approval_items_id.notification_rejected or action == 'ignored' and approval_list.approval_items_id.notification_ignored:
                    body = _("<p>Approval " + str(approval_list.approval_items_id.name) + " has been " + str(action) + ".</p>")

                # Getting the subtype from company configuration else put the subtype to be false
                default_message_type = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.default_message_type
                if default_message_type:
                    if default_message_type == 'message':
                        subtype = 'mail.mt_comment'
                    else:
                        subtype = False
                else:
                    subtype = False

                context.update({'thread_model': approval_list.model.model})
                if body:
                    res = self.pool.get('mail.thread').message_post(cr, uid, approval_list.doc_id, body=body, type='comment', subtype=subtype, context=context)
                else:
                    pass
            else:
                pass
        return res

    # This method will change the state to approved and create audit record
    def approve(self, cr, uid, ids, context=None):
        res = super(approval_list, self).approve(cr, uid, ids, context=context)
        self.create_message(cr, uid, ids, 'approved', context=context)
        return res

    # This method will change the state to reject and create audit record
    def reject(self, cr, uid, ids, context=None):
        res = super(approval_list, self).reject(cr, uid, ids, context=context)
        self.create_message(cr, uid, ids, 'rejected', context=context)
        return res

    # This method will change the state to ignore and create audit record
    def ignore(self, cr, uid, ids, context=None):
        res = super(approval_list, self).ignore(cr, uid, ids, context=context)
        self.create_message(cr, uid, ids, 'ignored', context=context)
        return res

approval_list()
