# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
#    Copyright (c) 2011 - 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

from osv import orm
from osv import fields

from tools.translate import _


class res_partner(orm.Model):
    _inherit = 'res.partner'

    def _get_param_value(self, cr, uid, ids, param_name='', context=None):
        if isinstance(ids, (long, int)):
            select = [ids]
        else:
            select = list(ids)

        res = {}
        val_obj = self.pool.get('partner.info')

        for _obj in self.browse(cr, uid, select, context=context):
            _val = False
            if param_name:
                _dom = [('partner_id', '=', _obj.id), ('parameter_id', '=', param_name)]
                val_rec_id = val_obj.search(cr, uid, _dom, context=context)
                _val = val_rec_id and val_obj.browse(cr, uid, val_rec_id[0], context=context) or False
            res[_obj.id] = _val and _val.value or ''

        if (len(select) == 1):
            res = res[select[0]]
        return res

    def _get_address(self, cr, uid, ids, addr_type='default', field='street', context=None):
        if isinstance(ids, (long, int)):
            select = [ids]
        else:
            select = list(ids)

        res = {}
        addr_obj = self.pool.get('res.partner.address')
        for _obj in self.browse(cr, uid, select, context=context):
            _dom = [('partner_id', '=', _obj.id), ('type', '=', addr_type)]
            addr_rec_id = addr_obj.search(cr, uid, _dom, context=context)
            addr = addr_rec_id and addr_obj.browse(cr, uid, addr_rec_id[0], context=context) or False
            res[_obj.id] = addr and addr[field] or ''

        if (len(select) == 1):
            res = res[select[0]]
        return res

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if not args:
            args = []
        args = args[:]

        _name_filter = False
        pos = 0
        while pos < len(args):
            if args[pos][0] == 'name' and args[pos][2]:
                _name_filter = args[pos][2]
                break
            pos += 1

        if _name_filter:
            args.insert(pos, ('partner_info.value', 'ilike', _name_filter))
            args.insert(pos, '|')

        return super(res_partner, self).search(cr, uid, args, offset, limit,
                order, context=context, count=count)

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not context:
            context = {}
        if not args:
            args = []
        args = args[:]

        if name:
            ids = self.search(cr, uid, [('ref', '=', name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('partner_info.value', 'ilike', name)] + args, limit=limit, context=context)
                if not ids:
                    ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    _columns = {
        'partner_info': fields.one2many('partner.info', 'partner_id', 'Partner Info'),
    }

res_partner()
