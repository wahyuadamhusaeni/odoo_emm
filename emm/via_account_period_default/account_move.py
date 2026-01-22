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

from osv import orm
from openerp.osv.orm import setup_modifiers
from lxml import etree


class account_move(orm.Model):
    _inherit = 'account.move'

    def write(self, cr, uid, ids, vals, context=None):
        _new_date = vals.get('date', False)
        result = True

        if _new_date:
            # Get the period and update it as well
            pids = self.pool.get('account.period').find(cr, uid, dt=_new_date, context=context)
            if pids:
                vals.update({'period_id': pids[0]})
                # Also write it to all line_id belonging to that account_move
                _line_vals = {
                    'date': _new_date,
                    'period_id': pids[0],
                }
                for _move in self.pool.get('account.move').browse(cr, uid, ids, context=context):
                    for _line in _move.line_id:
                        # To avoid recursion from account_move_line updating, don't use ORM
                        _vals_to_write = _line_vals.copy()
                        _vals_to_write.update({'id': _line.id})
                        cr.execute("UPDATE account_move_line SET date = '%(date)s', period_id = %(period_id)d WHERE id = %(id)d" % _vals_to_write)
            if vals:
                result = super(account_move, self).write(cr, uid, ids, vals, context=context)
        else:
            # Date is not specified but surely the account_move has had date by now
            # re-write that to workaround the date default logic in account_move_line
            for _move in self.pool.get('account.move').browse(cr, uid, ids, context=context):
                # To avoid recursion from account_move_line updating, don't use ORM
                _vals_to_write = vals.copy()
                _vals_to_write.update({'date': _move.date})
                result = result and super(account_move, self).write(cr, uid, [_move.id], _vals_to_write, context=context)

        return result

    def create(self, cr, uid, vals, context=None):
        _new_date = vals.get('date', False)
        if _new_date:
            pids = self.pool.get('account.period').find(cr, uid, dt=_new_date, context=context)
            if pids:
                vals.update({'period_id': pids[0]})
        result = super(account_move, self).create(cr, uid, vals, context=context)
        return result

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        res = super(account_move, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='period_id']"):
            node.set('invisible', "1")
            setup_modifiers(node, res.get('fields', {}).get('period_id', False))
            res['arch'] = etree.tostring(doc)
        return res

account_move()


class account_move_line(orm.Model):
    _inherit = 'account.move.line'

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        res = super(account_move_line, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='period_id']"):
            node.set('invisible', "1")
            setup_modifiers(node, res.get('fields', {}).get('period_id', False))
            res['arch'] = etree.tostring(doc)
        return res

account_move_line()
