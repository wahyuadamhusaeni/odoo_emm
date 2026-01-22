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


class file_upload_import_wiz(orm.TransientModel):
    _name = 'file.upload.import.wiz'
    _description = 'Wizard to execute the file upload and import utility'

    def _get_config_id(self, cr, uid, context=None):
        if context is None:
            context = {}

        _config = context.get('config_xmlid', False)
        if _config:
            _config = get_object_from_xml(self, cr, uid, _config, context=context)

        return _config and _config.id or False

    _columns = {
        'config_id': fields.many2one('file.upload.import.config', 'Template Config', required=True, domain=[('model_id.model', 'ilike', 'stock')]),
        'working_folder': fields.char('Working Folder', required=True, help="A folder at the server where the files will be uploaded to and processed from."),
        'run_logs': fields.many2many('file.upload.import.log', 'fuil_wiz_run_logs_rel', 'wiz_id', 'log_id', 'Run Logs', readonly=True),
    }

    _defaults = {
        'config_id': _get_config_id,
    }

    def onchange_config_id(self, cr, uid, ids, config_id, context=None):
        res = {'value': {}}
        _pool = self.pool.get(self._columns['config_id']._obj)
        _config = config_id and _pool.browse(cr, uid, config_id, context=context) or False
        if _config:
            res['value'].update({'working_folder': _config.working_folder})
        return res

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
        assert _obj.config_id, _("No File Upload Import Configuration is specified.  Contact your Administrator!")
        assert (len(ids) > 0) and ids[0], _("No data is provided")
        assert len(ids) == 1, _("Only one wizard can be porcessed at any time.")

        _ctx = context.copy()
        _ctx.update({'working_folder': _obj.working_folder})
        logs = _obj.config_id.execute(context=_ctx)
        _obj.write({'run_logs': [(6, 0, logs.get(_obj.config_id.id, []))]})

        _view_obj = get_object_from_xml(self, cr, uid, "view_form_file_upload_import_wiz_2", context=context)
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
