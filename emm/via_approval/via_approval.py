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

try:
    from tools.safe_eval import safe_eval
    from osv import orm, fields
    from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
except ImportError:
    import openerp
    from openerp.tools.safe_eval import safe_eval
    from openerp.osv import osv, fields
    from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
from openerp import SUPERUSER_ID


# This method is used to eval expression given
def formula_eval(expr, datatype='bool', to_str=False, globals_dict=None, locals_dict=None, mode="eval", nocopy=False):
    if locals_dict is None:
        locals_dict = {}

    locals_dict.update({
        'dt': datetime,
        'rdt': relativedelta,
        'int': int,
        'long': long,
        'float': float,
        'bool': bool,
        'float': float,
        'basestring': basestring,
        'isinstance': isinstance,
        'result': None,
    })
    _evaled = safe_eval(expr, globals_dict=globals_dict, locals_dict=locals_dict, mode="exec", nocopy=True)
    _evaled = locals_dict.get('result')
    if datatype in ['datetime']:
        if not isinstance(_evaled, datetime):
            _evaled = datetime.now()
    elif datatype in ['None']:
        _evaled = True
    else:
        _type = __builtins__.get(datatype)
        if not isinstance(_evaled, _type):
            # Use eval instead of to cater for non-simple data type
            _evaled = eval(str(_evaled))

    if to_str:
        _evaled = str(_evaled) or ''

    return _evaled


# This method is used to get time difference in days
def get_diff_time(self, cr, uid, ids, context=None):
    approval_obj = self.pool.get('approval.list').perm_read(cr, uid, ids, context=context)
    for approval in approval_obj:
        create_date = approval.get('create_date', '')
        create_date = datetime.strptime(create_date, "%Y-%m-%d %H:%M:%S.%f")
        now_date = datetime.now()
        diff_date = (now_date - create_date).days
        return diff_date


# This method will receive model_id and return the object of related model
def get_local_dict(self, cr, uid, ids, model_id, context=None):
    local_dict = {}
    model_name = self.pool.get('ir.model').browse(cr, uid, model_id, context=context).model
    obj = self.pool.get(model_name).browse(cr, uid, ids, context=context)
    local_dict.update({
        'obj': obj,
        'self': self,
        'cr': cr,
        'uid': uid,
        'ids': obj.id,
        'context': context,
        'SUPERUSER_ID': SUPERUSER_ID,
    })
    return local_dict

approval_state = [
    ('na', 'N/A'),
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('reject', 'Rejected'),
    ('ignore', 'Ignored'),
    ('passed', 'Passed'),
    ('failed', 'Failed'),
]


class approval_items(orm.Model):
    _name = 'approval.items'
    _description = 'Approval Items'

    _columns = {
        'name': fields.char('Approval Name', size=64, required=True),
        'approver': fields.many2many('res.groups', 'approval_item_group_rel', 'approval_item_id', 'group_id', 'Approver Groups', required=True),
        'approver_user': fields.many2one('res.users', 'Approver User'),
        'rule': fields.text('Rule', required=True),
        'model': fields.many2one('ir.model', 'Model', required=True),
        'description': fields.text('Description', required=True),
        'hash_code': fields.text('Hash Code', readonly=False, required=True),
        'hook': fields.many2many('approval.hook', 'approval_item_hook_rel', 'approval_item_id', 'approval_hook_id', 'Hook', required=True),
        'approval_type': fields.selection([('standard', 'Standard'), ('auto', 'Auto')], 'Approval Type', required=True),
    }

    _defaults = {
        'hash_code': 'result = True',
        'approval_type': 'standard',
    }

    # This method is used to filter hook field based on field model
    def model_change(self, cr, uid, ids, model, context=None):
        return {
            'domain': {'hook': [('model', '=', model)]}
        }

    # This method is used to filter approver_user field based on field approver
    def approver_change(self, cr, uid, ids, approver, context=None):
        users_ids = []
        groups_obj = self.pool.get('res.groups').browse(cr, uid, approver[0][2], context=context)

        for groups in groups_obj:
            for users in groups.users:
                users_ids.append(users.id)
            # users_ids = [users.id for users in groups.users]

        return {
            'domain': {'approver_user': [('id', 'in', users_ids)]}
        }

approval_items()


