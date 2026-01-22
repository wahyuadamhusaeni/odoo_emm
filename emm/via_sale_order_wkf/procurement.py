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

from openerp.osv import orm


class procurement_order(orm.Model):
    _inherit = "procurement.order"

    def test_cancel(self, cr, uid, ids):
        """ Tests whether state of move is cancelled or not.
        @return: True or False
        """
        temp = []
        for record in self.browse(cr, uid, ids):
            if record.move_id.sale_line_id:
                move_ids = self.pool.get('stock.move').search(cr, uid, [('sale_line_id', '=', record.move_id.sale_line_id.id)])
                temp = [move.state for move in self.pool.get('stock.move').browse(cr, uid, move_ids)]

            if 'cancel' in temp and all(state in ['done', 'cancel'] for state in temp):
                return True

        return False

procurement_order()
