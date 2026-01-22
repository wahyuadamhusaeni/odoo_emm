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
from openerp import SUPERUSER_ID


class purchase_info(orm.Model):
    _name = 'purchase.info'
    _description = 'Purchase Order Info'

    def _get_selection(self, cr, uid, context=None):
        res_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'via_purchase_enhancements', 'purchase_parameter')
        category_id = self.pool.get('code.category').search(cr, uid, [('id', '=', res_id[1])], context=context)
        company_id = self.pool.get('res.users').browse(cr, uid, uid)['company_id']
        res = self.pool.get('code.decode').get_selection(cr, uid, category_id, company_id)
        return res

    _columns = {
        'purchase_order_id': fields.many2one('purchase.order', 'Purchase Order', ondelete='cascade', required=True, select=True),
        'parameter_id': fields.selection(_get_selection, 'Parameter', help="Parameter used"),
        'value': fields.char('Value', size=512, readonly=False, required=True, select=True, help="Parameter's value"),
    }

    _sql_constraints = [
        ('purchase_order_parameter_uniq', 'unique (purchase_order_id,parameter_id)', 'The parameter must be unique per purchase order!')
    ]

purchase_info()