class approval_scheme(orm.Model):
    _name = 'approval.scheme'
    _description = 'Approval Scheme'

    _columns = {
        'name': fields.char('Scheme Name', size=64, required=True),
        'model': fields.many2one('ir.model', 'Model', required=True),
        'valid_date_to': fields.datetime('Valid To'),
        'filter': fields.text('Filter', required=True),
        'approval_scheme_line': fields.one2many('approval.scheme.line', 'approval_scheme_id', 'Approval List'),
        'sequence': fields.integer('Sequence', required=True),
    }

    # This method is used to filter approval_items_id field based on field model
    def model_change(self, cr, uid, ids, model, context=None):
        return {
            'domain': {'approval_items_id': [('model', '=', model)]}
        }

    # This method is used to update any scheme line to be the same with related approval items if any changes happened in approval item
    def update_scheme_line(self, cr, uid, ids, context=None):
        scheme_line_obj = self.pool.get('approval.scheme.line')
        scheme_line_ids = scheme_line_obj.search(cr, uid, [('approval_scheme_id', 'in', ids)], context=context)
        for scheme_line in scheme_line_obj.browse(cr, uid, scheme_line_ids, context=context):
            vals = {}
            approval_obj = scheme_line.approval_items_id
            approver_id = [approver.id for approver in approval_obj.approver]
            hook_id = [hook.id for hook in approval_obj.hook]

            vals.update({
                'model': approval_obj.model.id,
                'approval_rule': approval_obj.rule,
                'approver': [(6, 0, approver_id)],
                'approver_user': approval_obj.approver_user.id,
                'description': approval_obj.description,
                'hash_code': approval_obj.hash_code,
                'hook': [(6, 0, hook_id)],
                'approval_type': approval_obj.approval_type,
            })

            scheme_line_obj.write(cr, uid, scheme_line.id, vals, context=context)

        return True

approval_scheme()


