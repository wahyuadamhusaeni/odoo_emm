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

from datetime import datetime as DT
from lxml import etree

from openerp import netsvc
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp


class claim_picking_move_memory(orm.TransientModel):
    _name = "claim.picking.move.memory"
    _rec_name = 'product_id'

    _columns = {
        'wizard_id': fields.many2one('claim.create.picking', string="Wizard"),
        'move_id': fields.many2one('stock.move', "Move"),
        'prodlot_id': fields.related('move_id', 'prodlot_id', type='many2one', relation='stock.production.lot', string='Serial Number', readonly=True),
        'product_id': fields.related('move_id', 'product_id', type='many2one', relation='product.product', string='Product', readonly=True),
        'quantity': fields.float("Quantity", digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'uom_id': fields.many2one('product.uom', string="UoM", required=True),
    }


class claim_create_picking(orm.TransientModel):
    _name = 'claim.create.picking'
    _description = 'Create Picking'

    _columns = {
        'source_location': fields.many2one('stock.location', string='Source Location', required=True,
            help="Location where the returned products are from."),
        'dest_location': fields.many2one('stock.location', string='Dest. Location', required=True,
            help="Location where the system will stock the returned products."),
        'product_return_moves': fields.one2many('claim.picking.move.memory', 'wizard_id', 'Moves to Return'),
    }

    # Get default source location
    def _get_source_location(self, cr, uid, context=None):
        """
        Return the default location to be used as source.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param context: A standard dictionary
        @return:
            For an outoing shippment, use the selected warehouse stock location.
            For an incoming shippment, use the customer stock property.
        """
        loc_id = False
        if context is None:
            context = {}

        if context.get('picking_type') == 'out':
            _wh_id = context.get('warehouse_id', False)
            loc_id = _wh_id and self.pool.get('stock.warehouse').read(
                cr, uid, _wh_id, ['lot_stock_id'],
                context=context).get('lot_stock_id', False) or False
            loc_id = loc_id and loc_id[0] or False
        elif context.get('partner_id'):
            _rp_id = context.get('partner_id', False)
            loc_id = _rp_id and self.pool.get('res.partner').read(
                cr, uid, _rp_id, ['property_stock_customer'],
                context=context).get('property_stock_customer', False) or False
            loc_id = loc_id and loc_id[0] or False
        return loc_id

    # Get default destination location
    def _get_dest_location(self, cr, uid, context=None):
        """
        Return the default location to be used as destination.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param context: A standard dictionary
        @return:
            For an outoing shippment, use the customer stock property
            For an incoming shippment, use the common destination for all
            selected moves, returning None if different.
        """
        if context is None:
            context = {}
        loc_id = False
        if context.get('picking_type') == 'out' and context.get('partner_id'):
            loc_id = self.pool.get('res.partner').read(
                cr, uid, context.get('partner_id'),
                ['property_stock_customer'],
                context=context)['property_stock_customer'][0]
        elif context.get('picking_type') == 'in' and context.get('active_id', False):
            # Add the case of return to supplier !
            loc_id = []
            _claim_id = context.get('active_id', False)
            if _claim_id:
                _claim = self.pool.get('crm.claim').browse(cr, uid, _claim_id, context=context)
                loc_id = [line.location_id and line.location_id.id or False for line in _claim.claimed_moves]
                loc_id = (len(loc_id) == 1) and loc_id[0] or False
        return loc_id

    def default_get(self, cr, uid, fields, context=None):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary with default values for all field in ``fields``
        """
        result1 = []
        if context is None:
            context = {}
        res = super(claim_create_picking, self).default_get(cr, uid, fields, context=context)
        _claim_id = context.get('active_id', False)
        _picking_type = context.get('picking_type', False)
        if _claim_id:
            _claim = self.pool.get('crm.claim').browse(cr, uid, _claim_id, context=context)
            for line in _claim.claimed_moves:
                if _picking_type and _picking_type == 'out':
                    _prodlot_id = False
                else:
                    _prodlot_id = line.prodlot_id and line.prodlot_id.id or False
                result1.append({
                    'move_id': line.id,
                    'prodlot_id': _prodlot_id,
                    'product_id': line.product_id.id,
                    'quantity': line.product_qty,
                    'uom_id': line.product_uom and line.product_uom.id or False,
                })
            if result1 and 'product_return_moves' in fields:
                res.update({'product_return_moves': result1})

        return res

    _defaults = {
        'source_location': _get_source_location,
        'dest_location': _get_dest_location,
    }

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}

        res = super(claim_create_picking, self).fields_view_get(cr, user, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//button[@name='action_create_picking']")
        _type = context.get('picking_type' '')
        _model = 'stock.picking{0}'.format(_type and '.{0}'.format(_type) or '')
        _model = self.pool.get(_model)._description
        for node in nodes:
            node.set('string', _('Create {0}').format(_model))
        res['arch'] = etree.tostring(doc)
        return res

    def action_create_picking(self, cr, uid, ids, context=None):
        """
         Creates return picking.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: List of ids selected
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        if context is None:
            context = {}

        assert (len(ids) > 0) and ids[0], _("No data is provided.  Please contact your administrator.")
        assert (len(ids) == 1), _("Only one wizard can be processed at any time.  Please contact your administrator.")

        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        uom_obj = self.pool.get('product.uom')
        wf_service = netsvc.LocalService("workflow")
        claim_id = context.get('active_id', False)

        claim = claim_id and self.pool.get('crm.claim').browse(cr, uid, claim_id, context=context) or False
        data = self.browse(cr, uid, ids[0], context=context)
        date_cur = DT.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        set_invoice_state_to_none = True
        returned_lines = 0

        _move_ids = [_line.move_id for _line in data.product_return_moves]
        _valid_move_ids = []
        for _move in _move_ids:
            if not _move:
                raise orm.except_orm(_('Warning !'), _("You have manually created product lines, please delete them to proceed"))
            if _move and _move.state in ['done']:
                _valid_move_ids.append(_move.id)

        if not _valid_move_ids:
            raise orm.except_orm(_('Warning!'), _("No products to return (only lines in Done state and not fully returned yet can be returned)!"))

        _picking_ids = list(set([_move and _move.picking_id and _move.picking_id.id for _move in _move_ids]))
        assert (len(_picking_ids) == 1), _("Only Moves from one Stock Picking can be processed at any time.  Please amend your input data.")
        pick = pick_obj.browse(cr, uid, _picking_ids[0], context=context)

        if pick.state not in ['done', 'confirmed', 'assigned']:
            raise orm.except_orm(_('Warning!'), _("You may only return pickings that are Confirmed, Available or Done!"))

       # Create new picking for returned products
        new_type = context.get('picking_type', 'in')
        _new_model = 'stock.picking.{0}'.format(new_type)
        _model_name = self.pool.get(_new_model)._description
        note = 'RMA {0}'.format(_model_name)
        new_pick_name = self.pool.get('ir.sequence').get(cr, uid, _new_model, context=context)

        _location_id = data.source_location.id
        _location_dest_id = data.dest_location.id
        new_picking = pick_obj.copy(cr, uid, pick.id, {
            'name': _('{0}-{1}-{2}').format(new_pick_name, pick.name, note),
            'move_type': 'one',  # direct
            'move_lines': [],
            'state': 'draft',
            'type': new_type,
            'date': date_cur,

            # Additional fields for RMA Claim
            'invoice_state': 'none',
            'origin': claim and claim.claim_number or '',
            'partner_id': claim and claim.partner_id and claim.partner_id.id or False,
            'claim_id': claim and claim.id or False,
            'location_id': _location_id,
            'location_dest_id': _location_dest_id,
        })

        _picking_type = context.get('picking_type', False)
        ctx = context.copy()
        ctx.update({'runworkflow': False})
        for v in data.product_return_moves:
            new_qty = v.quantity
            move = v.move_id
            new_location = move.location_dest_id.id

            if new_qty:
                returned_lines += 1
                if _picking_type and _picking_type == 'out':
                    new_move = move_obj.copy(cr, uid, move.id, {
                        'product_qty': new_qty,
                        'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id, new_qty, move.product_uos.id),
                        'picking_id': new_picking,
                        'state': 'draft',
                        'location_id': new_location,
                        'location_dest_id': _location_dest_id,
                        'date': date_cur,
                        'prodlot_id': False,

                        # Additional fields for RMA Claim
                        'priority': '0',
                        'date_expected': date_cur,
                    }, context=ctx)
                else:
                    new_move = move_obj.copy(cr, uid, move.id, {
                        'product_qty': new_qty,
                        'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id, new_qty, move.product_uos.id),
                        'picking_id': new_picking,
                        'state': 'draft',
                        'location_id': new_location,
                        'location_dest_id': _location_dest_id,
                        'date': date_cur,

                        # Additional fields for RMA Claim
                        'priority': '0',
                        'date_expected': date_cur,
                    }, context=ctx)

                move_obj.write(cr, uid, [move.id], {'move_history_ids2': [(4, new_move)]}, context=context)
        if not returned_lines:
            raise orm.except_orm(_('Warning!'), _("Please specify at least one non-zero quantity."))

        if set_invoice_state_to_none:
            pick_obj.write(cr, uid, [pick.id], {'invoice_state': 'none'}, context=context)

        wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
        if new_type == 'in':
            # Do not force assign if it is not stock.picking.in
            pick_obj.force_assign(cr, uid, [new_picking], context)

        return {
            'res_id': new_picking,
            'name': _('Returned Picking'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': _new_model,
            'type': 'ir.actions.act_window',
            'context': context,
        }
