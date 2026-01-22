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

from openerp.osv import orm, fields
from openerp.tools.translate import _
from via_base_enhancements.models import get_object_from_xml


class file_upload_import_all_wiz(orm.TransientModel):
    _name = 'file.upload.import.all.wiz'
    _description = 'Wizard to execute active file upload and import configurations'

    def _get_all_active_config_ids(self, cr, uid, context=None):
        _active_config_ids = self.pool.get('file.upload.import.config').search(cr, uid, [], context=context)
        return _active_config_ids

    _columns = {
        'config_ids': fields.many2many('file.upload.import.config', 'fuic_wizall_config_ids_rel', 'wiz_id', 'config_id', 'Configurations', readonly=True),
        'run_logs': fields.many2many('file.upload.import.log', 'fuil_wizall_run_logs_rel', 'wiz_id', 'log_id', 'Run Logs', readonly=True),
    }

    _defaults = {
        'config_ids': _get_all_active_config_ids,
    }

    def execute(self, cr, uid, ids, context=None):
        """
        Execute the given File Upload and Import Configuration
        -------------------------------------------------------------------------
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: A List of ids
        @param context: A standard dictionary
        @return: Open the result window.
        """
        if context is None:
            context = {}

        _obj = self.browse(cr, uid, ids[0], context=context)
        assert _obj, _("Cannot read the data.")

        # Only handles 1 record of the wizard
        assert (len(ids) > 0) and ids[0], _("No data is provided")
        assert len(ids) == 1, _("Only one wizard can be porcessed at any time.")

        # Run all selected configurations
        ctx = context.copy()
        ctx.update({'raise_exception': False})
        for _config in _obj.config_ids:
            logs = _config.execute(context=ctx)
            _obj.write({'run_logs': [(4, x) for x in list(set(logs.get(_config.id, [])))]})

        _view_obj = get_object_from_xml(self, cr, uid, "view_form_file_upload_import_all_wiz_2", context=context)
        if _view_obj:
            return {
                'name': _("File Upload Process Completed"),
                'view_mode': _view_obj.type or 'form',
                'view_type': _view_obj.type or 'form',
                'res_model': _view_obj.model or '',
                'views': [(_view_obj.id or False, 'form')],
                'res_id': _obj and _obj.id or False,
                'type': 'ir.actions.act_window',
                'nodestroy': False,
                'target': 'new',
                'domain': '[]',
                'context': context
            }
        else:
            return {'type': 'ir.actions.act_window_close'}

    def close(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
