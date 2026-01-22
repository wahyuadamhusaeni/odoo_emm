# -*- encoding: utf-8 -*-

##############################################################################
#
#    Vikasa Infinity Anugrah, PT
#    Copyright (c) 2011 - 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

from osv import osv, fields
from tools.translate import _


class code_category(osv.osv):
    _name = 'code.category'
    _description = 'Code Category'

    _columns = {
        'name': fields.char('Code Category', size=64, readonly=False, required=True, translate=True, select=True, help="Register Code Category"),
        'pinned': fields.boolean('Pinned', readonly=True, help="This is to mark whether the code category is 'pinned', i.e. cannot be deleted.  Can be used by modules to force existence of the code category."),
    }

    _defaults = {
        'pinned': False,
    }

    ## unlink
    #
    # unlink intercepts the main unlink function to prevent deletion of pinned record.
    #
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        if not context.get('_force_unlink', False):
            for _obj in self.browse(cr, uid, ids, context=context):
                if _obj.pinned:
                    raise osv.except_osv(_('Error !'), _('Pinned %s cannot be deleted.') % (self._description))

        return super(code_category, self).unlink(cr, uid, ids, context=context)

code_category()
