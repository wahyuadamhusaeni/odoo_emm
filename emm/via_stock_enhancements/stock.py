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

from osv import osv, fields, orm


class stock_move(osv.osv):

    _inherit = 'stock.move'
    _columns = {
        'account_move_id': fields.many2many('account.move', 'stock_move_account_move_rel', 'stock_move_id', 'account_move_id', 'Journal Entries', readonly=True),
    }

    def _create_product_valuation_moves(self, cr, uid, move, context=None):
        """
        Generate the appropriate accounting moves if the product being moves is subject
        to real_time valuation tracking, and the source or destination location is
        a transit location or is outside of the company.
        """
        if move.product_id.valuation == 'real_time':  # FIXME: product valuation should perhaps be a property?
            if context is None:
                context = {}
            src_company_ctx = dict(context, force_company=move.location_id.company_id.id)
            dest_company_ctx = dict(context, force_company=move.location_dest_id.company_id.id)
            account_moves = []
            # Outgoing moves (or cross-company output part)
            if move.location_id.company_id \
                and (move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal'
                     or move.location_id.company_id != move.location_dest_id.company_id):
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, src_company_ctx)
                reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid, move, src_company_ctx)
                account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_valuation, acc_dest, reference_amount, reference_currency_id, context))]

            # Incoming moves (or cross-company input part)
            if move.location_dest_id.company_id \
                and (move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal'
                     or move.location_id.company_id != move.location_dest_id.company_id):
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, dest_company_ctx)
                reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid, move, src_company_ctx)
                account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_src, acc_valuation, reference_amount, reference_currency_id, context))]

            move_obj = self.pool.get('account.move')
            _account_move_to_link = []
            for j_id, move_lines in account_moves:
                move_id = move_obj.create(cr, uid, {
                    'journal_id': j_id,
                    'line_id': move_lines,
                    'ref': move.picking_id and move.picking_id.name})
                _account_move_to_link.append(move_id)
            self.write(cr, uid, [move.id], {'account_move_id': [(6, 0, _account_move_to_link)]}, context=context)

stock_move()


class stock_picking(orm.Model):
    _inherit = "stock.picking"

    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        res = super(stock_picking, self).do_partial(cr, uid, ids, partial_datas, context=context)
        _ids = []
        for key in res.keys():
            _ids.append(res[key].get('delivered_picking', False))
        for picking in self.browse(cr, uid, _ids, context=context):
            picking_code = (picking.type != 'internal') and ('stock.picking.%s' % (picking.type)) or 'stock.picking'
            if not picking.name:
                self.write(cr, uid, [picking.id],
                        {
                            'name': self.pool.get('ir.sequence').get(cr, uid, picking_code),
                        })
        return res
