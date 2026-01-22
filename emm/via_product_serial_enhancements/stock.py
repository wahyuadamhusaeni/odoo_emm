# -*- encoding: utf-8 -*-
##############################################################################
#
#    Product serial module for OpenERP
#    Copyright (C) 2008 Raphaël Valyi
#    Copyright (C) 2011 Anevia S.A. - Ability to group invoice lines
#              written by Alexis Demeaulte <alexis.demeaulte@anevia.com>
#    Copyright (C) 2011-2013 Akretion - Ability to split lines on logistical units
#              written by Emmanuel Samyn
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

from openerp.osv import orm, fields


class stock_picking(orm.Model):
    _inherit = "stock.picking"

    def action_invoice_create(self, cursor, user, ids, journal_id=False,
            group=False, type='out_invoice', context=None):

        user_id = self.pool.get('res.users').browse(cursor, user, user, context=context)
        memory_group = user_id.company_id.is_group_invoice_line
        is_group_by_product = context.get('is_group_by_product', False)
        user_id.company_id.write({'is_group_invoice_line': is_group_by_product}, context=context)

        invoice_dict = super(stock_picking, self).action_invoice_create(cursor, user,
            ids, journal_id, group, type, context=context)

        if is_group_by_product:
            for picking_id in invoice_dict:
                invoice = self.pool.get('account.invoice').browse(cursor, user, invoice_dict[picking_id], context=context)
                for line in invoice.invoice_line:
                    line.write({'prod_lot_id': False}, context=context)
        user_id.company_id.write({'is_group_invoice_line': memory_group}, context=context)

        return invoice_dict


class stock_production_lot(orm.Model):
    _inherit = "stock.production.lot"

    def _last_location_id(self, cr, uid, ids, field_name, arg, context=None):
        return super(stock_production_lot, self)._last_location_id(cr, uid, ids, field_name, arg, context=context)

    def _last_location_id_search(self, cr, uid, obj, name, args, context=None):
        _not = False
        _loc_pool = self.pool.get('stock.location')
        _loc_ids = []
        _is_null = False
        for _leaf in args:
            if _leaf[0] == 'last_location_id':
                if isinstance(_leaf[-1], (int, long)):
                    _val_id = _leaf[-1]
                else: 
                    _val = _leaf[-1]

                _op = _leaf[1].strip()
                _not = (('not' in _op) or ('!' in _op) or ('<' in _op) or
                        ('>' in _op))
                if isinstance(_leaf[-1], (bool)):
                    if _leaf[1] == '=':
                        _is_null = True
                    else:
                        _loc_ids.append(0)
                elif isinstance(_leaf[-1], (int, long)):
                    _loc_ids.append(_leaf[-1])
                else: 
                    _locs = _loc_pool.name_search(cr, uid, _leaf[-1], context=context)
                    _locs = tuple([x[0] for x in _locs])
                    _loc_ids.extend(_locs)

        if _is_null:
            cr.execute(
                "SELECT DISTINCT prodlot_id "
                "FROM stock_report_prodlots "
                "WHERE location_id IS NULL AND qty > 0")
        else:
            cr.execute(
                "SELECT DISTINCT prodlot_id "
                "FROM stock_report_prodlots "
                "WHERE location_id %s IN %%s AND qty > 0 " % (_not and 'NOT' or ''),
                (tuple(_loc_ids), ))
        prodlot_ids = filter(None, map(lambda x: x[0], cr.fetchall()))
        return [('id', 'in', tuple(prodlot_ids))]

    _columns = {
        'last_location_id': fields.function(
            _last_location_id,
            fnct_search=_last_location_id_search,
            type="many2one", relation="stock.location",
            string="Last location",
            help="Display the current stock location of this production lot"),
    }
