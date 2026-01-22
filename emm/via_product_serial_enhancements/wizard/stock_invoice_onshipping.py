# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


class stock_invoice_onshipping(osv.osv_memory):

    _inherit = "stock.invoice.onshipping"

    _columns = {
        'group_by_product': fields.boolean("Group by product"),
    }

    _defaults = {
        'group_by_product': False,
    }

    def create_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        onshipdata_obj = self.read(cr, uid, ids, ['group_by_product'])
        ctx = context.copy()
        ctx.update({'is_group_by_product': onshipdata_obj[0]['group_by_product']})
        return super(stock_invoice_onshipping, self).create_invoice(cr, uid, ids, context=ctx)

stock_invoice_onshipping()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
