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


class code_decode(osv.osv):
    _name = 'code.decode'
    _description = 'Code Decode Table Entry'
    _rec_name = 'value'

    def get_selection(self, cr, uid, cat_id, company_ids=None, context=None):
        if company_ids is None:
            company_ids = []

        if isinstance(cat_id, (int, long)):
            cat_id = [cat_id]
        company_id_list = []
        if isinstance(company_ids, (int, long)):
            company_id_list.append(company_ids)
        elif isinstance(company_ids, list):
            if len(company_ids) > 0 and type(company_ids[0]) == tuple:
                company_ids = map(lambda e: e[0], company_ids)
        elif isinstance(company_ids, dict):
            company_id_list = list(company_ids)

        if len(company_id_list) > 0:
            ids = self.search(cr, uid, [('category', 'in', cat_id), '|', ('company_id', 'in', company_id_list), ('company_id', '=', False)], context=context)
        else:
            ids = self.search(cr, uid, [('category', 'in', cat_id)], context=context)

        res = self.read(cr, uid, ids, ['code', 'value'], context=context)
        res = [(r['code'], r['value']) for r in res]

        return res

    def get_selection_for_category(self, cr, uid, module_name, cat_name, company_ids=[], context=None):
        cat_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, module_name, cat_name)
        res = self.get_selection(cr, uid, cat_id[1], company_ids, context=context)
        return res

    def get_company_selection_for_category(self, cr, uid, module_name, cat_name, context=None):
        _user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        _coy = _user and _user.company_id and [_user.company_id.id] or []
        res = self.get_selection_for_category(cr, uid, module_name, cat_name, _coy, context=context)
        return res

    def get_code_value(self, cr, uid, cat_module, cat_name, code, context=None):
        cat_obj = self.pool.get('ir.model.data').get_object(cr, uid, cat_module, cat_name)
        code_ids = self.search(cr, uid, [('code', '=', code), ('category', '=', cat_obj.id)], context=context)
        code_obj = code_ids and self.browse(cr, uid, code_ids[0], context=context) or False
        return code_obj and code_obj.value or ''

    _columns = {
        'sequence': fields.integer('Sequence', readonly=False, required=True, select=True),
        'code': fields.char('Code', size=64, readonly=False, required=True, select=True),
        'value': fields.char('Value', size=255, readonly=False, required=True, select=True, translate=True, help="Register Document Type"),
        'category': fields.many2one('code.category', 'Code Category', readonly=False, ondelete='cascade', required=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=False),
        'pinned': fields.boolean('Pinned', readonly=True, help="This is to mark whether the code is 'pinned', i.e. cannot be deleted.  Can be used by modules to force existence of the code."),
    }

    _sql_constraints = [
        ('code_category_uniq', 'unique (code,category)', 'The code and category pair must be unique!')
    ]

    _defaults = {
        'company_id': False,
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

        return super(code_decode, self).unlink(cr, uid, ids, context=context)

code_decode()
