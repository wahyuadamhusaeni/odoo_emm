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
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


class sale_revision_history(orm.Model):
    _name = "sale.revision.history"
    _rec_name = "rev_num"

    def _get_next_revnum(self, cr, uid, order_id=False, context=None):
        _obj = order_id and self.pool.get('sale.order').browse(cr, uid, order_id, context=context) or False
        return _obj and _obj.rev_num + 1 or 0

    def create(self, cr, uid, vals, context=None):
        _vals = vals.copy()
        _vals.update({'rev_num': self._get_next_revnum(cr, uid, vals.get('order_id', False), context=context)})
        for _field in ['create_uid', 'create_date']:
            _vals.pop(_field, None)

        return super(sale_revision_history, self).create(cr, uid, _vals, context=context)

    _columns = {
        'create_uid': fields.many2one('res.users', 'By', readonly=True),
        'create_date': fields.datetime('Date', readonly=True),
        'order_id': fields.many2one('sale.order', 'Sale Order', readonly=True),
        'rev_num': fields.integer('Revision #', required=True),
        'description': fields.text('Note', required=True),
    }

    _sql_constraints = [
        ('order_rev_num', 'UNIQUE (order_id, rev_num)', 'A revision number can only be used once in a Sales Order!')
    ]


class sale_order(orm.Model):
    _inherit = "sale.order"

    def _get_lastrev(self, cr, uid, ids, name, args, context=None):
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = {
                'rev_date': fields.datetime.now(),
                'rev_num': 0,
            }

            _revs = {}
            for _rev in _obj.revision_history:
                _revs.update({_rev.rev_num: _rev.read(['create_date', 'rev_num'])[0]})

            _max_revnum = max(_revs.keys() or [False])
            _last_rev = _revs.get(_max_revnum, {})
            if _last_rev:
                _last_rev.update({'rev_date': _last_rev.get('create_date', False)})
                _last_rev.pop('create_date', None)
                _last_rev.pop('id', None)
                res[_obj.id].update(_last_rev)

        return res

    def _get_order_from_revision(self, cr, uid, ids, context=None):
        result = {}
        for _obj in self.pool.get('sale.revision.history').browse(cr, uid, ids, context=context):
            result[_obj.order_id.id] = True
        return result.keys()

    def action_button_confirm(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)
        assert len(ids) == 1
        document = self.browse(cr, uid, ids[0], context=context)
        partner = document.partner_id
        company = document.company_id
        if not company.partner_follow_sale_order and partner.id in [line.id for line in document.message_follower_ids]:
            self.message_unsubscribe(cr, uid, ids, [partner.id], context=context)
        return res

    _columns = {
        'rev_date': fields.function(_get_lastrev, type='date', string='Last Revision Date',
            store={
                'sale.revision.history': (_get_order_from_revision, None, 20),
            },
            multi='revs'),
        'rev_num': fields.function(_get_lastrev, type='integer', string='Last Revision Number',
            store={
                'sale.revision.history': (_get_order_from_revision, None, 20),
            },
            multi='revs'),
        'revision_history': fields.one2many('sale.revision.history', 'order_id', 'Revision History', readonly=True),
    }

    _defaults = {
        'validity': lambda *a: str(date.today() + timedelta(days=7))
    }


    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(sale_order,self).onchange_partner_id(cr, uid, ids, part, context=context)
        _part=self.pool.get('res.partner').browse(cr, uid, part, context=context)
        _pl_cat = _part and _part.property_product_pricelist and _part.property_product_pricelist.pl_category or False

        if _pl_cat:
            new_domain = res.get('domain',{})
            new_domain.setdefault('pricelist_id',[('pl_category','=',_pl_cat), ('type','=','sale')])
            res.update({'domain': new_domain})
            return res

        new_domain = res.get('domain',{})
        new_domain.setdefault('pricelist_id', [('type','=','sale')])
        res.update({'domain':new_domain})
        return res

