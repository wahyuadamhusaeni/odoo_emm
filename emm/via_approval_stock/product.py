# -*- encoding: utf-8 -*-
###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2014 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
#
###############################################################################

from osv import orm, fields
from openerp.tools.translate import _


class product_product(orm.Model):
    _inherit = "product.product"

    def percentage_validation(self, cr, uid, ids, limit_delivery, vals=None, context=None):
        if limit_delivery == 'percentage':
            if ids:
                for product in self.browse(cr, uid, ids, context=context):
                    if vals.get('limit_percentage'):
                        limit_percentage = vals.get('limit_percentage')
                    else:
                        limit_percentage = self.browse(cr, uid, product.id, context=context).limit_percentage
            else:
                limit_percentage = vals.get('limit_percentage', 0.00)
            if limit_percentage > 100 or limit_percentage < 0:
                raise orm.except_orm(_('Error !!!'), _('Percentage of Limit Quantity is not valid'))
        elif limit_delivery == 'fix_qty':
            if ids:
                for product in self.browse(cr, uid, ids, context=context):
                    if vals.get('limit_qty'):
                        limit_qty = vals.get('limit_qty')
                    else:
                        limit_qty = self.browse(cr, uid, product.id, context=context).limit_qty
            else:
                limit_qty = vals.get('limit_qty', 0.00)
            if limit_qty < 0:
                raise orm.except_orm(_('Error !!!'), _('Limit Quantity is not valid'))

    def create(self, cr, uid, vals, context=None):
        limit_delivery = vals.get('limit_delivery', False)
        self.percentage_validation(cr, uid, False, limit_delivery, vals, context=context)
        return super(product_product, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        for product in self.browse(cr, uid, ids, context=context):
            if vals.get('limit_delivery'):
                limit_delivery = vals.get('limit_delivery')
            else:
                limit_delivery = self.browse(cr, uid, product.id, context=context).limit_delivery
            self.percentage_validation(cr, uid, ids, limit_delivery, vals, context=context)
        return super(product_product, self).write(cr, uid, ids, vals, context=context)

    def _get_selection(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid)['company_id']
        res = self.pool.get('code.decode').get_selection_for_category(cr, uid, 'via_approval_stock', 'product_limit_category', company_ids=[company_id], context=None)
        return res

    _columns = {
        'limit_delivery': fields.selection(_get_selection, 'Limit Delivery'),
        'limit_qty': fields.float('Limit Quantity'),
        'limit_percentage': fields.float('Limit Quantity'),
    }
