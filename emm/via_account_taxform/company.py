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


class res_company(orm.Model):
    _inherit = 'res.company'

    _columns = {
        'legal_id': fields.many2one('res.company', 'Legal Entity',
            help="Company that represent the legal entity. This company will held the sequence used for the tax form."),
        'user_id': fields.many2one('res.users', 'Taxform User', help='User that is used to access the information from the Legal Entity.'),
    }

    def get_taxform_sequence(self, cr, uid, ids, context=None):
        res = {}
        if not context:
            context = {}
        if isinstance(ids, (list, tuple, dict, )):
            select = list(ids)
        else:
            select = [ids]

        company_pool = self.pool.get('res.company')
        seq_pool = self.pool.get('ir.sequence')
        _seq_code_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'via_account_taxform', 'seq_type_taxform')
        _seq_code = self.pool.get('ir.sequence.type').browse(cr, uid, _seq_code_id, context=context)

        for _obj in company_pool.browse(cr, uid, select, context=context):
            _lcoy = _obj.legal_id or _obj
            _uid = _obj.user_id and _obj.user_id.id or False

            _seq_ids = seq_pool.search(cr, _uid, [('company_id', '=', _lcoy.id), ('code', '=', _seq_code.code)], context=context)
            res[_obj.id] = _seq_ids and _seq_ids[0] or False

        return isinstance(ids, (int, long, )) and res[ids] or res

res_company()
