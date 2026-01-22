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
from tools.translate import _


class stock_picking(orm.Model):
    _inherit = "stock.picking"

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not context:
            context = {}
        if not args:
            args = []
        args = args[:]

        res = super(stock_picking, self).name_search(cr, uid, name, args=args, operator='ilike', context=context, limit=limit)
        if name:
            ids1 = self.search(cr, uid, [('rma_number', operator, name)], limit=limit, context=context)
            ids2 = self.search(cr, uid, [('claim_id.claim_number', operator, name)], limit=limit, context=context)
            res += self.name_get(cr, uid, ids1 + ids2, context)

        return res[:limit]

    def create(self, cr, uid, vals, context=None):
        if ('name' not in vals) or (vals.get('name') == '/'):
            sequence_obj = self.pool.get('ir.sequence')
            if vals['type'] == 'internal':
                seq_obj_name = self._name
            else:
                seq_obj_name = 'stock.picking.' + vals['type']
            vals['name'] = sequence_obj.get(cr, uid, seq_obj_name, context=context)
        new_id = super(stock_picking, self).create(cr, uid, vals, context=context)
        return new_id

    def validate_receive(self, cr, uid, ids, name, args, context=None):
        """
        Returns True if all the serial number of all stock moves has been printed.
        If serial number is empty, return False.
        """
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            if _obj.claim_id:
                res[_obj.id] = True
            else:
                _line_checks = [line.id for line in _obj.move_lines if (line.state not in ['cancel'] and self._check_split(line) and line.prodlot_id and not line.prodlot_id.barcode_printed) or (line.state not in ['cancel'] and self._check_split(line) and not line.prodlot_id)]
                #_line_checks = [line.id for line in _obj.move_lines if ((line.state not in ['cancel']) and (not self._check_split(line) or (line.prodlot_id and not line.prodlot_id.barcode_printed))]
                res[_obj.id] = not bool(len(_line_checks))
                print _line_checks
        return res

    def _get_sp_from_spl(self, cr, uid, ids, context=None):
        res = []
        for _obj in self.pool.get('stock.production.lot').browse(cr, uid, ids, context=context):
            for move in _obj.move_ids:
                res.append(move.picking_id.id)

        return list(set(res))

    def _get_sp_from_sm(self, cr, uid, ids, context=None):
        res = []
        for _obj in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            res.append(_obj.picking_id.id)

        return list(set(res))

    def _get_selection(self, cr, uid, context=None):
        return self.pool.get('code.decode').get_selection_for_category(cr, uid, 'emm_claim_rma', 'claim_type_parameter', context=context)

    _columns = {
        'claim_id': fields.many2one('crm.claim', 'Claim'),
        'rma_number': fields.related('claim_id', 'rma_number', type='char', string='RMA Number', size=64, readonly=True),
        'claim_method': fields.related('claim_id', 'claim_method', type='selection', selection=_get_selection, string='Claim Method', readonly=True),
        'receive_ok': fields.function(validate_receive, method=True, type='boolean', string='OK to Receive', readonly=True,
            store={
                'stock.production.lot': (_get_sp_from_spl, ['barcode_printed'], 20),
                'stock.move': (_get_sp_from_sm, ['state'], 20),
            }),
    }

    def print_incoming_shipment(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()

        for _picking in self.browse(cr, uid, ids, context=context):
            try:
                _template = self.pool.get('ir.model.data').get_object(cr, uid, 'emm_claim_rma', 'stock_picking_in_form_template', context=context)
                _template = _template and _template.act_report_id and self.pool.get('ir.actions.report.xml').copy_data(cr, uid, _template.act_report_id.id, context=context) or False

                _datas = {
                    'ids': [_picking.id],
                }
                _template.update({'datas': _datas, 'context': ctx})
                return _template
            except:
                raise orm.except_orm(_('Error !'), _('Cannot load taxform print template!  Contact your administrator'))


class stock_picking_out(orm.Model):
    _inherit = "stock.picking.out"

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not context:
            context = {}
        if not args:
            args = []
        args = args[:]

        res = super(stock_picking_out, self).name_search(cr, uid, name, args=args, operator='ilike', context=context, limit=limit)
        if name:
            ids1 = self.search(cr, uid, [('rma_number', operator, name)], limit=limit, context=context)
            ids2 = self.search(cr, uid, [('claim_id.claim_number', operator, name)], limit=limit, context=context)
            res += self.name_get(cr, uid, ids1 + ids2, context)

        return res[:limit]

    def validate_receive(self, cr, uid, ids, name, args, context=None):
        return self.pool.get('stock.picking').validate_receive(cr, uid, ids, name, args, context=context)
        #return super(stock_picking_in, self).validate_receive(cr, uid, ids, name, args, context=context)

    def _get_sp_from_spl(self, cr, uid, ids, context=None):
        res = []
        for _obj in self.pool.get('stock.production.lot').browse(cr, uid, ids, context=context):
            for move in _obj.move_ids:
                res.append(move.picking_id.id)

        return list(set(res))

    def _get_sp_from_sm(self, cr, uid, ids, context=None):
        res = []
        for _obj in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            res.append(_obj.picking_id.id)

        return list(set(res))

    def _get_selection(self, cr, uid, context=None):
        return self.pool.get('code.decode').get_selection_for_category(cr, uid, 'emm_claim_rma', 'claim_type_parameter', context=context)

    _columns = {
        'claim_id': fields.many2one('crm.claim', 'Claim'),
        'rma_number': fields.related('claim_id', 'rma_number', type='char', string='RMA Number', size=64, readonly=True),
        'claim_method': fields.related('claim_id', 'claim_method', type='selection', selection=_get_selection, string='Claim Method', readonly=True),
        'receive_ok': fields.function(validate_receive, method=True, type='boolean', string='OK to Receive', readonly=True,
            store={
                'stock.production.lot': (_get_sp_from_spl, ['barcode_printed'], 20),
                'stock.move': (_get_sp_from_sm, ['state'], 20),
            }),
    }


class stock_picking_in(orm.Model):
    _inherit = "stock.picking.in"

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not context:
            context = {}
        if not args:
            args = []
        args = args[:]

        res = super(stock_picking_in, self).name_search(cr, uid, name, args=args, operator='ilike', context=context, limit=limit)
        if name:
            ids1 = self.search(cr, uid, [('rma_number', operator, name)], limit=limit, context=context)
            ids2 = self.search(cr, uid, [('claim_id.claim_number', operator, name)], limit=limit, context=context)
            res += self.name_get(cr, uid, ids1 + ids2, context)

        return res[:limit]

    def validate_receive(self, cr, uid, ids, name, args, context=None):
        return self.pool.get('stock.picking').validate_receive(cr, uid, ids, name, args, context=context)
        #return super(stock_picking_in, self).validate_receive(cr, uid, ids, name, args, context=context)

    def _get_sp_from_spl(self, cr, uid, ids, context=None):
        res = []
        for _obj in self.pool.get('stock.production.lot').browse(cr, uid, ids, context=context):
            for move in _obj.move_ids:
                res.append(move.picking_id.id)

        return list(set(res))

    def _get_sp_from_sm(self, cr, uid, ids, context=None):
        res = []
        for _obj in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            res.append(_obj.picking_id.id)

        return list(set(res))

    def _get_selection(self, cr, uid, context=None):
        return self.pool.get('code.decode').get_selection_for_category(cr, uid, 'emm_claim_rma', 'claim_type_parameter', context=context)

    _columns = {
        'claim_id': fields.many2one('crm.claim', 'Claim'),
        'rma_number': fields.related('claim_id', 'rma_number', type='char', string='RMA Number', size=64, readonly=True),
        'claim_method': fields.related('claim_id', 'claim_method', type='selection', selection=_get_selection, string='Claim Method', readonly=True),
        'receive_ok': fields.function(validate_receive, method=True, type='boolean', string='OK to Receive', readonly=True,
            store={
                'stock.production.lot': (_get_sp_from_spl, ['barcode_printed'], 20),
                'stock.move': (_get_sp_from_sm, ['state'], 20),
            }),
    }


class stock_production_lot(orm.Model):
    _inherit = "stock.production.lot"

    def _check_drafts(self, cr, uid, ids, context=None):
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            _draft_moves = []
            _draft_invoices = []
            for _move in _obj.move_ids or []:
                if _move.state in ['draft']:
                    _draft_moves.append(_move.id)
                    for _line in _move.sale_line_id.invoice_lines or []:
                        if _line.invoice_id and _line.invoice_id.state in ['draft']:
                            _draft_invoices.append(_line.invoice_id.id)
            res[_obj.id] = bool(len(_draft_moves) + len(_draft_invoices))
        return res
