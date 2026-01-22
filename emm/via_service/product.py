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


class product_product(orm.Model):
    _inherit = 'product.product'

    def create(self, cr, uid, vals, context=None):
        res = super(product_product, self).create(cr, uid, vals, context=context)

        auto_create_skill_set = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.auto_create_skill_set
        if auto_create_skill_set:
            model = self.pool.get('ir.model').search(cr, uid, [('model', '=', self._name)], context=context)
            value = {
                'name': vals.get('name'),
                'model': model and model[0] or False,
                'doc_id': res,
            }
            categ_id = vals.get('categ_id')
            categ_obj = categ_id and self.pool.get('product.category').browse(cr, uid, categ_id, context=context) or False
            _srss_pool = self.pool.get('service.request.skill.set')
            if categ_obj:
                sr_skill_set_ids = _srss_pool.search(cr, uid, [('name', '=', categ_obj.name)], context=context)
                if sr_skill_set_ids:
                    value.update({'skill_parent_id': sr_skill_set_ids[0]})
                else:
                    res = self.search_create_skill_set(cr, uid, categ_obj.id, context=context)
                    value.update({'skill_parent_id': res})
            sr_skill_set_name_ids = _srss_pool.search(cr, uid, [('name', '=', value.get('name'))], context=context)
            if not sr_skill_set_name_ids:
                _srss_pool.create(cr, uid, value, context=context)
        return res

    def search_create_skill_set(self, cr, uid, parent_id, context=None):
        categ_obj = self.pool.get('product.category').browse(cr, uid, parent_id, context=context)
        # parent_obj = categ_obj.parent_id or False
        _srss_pool = self.pool.get('service.request.skill.set')
        if categ_obj:
            model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'product.category')], context=context)
            vals = {
                'name': categ_obj.name,
                'model': model and model[0] or False,
                'doc_id': categ_obj.id,
            }
            parent_sr_skill_set_ids = _srss_pool.search(cr, uid, [('name', '=', categ_obj.parent_id.name)], context=context)
            if parent_sr_skill_set_ids:
                vals.update({'skill_parent_id': parent_sr_skill_set_ids[0]})
            else:
                categ_parent_id = categ_obj.parent_id.id
                if categ_parent_id:
                    res = self.search_create_skill_set(cr, uid, categ_parent_id, context=context)
                    vals.update({'skill_parent_id': res})
        result = _srss_pool.create(cr, uid, vals, context=context)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        value = {}
        _srss_pool = self.pool.get('service.request.skill.set')
        auto_create_skill_set = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.auto_create_skill_set

        prev_obj = self.browse(cr, uid, ids[0], context=context)
        prev_name = prev_obj.name

        res = super(product_product, self).write(cr, uid, ids, vals, context=context)

        if auto_create_skill_set:
            sr_skill_set_ids = _srss_pool.search(cr, uid, [('name', '=', prev_name)], context=context)
            if sr_skill_set_ids:
                if vals.get('name') is not None:
                    value.update({'name': vals.get('name')})
                if vals.get('model') is not None:
                    value.update({'model': vals.get('model')})
                if vals.get('categ_id') is not None:
                    prod_categ = self.pool.get('product.category').browse(cr, uid, vals.get('categ_id'), context=context)
                    skill_parent_id = _srss_pool.search(cr, uid, [('name', '=', prod_categ.name)], context=context)
                    if skill_parent_id:
                        value.update({'skill_parent_id': skill_parent_id[0]})
                    else:
                        res_parent_id = self.search_create_skill_set(cr, uid, prod_categ.id, context=context)
                        value.update({'skill_parent_id': res_parent_id})
                _srss_pool.write(cr, uid, sr_skill_set_ids[0], value, context=context)
            else:
                model = self.pool.get('ir.model').search(cr, uid, [('model', '=', self._name)], context=context)
                new_obj = self.browse(cr, uid, ids[0], context=context)
                value = {
                    'name': new_obj.name,
                    'model': model and model[0] or False,
                    'doc_id': ids[0],
                }
                categ_obj = new_obj.categ_id
                if categ_obj:
                    sr_skill_set_ids = _srss_pool.search(cr, uid, [('name', '=', categ_obj.name)], context=context)
                    if sr_skill_set_ids:
                        value.update({'skill_parent_id': sr_skill_set_ids[0]})
                    else:
                        res_parent_id = self.search_create_skill_set(cr, uid, categ_obj.id, context=context)
                        value.update({'skill_parent_id': res_parent_id})
                _srss_pool.create(cr, uid, value, context=context)
        return res

product_product()


