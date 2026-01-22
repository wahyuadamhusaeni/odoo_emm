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

from osv import osv, fields


class product_pricelist (osv.osv):
    _inherit = 'product.pricelist'
    _description = 'Add pricelist category'

    def _get_selection(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid)['company_id']
        res = self.pool.get('code.decode').get_selection_for_category(cr, uid, 'emm_product_enhancements', 'pricelist_category', company_ids=[company_id], context=None)
        return res

    _columns = {
        'pl_category': fields.selection(_get_selection, 'Category', required=True, help="Used to group price-list of the same nature"),
    }
