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
from via_account_taxform.account_taxform import account_taxform


class account_taxform_create_new_sequence(orm.TransientModel):
    """
    This wizard will create new sequences for all selected taxforms
    """
    _name = "account.taxform.create_new_sequence"
    _description = "Create sequences for the selected taxforms"

    _columns = {
        'trx_code': fields.char('Transaction Code', size=3),
        'branch_code': fields.selection(account_taxform._columns['branch_code'].selection, 'Branch Code'),
    }

    def create_new_sequence(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        data = self.pool.get('account.taxform.create_new_sequence').browse(cr, uid, ids[0], context=context)
        _taxform_ids = context.get(('active_ids'), [])
        result = self.pool.get('account.taxform').action_create_new_sequence(cr, uid, _taxform_ids, data.trx_code, data.branch_code, context=context)
        return result

account_taxform_create_new_sequence()