class product_category(orm.Model):
    _inherit = 'product.category'

    def create(self, cr, uid, vals, context=None):
        res = super(product_category, self).create(cr, uid, vals, context=context)

        auto_create_skill_set = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.auto_create_skill_set
        if auto_create_skill_set:
            model = self.pool.get('ir.model').search(cr, uid, [('model', '=', self._name)], context=context)
            value = {
                'name': vals.get('name'),
                'model': model and model[0] or False,
                'doc_id': res,
            }
            parent_id = vals.get('parent_id')
            _srss_pool = self.pool.get('service.request.skill.set')
            if parent_id:
                categ_obj = self.pool.get('product.category').browse(cr, uid, parent_id, context=context)
                sr_skill_set_ids = _srss_pool.search(cr, uid, [('name', '=', categ_obj.name)], context=context)
                if sr_skill_set_ids:
                    value.update({'skill_parent_id': sr_skill_set_ids[0]})
                else:
                    res = self.search_create_skill_set(cr, uid, parent_id, context=context)
                    value.update({'skill_parent_id': res})
            sr_skill_set_name_ids = _srss_pool.search(cr, uid, [('name', '=', value.get('name'))], context=context)
            if not sr_skill_set_name_ids:
                _srss_pool.create(cr, uid, value, context=context)
        return res

    def search_create_skill_set(self, cr, uid, parent_id, context=None):
        categ_obj = self.pool.get('product.category').browse(cr, uid, parent_id, context=context)
        _srss_pool = self.pool.get('service.request.skill.set')
        # parent_obj = categ_obj.parent_id
        if categ_obj:
            model = self.pool.get('ir.model').search(cr, uid, [('model', '=', 'product.category')], context=context)
            vals = {
                'name': categ_obj.name,
                'model': model and model[0] or False,
                'doc_id': parent_id,
            }
            parent_sr_skill_set_ids = _srss_pool.search(cr, uid, [('name', '=', categ_obj.parent_id.name)], context=context)
            if parent_sr_skill_set_ids:
                vals.update({'skill_parent_id': parent_sr_skill_set_ids[0]})
            else:
                categ_parent_id = categ_obj.parent_id.id
                if categ_parent_id:
                    res = self.search_create_skill_set(cr, uid, categ_parent_id, context=context)
                    vals.update({'skill_parent_id': res})
        result = _srss_pool.create(cr, uid, vals)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        value = {}
        _srss_pool = self.pool.get('service.request.skill.set')
        auto_create_skill_set = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.auto_create_skill_set

        prev_obj = self.browse(cr, uid, ids[0], context=context)
        prev_name = prev_obj.name

        res = super(product_category, self).write(cr, uid, ids, vals, context=context)

        if auto_create_skill_set:
            sr_skill_set_ids = _srss_pool.search(cr, uid, [('name', '=', prev_name)], context=context)
            if sr_skill_set_ids:
                if vals.get('name') is not None:
                    value.update({'name': vals.get('name')})
                if vals.get('parent_id') is not None:
                    prod_categ = self.pool.get('product.category').browse(cr, uid, vals.get('parent_id'), context=context)
                    skill_parent_id = _srss_pool.search(cr, uid, [('name', '=', prod_categ.name)], context=context)
                    if skill_parent_id:
                        value.update({'skill_parent_id': skill_parent_id[0]})
                    else:
                        res_parent_id = self.search_create_skill_set(cr, uid, prod_categ.id, context=context)
                        value.update({'skill_parent_id': res_parent_id})
                _srss_pool.write(cr, uid, sr_skill_set_ids[0], value, context=context)
            else:
                model = self.pool.get('ir.model').search(cr, uid, [('model', '=', self._name)], context=context)
                new_obj = self.browse(cr, uid, ids[0], context=context)
                value = {
                    'name': new_obj.name,
                    'model': model and model[0] or False,
                    'doc_id': ids[0],
                }
                parent_obj = new_obj.parent_id
                if parent_obj:
                    sr_skill_set_ids = _srss_pool.search(cr, uid, [('name', '=', parent_obj.name)], context=context)
                    if sr_skill_set_ids:
                        value.update({'skill_parent_id': sr_skill_set_ids[0]})
                    else:
                        res_parent_id = self.search_create_skill_set(cr, uid, parent_obj.id, context=context)
                        value.update({'skill_parent_id': res_parent_id})
                _srss_pool.create(cr, uid, value, context=context)
        return res

product_category()


class product_template(orm.Model):
    _inherit = 'product.template'

    _columns = {
        'additional_service_fee': fields.many2one('product.product', 'Additional Service Fee', domain=[('type','=','service')]),
    }

    _defaults = {
        'additional_service_fee': False,
    }

product_template()
