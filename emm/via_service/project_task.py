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

from osv import osv, orm, fields
from openerp.tools.translate import _


class project_task(orm.Model):
    _inherit = 'project.task'

    def _get_selection(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid)['company_id']
        res = self.pool.get('code.decode').get_selection_for_category(cr, uid, 'via_service', 'task_rating_category', company_ids=[company_id], context=None)
        return res

    _columns = {
        'origin': fields.char('Source Document'),
        'model': fields.many2one('ir.model', 'Model'),
        'document_id': fields.integer('Document ID'),
        'task_task': fields.many2many('service.request', 'service_request_project_task_rel', 'project_task_id', 'service_request_id', 'Service Requests'),
        'rating': fields.selection(_get_selection, 'Rating'),
    }

    def open_document(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        if not obj.model or not obj.document_id:
            return True

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': obj.model.model,
            'res_id': obj.document_id,
            'nodestroy': True,
            'target': 'current',
        }

    def print_service_task(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        _obj = self.pool.get('ir.model.data').get_object(cr, uid, 'via_service', 'via_webkit_form_srm', context=context)
        report_id = _obj.act_report_id and _obj.act_report_id.id or False
        if not report_id:
            raise orm.except_orm(_('Error'), _('Can\'t print service task form.'))
        res = self.pool.get('ir.actions.report.xml').copy_data(cr, uid, report_id, context=context)
        res.update({'context': context})
        return res

project_task()
