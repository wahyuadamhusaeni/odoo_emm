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


class add_rev_history(orm.TransientModel):
    _name = "add.rev.history"
    _rec_name = "rev_num"

    def _get_revnum(self, cr, uid, context=None):
        _obj_pool = self.pool.get("sale.revision.history")
        _active_id = context.get('active_id', False)
        res = _active_id and _obj_pool._get_next_revnum(cr, uid, order_id=_active_id, context=context) or 0

        return res

    def add_button_revision(self, cr, uid, ids, context=None):
        _obj_pool = self.pool.get('sale.revision.history')

        for wiz_consume in self.browse(cr, uid, ids, context=context):
            _vals = self.copy_data(cr, uid, wiz_consume.id, context=context)

            for _field in ['create_uid', 'create_date']:
                _vals.pop(_field, None)

            _vals.update({'rev_num': self._get_revnum(cr, uid, context=context)})
            _obj_pool.create(cr, uid, _vals, context)

        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'by_uid': fields.many2one('res.users', 'By', readonly=True),
        'date': fields.datetime('Date', readonly=True, help="This is indicative Revision Date, actual value will be obtained when the Revision is Saved."),
        'order_id': fields.many2one('sale.order', 'Sale Order', readonly=True),
        'rev_num': fields.integer('Revision #', readonly=True, help="This is indicative Revision Number, actual value will be obtained when the Revision is Saved."),
        'description': fields.text('Note', required=True),
    }

    _defaults = {
        'rev_num': _get_revnum,
        'order_id': lambda self, cr, uid, context: context.get('active_id'),
        'date': fields.datetime.now,
        'by_uid': lambda self, cr, uid, context: uid,
    }
