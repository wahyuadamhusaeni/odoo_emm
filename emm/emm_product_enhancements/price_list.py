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
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class product_search(orm.TransientModel):
    _name = "product.search"

    _columns = {
        'product': fields.many2one('product.product', 'Product', domain="[('sale_ok', '=', 'true')]", required=True),
        'partner': fields.many2one('res.partner', 'Partner', domain="[('customer', '=', 'true')]"),
        'product_pricelist': fields.many2one('product.pricelist', 'Product Pricelist'),
        'product_result': fields.one2many('product.result', 'product_search', 'Product Result'),
    }

    def onchange_partner(self, cr, uid, ids, partner, context=None):
        _val = {}
        if partner:
            _partner = self.pool.get('res.partner').browse(cr, uid, partner, context=context)
            if _partner.property_product_pricelist.id:
                _val.update({'product_pricelist': _partner.property_product_pricelist.id})
        return {'value': _val}

    def clear_parameter(self, cr, uid, ids, context=None):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Per Pricelist',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'product.search',
            'nodestroy': True,
            'target': 'inline',
            'context': context,
        }

    def search_pricelist(self, cr, uid, ids, context=None):
        _pricelist = []
        arr = []
        __partner = False
        for item in self.browse(cr, uid, ids, context=context):
            if not item.product:
                raise orm.except_orm(_('Error!'), _('Please enter the Product criteria!'))
            else:
                if item.partner:
                    _pricelist.append(item.partner.property_product_pricelist.id)
                    __partner = item.partner
                else:
                    if item.product_pricelist:
                        _pricelist.append(item.product_pricelist.id)
                    else:
                        _pricelist = self.pool.get('product.pricelist').search(cr, uid, [])

            for obj_product in self.pool.get('product.pricelist').browse(cr, uid, _pricelist, context=context):
                for obj_version in obj_product.version_id:
                    for obj_item in obj_version.items_id:
                        if obj_item.product_id and (obj_item.product_id.id == item.product.id):
                            _vals = {
                                # 'product_search': _id,
                                'product_pricelist_item': obj_item.id,
                                'product': obj_item.product_id.id
                            }
                        elif not obj_item.product_id:
                            _vals = {
                                # 'product_search': _id,
                                'product_pricelist_item': obj_item.id,
                                'product': item.product.id
                            }
                        else:
                            _vals = {}

                        result_id = False
                        if _vals:
                            result_id = self.pool.get('product.result').create(cr, uid, _vals, context)
                            arr.append(result_id)

        self.write(cr, uid, ids, {'product_result': [(6, 0, arr)]}, context=context)

        if __partner:
            if __partner.property_product_pricelist.id:
                self.write(cr, uid, ids, {'product_pricelist': __partner.property_product_pricelist.id}, context=context)
        return {'value': {'product.result': {'reload': True}}}


class product_result(orm.TransientModel):
    _name = "product.result"

    def get_price(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        ctx = context.copy()

        for _obj in self.browse(cr, uid, ids, context=context):
            ctx.update({'date': _obj.date_start})
            price = self.pool.get('product.pricelist').price_get(cr, uid, [_obj.pricelist_id.id], _obj.product.id, _obj.min_qty or 1.0, _obj.product_search.partner.id, context=ctx)
            _price = price.get(_obj.pricelist_id.id, 0.0)
            res[_obj.id] = _price
        return res

    _columns = {
        'product_search': fields.many2one('product.search', 'Product Search'),
        'product_pricelist_item': fields.many2one('product.pricelist.item', 'Product Pricelist Item'),
        'min_qty': fields.related('product_pricelist_item', 'min_quantity', string='Min Qty', type='integer'),
        'date_start': fields.related('product_pricelist_item', 'price_version_id', 'date_start', string='Start Date', type='date'),
        'date_end': fields.related('product_pricelist_item', 'price_version_id', 'date_end', string='End Date', type='date'),
        'pricelist_id': fields.related('product_pricelist_item', 'price_version_id', 'pricelist_id', string='Pricelist',  type='many2one', relation='product.pricelist'),
        'currency_id': fields.related('product_pricelist_item', 'price_version_id', 'pricelist_id', 'currency_id', string='Currency',  type='many2one', relation='res.currency'),
        'product': fields.many2one('product.product', 'Product'),
        'uom_id': fields.related('product', 'uom_id', string='UoM', type='many2one', relation='product.uom'),
        'price': fields.function(get_price, string='Price', digits_compute=dp.get_precision('Product Price')),
    }
