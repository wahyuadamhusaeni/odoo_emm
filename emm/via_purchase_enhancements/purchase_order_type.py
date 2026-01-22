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


class purchase_order_type(orm.Model):
    _name = 'purchase.order.type'
    _description = 'Purchase Order Type'

    _columns = {
        'name': fields.char('Type', size=64, readonly=False, required=True, translate=True, select=True, help="Type of Purchase Order"),
        'company_id': fields.many2one('res.company', 'Company', required=True, select=True),
        'sequence_id': fields.many2one('ir.sequence', 'Sequence', readonly=False, required=True, help="Sequence to be used by the Purchase Order Type", domain=[("code", "=", "purchase.order.type")]),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.order.type', context=context),
    }

purchase_order_type()
