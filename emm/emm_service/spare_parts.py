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
from openerp.tools.translate import _


class spare_parts_wizard(orm.TransientModel):
    _inherit = "spare.parts.wizard"

    def create_request(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        context.update({'set_default_warehouse': True})
        return super(spare_parts_wizard, self).create_request(cr, uid, ids, context=context)

    def create_pickup(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        context.update({'set_default_warehouse': True})
        return super(spare_parts_wizard, self).create_pickup(cr, uid, ids, context=context)

    def create_return(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        context.update({'set_default_warehouse': True})
        return super(spare_parts_wizard, self).create_return(cr, uid, ids, context=context)


class stock_picking(orm.Model):
    _inherit = "stock.picking"

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}

        if context.get('set_default_warehouse', False) and vals.get('service_id', False):
            _move_ids = vals.get('move_lines', [])
            _move_ids = _move_ids and _move_ids[0][2] or []
            _move_ids = _move_ids and _move_ids[0] or False
            _move = self.pool.get('stock.move').browse(cr, uid, _move_ids, context=context)
            _src_whse = _move.location_id and _move.location_id.get_warehouse(context=context).get(_move.location_id.id, []) or []
            _dest_whse = _move.location_dest_id and _move.location_dest_id.get_warehouse(context=context).get(_move.location_dest_id.id, []) or []

            vals.update({
                'source_warehouse': _src_whse and _src_whse[0] or False,
                'dest_warehouse': _dest_whse and _dest_whse[0] or False,
            })

        return super(stock_picking, self).create(cr, uid, vals, context=context)
