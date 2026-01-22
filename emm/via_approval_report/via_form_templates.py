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

from openerp.osv import orm


class via_form_templates(orm.Model):
    _inherit = 'via.form.templates'

    # This method override activate method of via_form_templates by adding functionality to create record for approval_hook table
    def activate(self, cr, uid, ids, context=None):
        _hook_obj = self.pool.get('approval.hook')

        for rpt in self.browse(cr, uid, ids, context=context):
            vals = {
                'name': rpt.name,
                'method_name': rpt.internal_name,
                'model': rpt.model_id.id,
            }
            # Finding the same record that has the same method_name
            hook_ids = _hook_obj.search(cr, uid, [('method_name', '=', rpt.internal_name)], context=context)

            # If there is the same record with the same method_name, update those record with the new ones. Else, create a new record
            if hook_ids:
                _hook_obj.write(cr, uid, hook_ids, vals, context=context)
            else:
                _hook_obj.create(cr, uid, vals, context=context)

        return super(via_form_templates, self).activate(cr, uid, ids, context=context)

via_form_templates()
