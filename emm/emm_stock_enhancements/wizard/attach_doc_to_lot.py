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


class attach_doc_to_lot(orm.TransientModel):
    _name = 'attach.doc.to.lot'

    _columns = {
        'attachment': fields.many2many('ir.attachment',
            'attach_doc_to_lot_ir_attachments_rel',
            'wizard_id', 'attachment_id', 'Attachments'),
    }

    def execute(self, cr, uid, ids, context=None):
        """
         Create a record in Draft Valuation Document from Cost Revaluation wizard
         -------------------------------------------------------------------------
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: A List of ids
         @param context: A standard dictionary
         @return: Return a id which created.
        """
        if context is None:
            context = {}

        _active_obj = context.get('active_id', False)
        if not _active_obj:
            raise orm.except_orm(_('Error !'), _("No Stock Move is selected"))

        _active_obj = self.pool.get('stock.move').browse(cr, uid, _active_obj, context=context) or False
        if not _active_obj:
            raise orm.except_orm(_('Error !'), _("No Stock Move is selected"))

        if not _active_obj.prodlot_id:
            raise orm.except_orm(_('Error !'), _("Stock Move does not have Serial Number"))

        # Only handles 1 record of the wizard
        if not ids:
            raise orm.except_orm(_('Error !'), _("No data is provided"))

        _obj = self.browse(cr, uid, ids[0], context=context)
        if _obj:
            for _file in _obj.attachment:
                _vals = {
                    'res_model': _active_obj.prodlot_id._model._name,
                    'res_id': _active_obj.prodlot_id.id
                }
                _file.write(_vals, context=context)

        return {'type': 'ir.actions.act_window_close'}

attach_doc_to_lot()