class approval_scheme_line(orm.Model):
    _name = 'approval.scheme.line'
    _description = 'Approval Scheme Line'

    # This method is used to get any information related to given approval_items_id and return the vals as dictionary
    def update_vals(self, cr, uid, vals, context=None):
        if vals.get('approval_items_id'):
            approval_obj = self.pool.get('approval.items').browse(cr, uid, vals.get('approval_items_id'), context=context)
            approver_id = [approver.id for approver in approval_obj.approver]
            hook_id = [hook.id for hook in approval_obj.hook]

            vals.update({
                'model': approval_obj.model.id,
                'approval_rule': approval_obj.rule,
                'approver': [(6, 0, approver_id)],
                'approver_user': approval_obj.approver_user.id,
                'description': approval_obj.description,
                'hash_code': approval_obj.hash_code,
                'hook': [(6, 0, hook_id)],
                'approval_type': approval_obj.approval_type,
            })
        else:
            pass

        return vals

    # This method is used to store and write the new value when the object is created
    def create(self, cr, uid, vals, context=None):
        self.update_vals(cr, uid, vals, context=context)
        res = super(approval_scheme_line, self).create(cr, uid, vals, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        self.update_vals(cr, uid, vals, context=context)
        res = super(approval_scheme_line, self).write(cr, uid, ids, vals, context=context)
        return res

    _columns = {
        'approval_scheme_id': fields.many2one('approval.scheme', 'Approval Scheme ID', required=True, ondelete='cascade', select=True),
        'approval_items_id': fields.many2one('approval.items', 'Approval', change_default=True),
        'model': fields.many2one('ir.model', 'Model'),
        'approval_rule': fields.text('Rule'),
        'approver': fields.many2many('res.groups', 'approval_scheme_line_group_rel', 'approval_scheme_line_id', 'group_id', 'Approver'),
        'approver_user': fields.many2one('res.users', 'Approver User'),
        'approval_sequence': fields.integer('Sequence', required=False),
        'description': fields.text('Description'),
        'hash_code': fields.text('Hash Code'),
        'hook': fields.many2many('approval.hook', 'approval_scheme_line_hook_rel', 'approval_scheme_line_id', 'approval_hook_id', 'Hook'),
        'approval_type': fields.selection([('standard', 'Standard'), ('auto', 'Auto')], 'Approval Type'),
    }

    # This method is used to automatically fill certain fields when approval_items_id field is changing
    def approval_items_id_change(self, cr, uid, ids, approval_items_id, context=None):
        result = {}

        if approval_items_id:
            obj_pool = self.pool.get('approval.items').browse(cr, uid, approval_items_id, context=context)
            approver_id = [approver.id for approver in obj_pool.approver]
            hook_id = [hook.id for hook in obj_pool.hook]

            result['approval_rule'] = obj_pool.rule
            result['model'] = obj_pool.model.id
            result['approver'] = approver_id
            result['approver_user'] = obj_pool.approver_user.id
            result['description'] = obj_pool.description
            result['hash_code'] = obj_pool.hash_code
            result['hook'] = hook_id
            result['approval_type'] = obj_pool.approval_type
        else:
            pass

        return {'value': result}

approval_scheme_line()


class approval_list(orm.Model):
    _name = 'approval.list'
    _description = 'Approval List'

    # This method is used to store and write the new value when the object is created
    def create(self, cr, uid, vals, context=None):
        # If the value of approval_items_id cannot be found or zero then raise exception
        if vals.get('approval_items_id', 0) == 0 or vals.get('doc_id', 0) == 0:
            raise orm.except_orm(_('Error!'), _('The ID cannot be 0 !!!'))

        approval_items_obj = self.pool.get('approval.items').browse(cr, uid, [vals.get('approval_items_id', 0)], context=context)
        for approval_items in approval_items_obj:
            locals_dict = get_local_dict(self, cr, uid, vals.get('doc_id', 0), approval_items.model.id, context=context)

            approver_id = [approver.id for approver in approval_items.approver]

            users_ids = []
            for groups in self.pool.get('res.groups').browse(cr, uid, approver_id, context=context):
                for users in groups.users:
                    users_ids.append(users.id)
                # users_ids = [users.id for users in groups.users]

            hook_id = [hook.id for hook in approval_items.hook]

            model = approval_items.model and approval_items.model.model or ''
            doc_name = self.pool.get(str(model)).browse(cr, uid, vals.get('doc_id', 0), context=context).name

            vals.update({
                'doc_name': doc_name,
                'model': approval_items.model.id,
                'approval_rule': approval_items.rule,
                'approver': [(6, '?', approver_id)],
                'user': [(6, '?', list(set(users_ids)))],
                'approver_user': approval_items.approver_user.id,
                'approver_user_show': approval_items.approver_user.id,
                'description': approval_items.description,
                'hash_code': approval_items.hash_code,
                'hash_value': str(formula_eval(approval_items.hash_code, datatype='str', locals_dict=locals_dict, mode="eval")),
                'hook': [(6, '?', hook_id)],
                'approval_type': approval_items.approval_type,
            })

            if not context.get('exception',False):
                if approval_items.approval_type == 'standard':
                    vals.update({
                        'state': 'na',
                    })
                elif approval_items.approval_type == 'auto':
                    vals.update({
                        'state': 'failed',
                    })

                visibility_bool = formula_eval(approval_items.rule, datatype='bool', locals_dict=locals_dict, mode="eval")
                if visibility_bool and approval_items.approval_type == 'standard':
                    vals.update({
                        'state': 'pending',
                    })
                elif visibility_bool and approval_items.approval_type == 'auto':
                    vals.update({
                        'state': 'passed',
                    })

        return super(approval_list, self).create(cr, uid, vals, context=context)

    # This method is used to create a new object when a certain document is being created
    def create_obj(self, cr, uid, vals, context=None):
        if not vals:
            vals = {}
        if not context:
            context = {}

        if not context.get('approval_carry_over',False):
            temp_scheme_ids = []
            temp_scheme_ids_2 = [0]
            temp_date = '1970-01-01'
            locals_dict = get_local_dict(self, cr, uid, vals.get('doc_id', 0), vals.get('model', 0), context=context)

            # Searching any scheme with the same model
            scheme_ids = self.pool.get('approval.scheme').search(cr, uid, [('model', '=', vals.get('model', ''))], context=context)
            scheme_obj = self.pool.get('approval.scheme').browse(cr, uid, scheme_ids, context=context)

            # Checking whether the formula of the scheme is suitable with the current document or not
            for scheme in scheme_obj:
                value = formula_eval(scheme.filter, datatype='bool', locals_dict=locals_dict, mode="eval")
                if value:
                    #checking whether the scheme is valid or not (valid_date_to)
                    if scheme.valid_date_to:
                        if datetime.now() <= datetime.strptime(scheme.valid_date_to, DEFAULT_SERVER_DATETIME_FORMAT):
                            temp_scheme_ids.append(scheme.id)
                    else:
                        temp_scheme_ids.append(scheme.id)

            # Checking which scheme has the latest write_date and use the latest write_date
            scheme_obj_2 = self.pool.get('approval.scheme').perm_read(cr, uid, temp_scheme_ids, context=context)
            for scheme in scheme_obj_2:
                if temp_date < scheme.get('write_date', ''):
                    temp_date = scheme.get('write_date', '')
                    temp_scheme_ids_2[0] = scheme.get('id', '')

            #if there is any scheme which suitable with the current document
            if temp_scheme_ids_2:
                approval_ids = self.pool.get('approval.scheme.line').search(cr, uid, [('approval_scheme_id', 'in', temp_scheme_ids_2)], context=context)
                approval_obj = self.pool.get('approval.scheme.line').browse(cr, uid, approval_ids, context=context)

                approver_id = []
                hook_id = []
                for obj in approval_obj:
                    approver_id = [approval_id.id for approval_id in obj.approver]
                    users_ids = []
                    for groups in self.pool.get('res.groups').browse(cr, uid, approver_id, context=context):
                        for users in groups.users:
                            users_ids.append(users.id)
                        # users_ids = [users.id for users in groups.users]
                    hook_id = [hook.id for hook in obj.hook]

                    vals.update({
                        'scheme_id': obj.approval_scheme_id.id,
                        'scheme_name': obj.approval_scheme_id.name,
                        'scheme_filter': obj.approval_scheme_id.filter,
                        'approval_items_id': obj.approval_items_id.id,
                        'approval_rule': obj.approval_rule,
                        'approval_sequence': obj.approval_sequence,
                        'approver': [(6, '?', approver_id)],
                        'user': [(6, '?', users_ids)],
                        'approver_user': obj.approver_user.id,
                        'approver_user_show': obj.approver_user.id,
                        'description': obj.description,
                        'state': 'na',
                        'hash_code': obj.hash_code,
                        'hash_value': str(formula_eval(obj.hash_code, datatype='str', locals_dict=locals_dict, mode="eval")),
                        'hook': [(6, '?', hook_id)],
                        'approval_type': obj.approval_type,
                    })

                    if obj.approval_type == 'standard':
                        vals.update({
                            'state': 'na',
                        })
                    elif obj.approval_type == 'auto':
                        vals.update({
                            'state': 'failed',
                        })

                    visibility_bool = formula_eval(obj.approval_rule, datatype='bool', locals_dict=locals_dict, mode="eval")
                    user_ids = []
                    # If there is any specific user that has been stated, ignore the groups
                    if obj.approver_user:
                        user_ids.append(obj.approver_user.id)
                    else:
                        for group in obj.approver:
                            for user in group.users:
                                user_ids.append(user.id)
                            # user_ids = [user.id for user in group.users]

                    # If the user login eligible to approve
                    user_valid_bool = uid in list(set(user_ids))

                    #if the formula and the user approver fulfills the criteria
                    if visibility_bool and obj.approval_type == 'standard':
                        vals.update({
                            'state': 'pending',
                        })
                    elif visibility_bool and obj.approval_type == 'auto':
                        vals.update({
                            'state': 'passed',
                        })

                    self.pool.get('approval.list').create(cr, uid, vals, context=context)
        else:
            if context.get('active_id'):
                obj_pool = self.pool.get(context.get('active_model')).browse(cr, uid, context.get('active_id'), context=context)
                for approval in obj_pool.approval_list:
                    if vals.get('doc_id'):
                        context.update({'exception': True})
                        self.copy(cr, uid, approval.id, {'doc_id': vals.get('doc_id'), 'state': approval.state}, context=context)

    # This method is used when there is some changes in the related document
    def write_obj(self, cr, uid, ids, model, vals, context=None, **kwargs):
        if context is None:
            context = {}
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        approval_ids = self.pool.get('approval.list').search(cr, uid, [('doc_id', 'in', ids),('model','in',model)], context=context)
        approval_obj = self.pool.get('approval.list').browse(cr, uid, approval_ids, context=context)

        res = {}
        for obj in approval_obj:
            value = {}
            locals_dict = get_local_dict(self, cr, uid, obj.doc_id, obj.model.id, context=context)
            visibility_bool = formula_eval(obj.approval_rule, datatype='bool', locals_dict=locals_dict, mode="eval")
            hash_value = str(formula_eval(obj.hash_code, datatype='str', locals_dict=locals_dict, mode="eval"))

            user_ids = []
            # If there is any specific user that has been stated, ignore the groups
            if obj.approver_user:
                user_ids.append(obj.approver_user.id)
            else:
                for group in obj.approver:
                    for user in group.users:
                        user_ids.append(user.id)
                    # user_ids = [user.id for user in group.users]

            # If the user login eligible to approve
            user_valid_bool = uid in list(set(user_ids))

            # If the formula and the user approver fulfills the criteria
            if visibility_bool:
                # If hash value before and after edit does not match
                if obj.approval_type == 'standard':
                    if obj.state in ['approved', 'reject', 'ignore']:
                        if obj.hash_value != hash_value:
                            value.update({
                                'state': 'pending',
                                'hash_value': hash_value,
                            })
                    elif obj.state == 'na':
                        value.update({
                            'state': 'pending'
                        })
                        if obj.hash_value != hash_value:
                            value.update({
                                'hash_value': hash_value,
                            })
                    elif obj.state == 'pending':
                        if obj.hash_value != hash_value:
                            value.update({
                                'hash_value': hash_value,
                            })
                elif obj.approval_type == 'auto' and obj.state != 'ignore':
                    value.update({
                        'state': 'passed'
                    })
            else:
                if obj.state not in ['approved', 'reject', 'ignore'] and obj.approval_type == 'standard':
                    value.update({
                        'state': 'na',
                    })
                elif obj.approval_type == 'auto' and obj.state != 'ignore':
                    value.update({
                        'state': 'failed',
                    })
            # If approval type is auto then store the old and new states (either old and new same or different)
            if obj.approval_type == 'auto':
                context.update({'state_from': obj.state})
                old_state = obj.state
                new_state = value.get('state')

            # Change the state of approval list
            res = self.pool.get('approval.list').write(cr, uid, obj.id, value, context=context)

            # If approval type is auto, check the old and new states, if different, create approval audit based on both states
            if obj.approval_type == 'auto':
                if old_state != new_state:
                    self.create_audit(cr, uid, [obj.id], context=context)
        return res

    # This method is called when the object is being used / called
    def user_view_function(self, cr, uid, ids, name, arg, context=None):
        res = {}

        for obj in self.pool.get('approval.list').browse(cr, uid, ids, context=context):
            locals_dict = get_local_dict(self, cr, uid, obj.doc_id, obj.model.id, context=context)
            visibility_bool = formula_eval(obj.approval_rule, datatype='bool', locals_dict=locals_dict, mode="eval")

            user_ids = []
            user_valid_bool = False

            #if there is any specific user that has been stated, ignore the groups
            if obj.approver_user:
                user_ids.append(obj.approver_user.id)
            else:
                for group in obj.approver:
                    for user in group.users:
                        user_ids.append(user.id)
                    # user_ids = [user.id for user in group.users]

            #if the user login eligible to approve
            if uid in list(set(user_ids)) and obj.approval_type == 'standard':
                user_valid_bool = True

            #if the formula and the user approver fulfills the criteria
            if obj.approval_type == 'standard':
                res[obj.id] = visibility_bool and user_valid_bool
            elif obj.approval_type == 'auto':
                res[obj.id] = user_valid_bool

        return res

    # This method is used to create a record in approval_audit
    def create_audit(self, cr, uid, ids, context=None):
        obj_pool = self.browse(cr, uid, ids, context=context)

        for obj in obj_pool:
            approver_ids = [approver.id for approver in obj.approver]

            value = {
                'doc_id': obj.doc_id,
                'doc_name': obj.doc_name,
                'model': obj.model.id,
                'scheme_id': obj.scheme_id.id,
                'scheme_name': obj.scheme_name,
                'scheme_filter': obj.scheme_filter,
                'approval_items_id': obj.approval_items_id.id,
                'approval_rule': obj.approval_rule,
                'approval_sequence': obj.approval_sequence,
                'approver': [(6, 0, approver_ids)],
                'state_from': context.get('state_from', ''),
                'state_to': obj.state,
                'date': datetime.now(),
                'user': uid,
                'description': obj.description,
                'approval_type': obj.approval_type,
            }

            self.pool.get('approval.audit').create(cr, uid, value, context=context)
        return True

    # This method will change the state to approved and create audit record
    def approve(self, cr, uid, ids, context=None):
        obj_pool = self.pool.get('approval.list').browse(cr, uid, ids, context=context)
        for obj in obj_pool:
            context = {'state_from': obj.state}
            diff_time = get_diff_time(self, cr, uid, ids, context=context)
            _new_state = (obj.approval_type == 'standard') and 'approved' or 'passed'
            self.write(cr, uid, ids, {'state': _new_state, 'aging': str(diff_time) + ' days'}, context=context)
            return self.create_audit(cr, uid, ids, context=context)

    # This method will change the state to reject and create audit record
    def reject(self, cr, uid, ids, context=None):
        obj_pool = self.pool.get('approval.list').browse(cr, uid, ids, context=context)
        for obj in obj_pool:
            context = {'state_from': obj.state}
            diff_time = get_diff_time(self, cr, uid, ids, context=context)
            self.write(cr, uid, ids, {'state': 'reject', 'aging': str(diff_time) + ' days'}, context=context)
            return self.create_audit(cr, uid, ids, context=context)

    # This method will change the state to ignore and create audit record
    def ignore(self, cr, uid, ids, context=None):
        obj_pool = self.pool.get('approval.list').browse(cr, uid, ids, context=context)
        for obj in obj_pool:
            context = {'state_from': obj.state}
            diff_time = get_diff_time(self, cr, uid, ids, context=context)
            self.write(cr, uid, ids, {'state': 'ignore', 'aging': str(diff_time) + ' days'}, context=context)
            return self.create_audit(cr, uid, ids, context=context)

    # This method will return action windows based on the approval list choosen
    def view(self, cr, uid, ids, context=None):
        obj = self.pool.get('approval.list').browse(cr, uid, ids, context=context)
        return {
            'name': 'Approval List %s' % (obj[0].approval_items_id.name),
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'approval.audit',
            'domain': [('approval_items_id', '=', obj[0].approval_items_id.id), ('doc_id', '=', obj[0].doc_id)],
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }

    # This method will return the document view choosen by user
    def view_doc(self, cr, uid, ids, context=None):
        obj = self.pool.get('approval.list').browse(cr, uid, ids, context=context)
        doc_id = obj[0].doc_id
        doc_model = obj[0].model
        obj_pool = self.pool.get(doc_model.model).browse(cr, uid, doc_id, context=context)

        return {
            'name': '%s' % (obj_pool.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': doc_model.model,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': doc_id or False,
        }

    _columns = {
        'doc_id': fields.integer('Document ID', required=True),
        'doc_name': fields.char('Document Name', size=64, readonly=False),
        'model': fields.many2one('ir.model', 'Model', required=True),
        'scheme_id': fields.many2one('approval.scheme', 'Scheme ID', required=False),
        'scheme_name': fields.char('Scheme Name', size=64, readonly=False),
        'scheme_filter': fields.text('Scheme Filter', required=False),
        'approval_items_id': fields.many2one('approval.items', 'Approval', required=True),
        'approval_rule': fields.text('Approval Rule', readonly=False),
        'approval_sequence': fields.integer('Seq', required=False, readonly=True),
        'approver': fields.many2many('res.groups', 'approval_list_group_rel', 'approval_list_id', 'group_id', 'Approver', readonly=False),
        'user': fields.many2many('res.users', 'approval_list_users_rel', 'approval_list_id', 'user_id', 'Approver User', readonly=False),
        'approver_user': fields.many2one('res.users', 'Approver User', readonly=False),
        'approver_user_show': fields.many2one('res.users', 'Approver User', readonly=False),
        'visibility': fields.function(user_view_function, string='User View Function', method=True, type='boolean'),
        'state': fields.selection(approval_state, 'Status', readonly=True),
        'description': fields.text('Description', required=True, readonly=True),
        'hash_code': fields.text('Hash Code', readonly=True),
        'hash_value': fields.text('Hash Code', readonly=True),
        'hook': fields.many2many('approval.hook', 'approval_list_hook_rel', 'approval_list_id', 'approval_hook_id', 'Hook', readonly=False),
        'aging': fields.char('Aging (In Days)', readonly=False),
        'approval_type': fields.selection([('standard', 'Standard'), ('auto', 'Auto')], 'Approval Type', required=True),
        'user_filter': fields.boolean('User Filter'),
    }

    _defaults = {
        'approval_sequence': 100,
    }

    #this method is used to automatically fill certain fields when approval_items_id field is changing
    def approval_items_id_change(self, cr, uid, ids, approval_items_id, context=None):
        result = {}

        obj_pool = self.pool.get('approval.items').browse(cr, uid, approval_items_id, context=context)
        approver_id = [approver.id for approver in obj_pool.approver]
        result['approver'] = approver_id
        result['approver_user'] = obj_pool.approver_user.id
        result['approver_user_show'] = obj_pool.approver_user.id
        result['description'] = obj_pool.description

        return {'value': result}

    def approval_user_show_change(self, cr, uid, ids, approver_user_show, context=None):
        result = {}

        result['approver_user'] = approver_user_show

        return {'value': result}

    def approval_user_change(self, cr, uid, ids, approver_user, context=None):
        res = self.write(cr, uid, ids, {'approver_user_show': approver_user}, context=context)
        return res

    #this method is used to validate whether any approval related to the button has been approved or not
    def hook_validation(self, cr, uid, doc_id, hook_name, context=None):
        if context is None:
            context = {}
        if not isinstance(doc_id, (list, tuple)):
            doc_id = [doc_id]
        approval_ids = self.pool.get('approval.list').search(cr, uid, [('doc_id', 'in', doc_id)], context=context)
        approval_obj = self.pool.get('approval.list').browse(cr, uid, approval_ids, context=context)
        approval_hook_ids = []
        force_to_pass = context.get('force_to_pass',False)
        for approval in approval_obj:
            if approval.hook:
                for hook in approval.hook:
                    if hook.method_name == hook_name:
                        approval_hook_ids.append(approval.id)
                    if hook.method_name != 'force_assign':
                        force_to_pass = False

            approval_pool = self.pool.get('approval.list').browse(cr, uid, approval_hook_ids, context=context)
            for approval in approval_pool:
                user_ids = []
                force_to_approve = False
                if approval.approval_type == 'standard':
                    if approval.approver_user:
                        user_ids.append(approval.approver_user.id)
                    else:
                        for group in approval.approver:
                            for user in group.users:
                                user_ids.append(user.id)
                            # user_ids = [user.id for user in group.users]
                if uid in user_ids:
                    force_to_approve = True

                if force_to_pass:
                    self.pool.get('approval.list').write(cr, uid, approval.id, {'state': 'ignore'}, context=context)
                elif force_to_approve:
                    if approval.state != 'na':
                        self.pool.get('approval.list').write(cr, uid, approval.id, {'state': 'approved'}, context=context)
                elif approval.state in ['reject', 'pending']:
                    raise orm.except_orm(_('Error!'), _('This activity needs approval "%s" !!!') % (approval.approval_items_id.name))
                elif approval.state in ['failed']:
                    raise orm.except_orm(_('Error!'), _('This opertaion is prohibited by T&C "%s" !!!') % (approval.approval_items_id.name))

approval_list()


class approval_audit(orm.Model):
    _name = 'approval.audit'
    _description = 'Approval Audit'

    _columns = {
        'doc_id': fields.integer('Document ID', required=True),
        'doc_name': fields.char('Document Name', size=64, readonly=False),
        'model': fields.many2one('ir.model', 'Model', required=True),
        'scheme_id': fields.many2one('approval.scheme', 'Scheme ID', required=False),
        'scheme_name': fields.char('Scheme Name', size=64, readonly=False),
        'scheme_filter': fields.text('Scheme Filter', required=False),
        'approval_items_id': fields.many2one('approval.items', 'Approval', required=True),
        'approval_rule': fields.text('Approval Rule', readonly=False),
        'approval_sequence': fields.integer('Sequence', required=True),
        'approver': fields.many2many('res.groups', 'approval_audit_group_rel', 'approval_audit_id', 'group_id', 'Approver', readonly=False),
        'state_from': fields.selection(approval_state, 'Status From', required=True, readonly=True),
        'state_to': fields.selection(approval_state, 'Status To', required=True, readonly=True),
        'date': fields.datetime('Date', required=False, select=True),
        'user': fields.many2one('res.users', 'Approver', required=True),
        'description': fields.text('Description', required=True),
        'approval_type': fields.selection([('standard', 'Standard'), ('auto', 'Auto')], 'Approval Type', required=True),
    }
approval_audit()


class approval_hook(orm.Model):
    _name = 'approval.hook'
    _description = 'Approval Hook'

    _columns = {
        'name': fields.char('Button Name'),
        'model': fields.many2one('ir.model', 'Model'),
        'method_name': fields.char('Method Name'),
    }

approval_hook()
