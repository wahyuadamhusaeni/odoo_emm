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
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class hr_employee(orm.Model):
    _inherit = 'hr.employee'

    # This method is used to find the earliest available date for each employee based on the task assigned
    def available_date_function(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for obj in self.pool.get('hr.employee').browse(cr, uid, ids, context=context):
            available_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            user_id = obj.user_id.id
            # Add state as filter (new, in progress)
            _task_pool = self.pool.get('project.task')
            task_ids = _task_pool.search(cr, uid, [('user_id', '=', user_id), ('date_end', '>', available_date),('state', 'not in', ['done','cancelled'])], order='date_start', context=context)
            for task in _task_pool.browse(cr, uid, task_ids, context=context):
                if available_date > task.date_start and available_date < task.date_end:
                    available_date = task.date_end
                elif available_date == task.date_start:
                    available_date = task.date_end
                elif available_date < task.date_start:
                    available_date = available_date
            res[obj.id] = available_date
        return res

    # This method is used to find the duration of days when the employee is free
    # The method will return number (in day(s)) if there is any free day between task and free if there is no task anymore after the latest task
    def available_duration_function(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for obj in self.pool.get('hr.employee').browse(cr, uid, ids, context=context):
            duration = 'Free'
            available_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            user_id = obj.user_id.id
            _task_pool = self.pool.get('project.task')
            task_ids = _task_pool.search(cr, uid, [('user_id', '=', user_id), ('date_end', '>', available_date),('state', 'not in', ['done','cancelled'])], order='date_start', context=context)
            for task in _task_pool.browse(cr, uid, task_ids, context=context):
                if available_date > task.date_start and available_date < task.date_end:
                    available_date = task.date_end
                elif available_date == task.date_start:
                    available_date = task.date_end
                elif available_date < task.date_start:
                    available_date = available_date
                    duration = str((datetime.strptime(task.date_start, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(available_date, DEFAULT_SERVER_DATETIME_FORMAT)).days)
            res[obj.id] = duration
        return res

    _columns = {
        'hr_employee_skills': fields.many2many('service.request.skill.set', 'hr_employee_sr_skill_set_rel', 'hr_employee_id', 'sr_skill_set_id', 'Employee Skills'),
        'available_date': fields.function(available_date_function, string='Earliest Available', method=True, type='datetime'),
        'available_duration': fields.function(available_duration_function, string='Duration', method=True, type='char'),
        'hit': fields.integer('Matches'),
    }

    # TODO
    def show_employee(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        employee = self.pool.get('hr.employee').browse(cr, uid, ids[0])
        # wizard_data = self.pool.get('service.task.wizard').browse(cr, uid, ids and ids[0], context=context)
        # sl_id = wizard_data.id

        view_id = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'view_employee_skills_task_form', context=context).id

        return {
            'type': 'ir.actions.act_window',
            'name': '%s' % (employee.name),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'hr.employee',
            'res_id': ids[0],
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

hr_employee()
