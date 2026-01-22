# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP SA (<http://openerp.com>).
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _


class stock_partial_picking(osv.osv_memory):
    _inherit = "stock.partial.picking"

    def do_partial(self, cr, uid, ids, context=None):
        do_line_qty = {}
        wizard_line_qty = {}
        partial = self.browse(cr, uid, ids[0], context=context)
        do_obj = self.pool.get(context.get('active_model')).browse(cr, uid, context.get('active_id'), context=context)
        uom_obj = self.pool.get('product.uom')

        for move_lines in do_obj.move_lines:
            prod_id = move_lines.product_id.id
            prod_uom_standard = move_lines.product_id.uom_id.id
            prod_uom = move_lines.product_uom.id
            prod_qty = 0

            if prod_uom != prod_uom_standard:
                prod_uom_factor = uom_obj.browse(cr, uid, prod_uom, context=context).factor
                prod_uom_factor_standard = uom_obj.browse(cr, uid, prod_uom_standard, context=context).factor
                prod_qty = move_lines.product_qty / prod_uom_factor * prod_uom_factor_standard
            else:
                prod_qty = move_lines.product_qty

            if do_line_qty.get(prod_id, False):
                total_prod_qty = do_line_qty.get(prod_id) + prod_qty
                do_line_qty.update({prod_id: total_prod_qty})
            else:
                do_line_qty.update({prod_id: prod_qty})

        for wizard_line in partial.move_ids:
            prod_id = wizard_line.product_id.id
            prod_uom_standard = wizard_line.product_id.uom_id.id
            prod_uom = wizard_line.product_uom.id
            prod_qty = 0

            if prod_uom != prod_uom_standard:
                prod_uom_factor = uom_obj.browse(cr, uid, prod_uom, context=context).factor
                prod_uom_factor_standard = uom_obj.browse(cr, uid, prod_uom_standard, context=context).factor
                prod_qty = wizard_line.quantity / prod_uom_factor * prod_uom_factor_standard
            else:
                prod_qty = wizard_line.quantity

            if wizard_line_qty.get(prod_id, False):
                total_prod_qty = wizard_line_qty.get(prod_id) + prod_qty
                wizard_line_qty.update({prod_id: total_prod_qty})
            else:
                wizard_line_qty.update({prod_id: prod_qty})

        print do_line_qty
        print wizard_line_qty

        for key in wizard_line_qty.keys():
            if wizard_line_qty.get(key):
                wizard_qty = wizard_line_qty.get(key)
                do_qty = do_line_qty.get(key)
                if wizard_qty > do_qty:
                    raise osv.except_osv(_('Error!'), _('The total quantity to be delivered cannot more than total quantity in delivery order !!!'))

        return super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
