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


class stock_partial_picking(orm.TransientModel):
    _inherit = "stock.partial.picking"

    def do_partial(self, cr, uid, ids, context=None):
        res = super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)
        partial = self.browse(cr, uid, ids[0], context=context)
        for wizard_line in partial.move_ids:
            if wizard_line.location_dest_id != wizard_line.move_id.location_dest_id:
                wizard_line.move_id.write({'location_dest_id': wizard_line.location_dest_id.id})

        return res
