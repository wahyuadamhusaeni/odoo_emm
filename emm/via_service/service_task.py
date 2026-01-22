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
from openerp.tools.translate import _


class service_task_wizard(orm.TransientModel):
    _name = 'service.task.wizard'
    _description = 'Service Task Wizard'

    _columns = {
        'task_name': fields.char('Service Task Name', required=False),
        'deadline': fields.date('Next Deadline', required=False),
        'start_date': fields.datetime('Planned Start Date', required=False),
        'end_date': fields.datetime('Planned End Date', required=False),
        'planned_hours': fields.float('Planned Hour(s)'),
        'service_employee_id': fields.many2many('hr.employee', 'service_task_wizard_hr_employee_rel', 'service_task_wizard_id', 'hr_employee_id', 'Service Employee'),
        'employee_category': fields.many2many('hr.employee.category', 'service_task_wizard_hr_employee_category', 'service_task_wizard', 'hr_employee_category_id', 'Tags'),
        'sr_skill_set': fields.many2many('service.request.skill.set', 'service_task_wizard_sr_skill_set', 'service_task_wizard_id', 'sr_skill_set_id', 'Skill Set'),
        'limit': fields.integer('Employee Limit'),
    }

    _defaults = {
        'sr_skill_set': lambda self, cr, uid, context: context['sr_skill_set'],
        'employee_category': lambda self, cr, uid, context: [(6, 0, [cat.id for cat in self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.hr_employee_category])],
        'limit': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.limit,
    }

    def search_employee(self, cr, uid, ids, context=None):
        if context is None:
            return True

        employee_category = []
        sr_skill_set = []
        parent_sr_skill_set = []
        if context.get('employee_category'):
            employee_category = [cat for cat in context.get('employee_category')[0][2]]
        if context.get('sr_skill_set'):
            sr_skill_set = [skill for skill in context.get('sr_skill_set')[0][2]]
        for skill_set_obj in self.pool.get('service.request.skill.set').browse(cr, uid, context.get('sr_skill_set')[0][2], context=context):
            parent_ids = self.pool.get('service.request.skill.set').search(cr, uid, [('parent_left', '<', skill_set_obj.parent_left), ('parent_right', '>', skill_set_obj.parent_right)], context=context)
            for parent_id in parent_ids:
                parent_sr_skill_set.append(parent_id)

        # Reset all the hit in each employee
        default_employee_ids = self.pool.get('hr.employee').search(cr, uid, [], context=context)
        for hr_employee in default_employee_ids:
            self.pool.get('hr.employee').write(cr, uid, hr_employee, {'hit': 0}, context=context)

        hr_employee_ids = self.pool.get('hr.employee').search(cr, uid, ['|', ('hr_employee_skills', 'in', sr_skill_set), ('hr_employee_skills', 'in', parent_sr_skill_set)], context=context)

        # For each employee, write no of hit based on the employee skills over sr skill set
        for hr_employee in hr_employee_ids:
            employee_skill_set = [employee_skill_set.id for employee_skill_set in self.pool.get('hr.employee').browse(cr, uid, hr_employee).hr_employee_skills]
            counter = 0
            for skill in employee_skill_set:
                if skill in sr_skill_set:
                    counter = counter + 2
                elif skill in parent_sr_skill_set:
                    counter = counter + 1
            self.pool.get('hr.employee').write(cr, uid, hr_employee, {'hit': counter}, context=context)

        #find which company id that user belonged to
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        company_hit = self.pool.get('res.company').browse(cr, uid, company_id, context=context).hit
        limit = context.get('limit')

        #search employee where no of hit equals or greater than no of hit specified in the company configuration
        #and also search employee where category_ids related to category_ids which is choosed by user
        employee_hit_ids = self.pool.get('hr.employee').search(cr, uid, [('hit', '>=', company_hit), ('category_ids', 'in', employee_category), ('user_id', '!=', False)], context=context, limit=limit, order='hit DESC')

        #make relation between service task wizard and employee that has been filtered
        self.pool.get('service.task.wizard').write(cr, uid, ids[0], {'service_employee_id': [(6, 0, employee_hit_ids)]}, context=context)
        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_assign_service_task_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Task',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'service.task.wizard',
            'res_id': ids[0],
            'view_id': view_id,
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    def create_service_task(self, cr, uid, ids, context=None):
        res = {}
        obj = self.pool.get('service.task.wizard').browse(cr, uid, ids[0], context=context)
        model = self.pool.get('ir.model').search(cr, uid, [('model', '=', context.get('active_model'))], context=context)
        if context.get('hr_employee')[0][2]:
            # employee_id = context.get('hr_employee')[0][2][0]
            # task_ids = []
            employee_ids = context.get('hr_employee')[0][2]
            # employee_obj = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context).user_id.id
            for employee in self.pool.get('hr.employee').browse(cr, uid, employee_ids, context=context):
                vals = {
                    'name': obj.task_name,
                    'date_deadline': obj.deadline,
                    'date_start': obj.start_date,
                    'date_end': obj.end_date,
                    'planned_hours': obj.planned_hours,
                    'model': model[0],
                    'origin': self.pool.get('service.request').browse(cr, uid, context.get('active_id'), context=context).name,
                    'document_id': context.get('active_id'),
                    'user_id': employee.user_id.id,
                }
                new_id = self.pool.get('project.task').create(cr, uid, vals, context=context)
                res = self.pool.get('service.request').write(cr, uid, [context.get('active_id')], {'service_task': [(4, new_id)]}, context=context)
                # task_ids.append(res)

            # user_id = self.pool.get('res.users').browse(cr, uid, employee_obj, context=context)
            # raise orm.except_orm(_('Error!'), _('Error'))
            # if user_id.id:
                # vals.update({'user_id': user_id.id, })
            # else:
                # raise orm.except_orm(_('Error!'), _('The Selected Employee Does Not Have User ID !!!'))
        # res = self.pool.get('project.task').create(cr, uid, vals, context=context)
        else:
            raise orm.except_orm(_('Error!'), _('There is No Employee Selected !!!'))
        return res

service_task_wizard()
