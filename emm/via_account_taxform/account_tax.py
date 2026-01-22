# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
#    Copyright (c) 2011 - 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

from osv import fields, orm


class account_tax(orm.Model):
    _inherit = "account.tax"

    def _get_tax_category(self, cr, uid, context=None):
        res = self.pool.get('code.decode').get_company_selection_for_category(cr, uid, 'via_account_taxform', 'tax_category', context=context)
        return res

    _columns = {
        'tax_category': fields.selection(_get_tax_category, 'Tax Category'),
    }

account_tax()
