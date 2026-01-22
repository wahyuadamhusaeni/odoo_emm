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

from openerp.osv import fields, orm
from openerp.tools.translate import _


class product_category(orm.Model):
    _inherit = 'product.category'

    _columns = {
        'code': fields.char('Category Code', size=16, required=True),
    }

    def check_code(self, cr, uid, ids, context=None):
        param_pool = self.pool.get('ir.config_parameter')
        param_id = param_pool.search(cr, uid, [('key', '=', 'product_category.is_unique')], context=context)
        param_browse = param_pool.browse(cr, uid, param_id, context=context)
        is_unique = param_browse[0].value

        category_pool = self.pool.get('product.category')
        self_pool = self.browse(cr, uid, ids, context=context)
        new_category = self_pool
        _ids = category_pool.search(cr, uid, [], context=context)
        _category = category_pool.browse(cr, uid, _ids, context=context)

        for _code in new_category:
            if is_unique == "system":
                category = _category
            elif is_unique == "siblings":
                category = []
                for line in _category:
                    if line.parent_id.id == _code.parent_id.id:
                        category.append(line)
            else:
                return True
            for line in category:
                    if line.code == _code.code and line.id != _code.id:
                        return False
            return True

    _constraints = [
        (check_code, 'Category Code could not be same with other Category Code(s)', ['Category Code']),
    ]


class stock_config_settings(orm.TransientModel):
    _inherit = 'stock.config.settings'

    _columns = {
        'category_code_is_unique': fields.selection([('system', 'System-wide'), ('siblings', 'Among Siblings')], 'Product Category Code Is Unique'),
    }

    def get_default_is_unique(self, cr, uid, fields, context=None):
        key = 'product_category.is_unique'
        is_unique_value = self.pool.get('ir.config_parameter').get_param(cr, uid, key, context=context)
        return {'category_code_is_unique': is_unique_value}

    def set_default_is_unique(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        is_unique_pool = self.pool.get('ir.config_parameter')
        key = 'product_category.is_unique'
        value = config.category_code_is_unique
        is_unique_pool.set_param(cr, uid, key, value, context=context)
