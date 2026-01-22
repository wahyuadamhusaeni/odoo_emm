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

from lxml import etree
import json

from osv import orm, osv, fields
from tools.translate import _
from openerp import netsvc
from datetime import datetime as DT

import logging

DELIVER_WIDGETS = {
    'draft_validate': 'button',
    'action_process': 'button',
}

__module__ = __package__.split('.')[-1]


class product_product(orm.Model):
    _inherit = "product.product"

    _sql_constraints = [
        ('default_code', 'unique (default_code)', 'Product Internal Reference must be unique !'),
    ]


class stock_location(orm.Model):
    _name = "stock.location"
    _inherit = "stock.location"

    def get_warehouse(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple, dict, )):
            select = list(ids)
        else:
            select = [ids]

        res = {}
        warehouse_obj = self.pool.get('stock.warehouse')
        for _obj in self.browse(cr, uid, list(set(select)), context=context):
            _loc_ids = self.search(cr, uid, [('parent_left', '<=', _obj.parent_left), ('parent_right', '>=', _obj.parent_right)], context=context)
            _dom = [
                '|', ('lot_input_id', 'in', _loc_ids),
                '|', ('lot_stock_id', 'in', _loc_ids),
                ('lot_output_id', 'in', _loc_ids),
            ]
            res[_obj.id] = warehouse_obj.search(cr, uid, _dom, context=context)
        return res

    def get_children(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple, dict, )):
            select = list(ids)
        else:
            select = [ids]

        res = {}
        location_ids = list(set(select))
        for _id in location_ids:
            fin_loc_ids = []
            fin_loc_ids.append(_id)
            fin_loc_ids.extend(self.search(cr, uid, [('id', 'child_of', _id)], context=context))
            res[_id] = list(set(fin_loc_ids))
        return res


class stock_warehouse(orm.Model):
    _inherit = "stock.warehouse"

    def get_all_locations(self, cr, uid, ids, context=None):
        res = {}
        _loc_obj = self.pool.get('stock.location')

        for _obj in self.browse(cr, uid, ids, context=context):
            location_ids = []
            if _obj.lot_stock_id:
                location_ids.append(_obj.lot_stock_id.id)
            if _obj.lot_input_id:
                location_ids.append(_obj.lot_input_id.id)
            if _obj.lot_output_id:
                location_ids.append(_obj.lot_output_id.id)

            fin_loc_ids = _loc_obj.get_children(cr, uid, list(set(location_ids)), context=context)
            fin_loc_ids = list(set([item for sublist in fin_loc_ids.values() for item in sublist]))
            res[_obj.id] = fin_loc_ids
        return res


class stock_production_lot(orm.Model):
    _name = "stock.production.lot"
    _inherit = ['stock.production.lot', 'mail.thread']

    def _get_spl_from_move(self, cr, uid, ids, context=None):
        result = [_obj.prodlot_id.id for _obj in self.pool.get('stock.move').browse(cr, uid, ids, context=context) if _obj.prodlot_id]
        return list(set(result))

    def move_utilized(self, cr, uid, ids, name, args, context=None):
        """
        Returns True if there is any of the stock.production.lot's move_ids' state is Done.
        """
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = bool(len([line.id for line in _obj.move_ids if (line.state == 'done')]))
        return res

    _columns = {
        'barcode_printed': fields.boolean('Printed', readonly="1"),
        'utilized': fields.function(move_utilized, method=True, type='boolean',
            store={
                'stock.production.lot': (lambda self, cr, uid, ids, c={}: ids, ['move_ids'], 20),
                'stock.move': (_get_spl_from_move, ['state'], 20),
            }, string='Utilized', readonly=True),
    }

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Serial Number must be unique !'),
    ]

    _defaults = {
        'name': '/',
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'stock.production.lot', context=c),
        'barcode_printed': lambda *a: False,
    }

    def create(self, cr, uid, vals, context=None):
        """
        This method updates the vals directory with the cost price per unit for production lot.
        ---------------------------------------------------------------------------------------
        @param self: Object Pointer
        @param cr: Database Cursor
        @param uid: Current Logged in User
        @param vals: Vals Directory having field, value pairs
        @param context: Standard Dictionary
        @return: Identifier of the newly created record
        """
        if not vals.get('cost_price_per_unit', False) and vals.get('product_id', False):
            _tmp = self.onchange_product_id(cr, uid, [], vals['product_id'], context=context)
            _tmp = _tmp and _tmp['value'] or {}
            vals.update(_tmp)

        # Component of Serial Number
        _product_id = vals.get('product_id', False)
        _product_obj = _product_id and self.pool.get('product.product').browse(cr, uid, _product_id, context=context) or False
        _product_tmpl = _product_obj and _product_obj.product_tmpl_id

        _serial_number = self.pool.get('ir.sequence').get(cr, uid, 'stock.lot.serial')
        _serial_number = _serial_number[-5:]
        _year = (long(DT.now().strftime('%y')) + 3)
        _product = _product_obj and _product_obj.default_code or ""
        _product = _product[-5:] or ""
        _sub_category = _product_tmpl.categ_id and _product_tmpl.categ_id.code or ""
        _sub_category = _sub_category[-3:] or ""
        _category = _product_tmpl.categ_id and _product_tmpl.categ_id.parent_id and _product_tmpl.categ_id.parent_id.code or ""
        _category = _category[-2:] or ""

        # Assembly of components. If error happened in this line, this should because the product
        # doesn't have _category or _subcategory (both of them will have false value if doesn't have
        # category code). But doesn't matter, category code is a mandatory field. It's always filled
        # by user.
        serial_number = "{0:.2s}.{1:.3s}.{2:.5s}.{3:.2s}.{4:.5s}".format(_category, _sub_category, _product, str(_year), _serial_number)

        # Write serial_number to 'name' field
        vals.update({'name': serial_number})
        return super(stock_production_lot, self).create(cr, uid, vals, context=context)

    def load(self, cr, uid, fields, data, context=None):
        if 'name' in fields:
            raise orm.except_orm(
                _('Error!'),
                _('Can not import serial number!'))

        return super(stock_production_lot, self).load(cr, uid, fields, data, context=context)

    def print_serial_barcode(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        # Cari id dari VIA Form Template untuk mencetak barcode
        _obj = self.pool.get('ir.model.data').get_object(cr, uid, __module__, 'ir_webkit_form_barcode', context=context)
        report_id = _obj.act_report_id and _obj.act_report_id.id or False
        if not report_id:
            raise orm.except_orm(_('Error'), _('Can\'t print barcode because barcode form/template in VIA Form Template is missing.'))
        res = self.pool.get('ir.actions.report.xml').copy_data(cr, uid, report_id, context=context)

        # Tambahkan parameter (sementara ini hard code)
        _ctx = context.copy()
        _print_param = context.get('param', [])
        if not _print_param:
            _print_param = [["A", 1]]
            _ctx.update({'param': _print_param})
        res.update({'context': _ctx})

        print_ids = context.get('print_ids', ids)
        res.update({'datas': {'ids': print_ids, }})

        return res


def visible_when_ready(arch, widgets):
    doc = etree.XML(arch)
    nodes = doc.xpath("//field[@name='ready_for_transfer']")
    if nodes:
        for wdg_name, wdg_type in widgets.iteritems():
            nodes = doc.xpath("//%s[@name='%s']" % (wdg_type, wdg_name))
            for node in nodes:
                _orig_json = node.get('modifiers', '{}')

                #  The modifiers has been json-encoded so, decode it from json before encoding it back
                _orig = json.loads(_orig_json)
                _invis = _orig.get('invisible', [])
                _invis.insert(0, ('ready_for_transfer', '=', False))
                if len(_invis) > 1:
                    # OR it with the rest of the modifier
                    _invis.insert(0, '|')
                _orig.update({'invisible': _invis or []})

                node.set('modifiers', json.dumps(_orig))

    return etree.tostring(doc)


class stock_picking(orm.Model):
    _inherit = "stock.picking"

    def validate_receive(self, cr, uid, ids, name, args, context=None):
        """
        Returns True if all the serial number of all stock moves has been printed.
        If serial number is empty, return False.
        """
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            _line_checks = [line.id for line in _obj.move_lines if ((line.state not in ['cancel']) and line.prodlot_id and not line.prodlot_id.barcode_printed)]
            res[_obj.id] = not bool(len(_line_checks))
        return res

    def _get_sp_from_spl(self, cr, uid, ids, context=None):
        res = []
        for _obj in self.pool.get('stock.production.lot').browse(cr, uid, ids, context=context):
            for move in _obj.move_ids:
                res.append(move.picking_id.id)

        return list(set(res))

    def _get_warehouse(self, cr, uid, ids, name, args, context=None):
        """
        Returns True if all the serial number of all stock moves has been printed.
        If serial number is empty, return False.
        """
        res = {}

        _def = name.endswith('_default')
        for _obj in self.browse(cr, uid, ids, context=context):
            _whse = False
            location_ids = []
            if name.startswith('dest_'):
                _whse = _obj.dest_warehouse or False
            elif name.startswith('source_'):
                _whse = _obj.source_warehouse or False

            if _whse:
                if _def:
                    location_ids = _whse.lot_stock_id.get_children(context=context).get(_whse.lot_stock_id.id, [])
                else:
                    location_ids = _whse.get_all_locations(context=context).get(_whse.id, [])

            res[_obj.id] = [(6, 0, location_ids)]

        return res

    def _get_sp_from_sm(self, cr, uid, ids, context=None):
        res = []
        for _obj in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            res.append(_obj.picking_id.id)

        return list(set(res))

    _columns = {
        'ready_for_transfer': fields.boolean('Ready for Transfer', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
        'phone': fields.related('partner_id', 'phone', type='char', string='Phone', size=64),
        'mobile': fields.related('partner_id', 'mobile', type='char', string='Mobile', size=64),
        'receive_ok': fields.function(validate_receive, method=True, type='boolean', string='OK to Receive', readonly=True,
            store={
                'stock.production.lot': (_get_sp_from_spl, ['barcode_printed'], 20),
                'stock.move': (_get_sp_from_sm, ['state'], 20),
            }),
        'source_warehouse': fields.many2one('stock.warehouse', 'Source Warehouse', required=True, select=True, help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
        'dest_warehouse': fields.many2one('stock.warehouse', 'Destination Warehouse', required=True, help="Location where the system will stock the finished products."),
        'has_been_received': fields.boolean('Checked', help="Check this if product has been received by customer"),
        'source_loc_ids': fields.function(_get_warehouse, method=True, type='many2many', relation="stock.location", string='Source Locations'),
        'dest_loc_ids': fields.function(_get_warehouse, method=True, type='many2many', relation="stock.location", string='Destination Locations'),
        'source_loc_ids_default': fields.function(_get_warehouse, method=True, type='many2many', relation="stock.location", string='Source Locations Default'),
        'dest_loc_ids_default': fields.function(_get_warehouse, method=True, type='many2many', relation="stock.location", string='Destination Locations Default'),
        'dont_check_constraint': fields.boolean('Dont Check Constraint'),
    }

    # receive_ok's default is set to be True to support record rules preventing groups to read stock.picking which receive_ok is False
    # but still allow for copying the stock.picking which receive_ok is True.  If not defaulted receive_ok will be False until calculated
    _defaults = {
        'receive_ok': lambda *a: True,
        'ready_for_transfer': lambda *a: False,
    }

    def validate_serial_number(self, cr, uid, ids, serial_number, context=None):
        if isinstance(ids, (list, tuple, dict, )):
            select = list(ids)
        else:
            select = [ids]

        move_pool = self.pool.get('stock.move')
        lot_pool = self.pool.get('stock.production.lot')
        pick_pool = self.pool.get('stock.picking')

        # Find the if the Serial Number (stock.production.lot) exist.  The given serial number should match name field of stock.production.lot
        if not serial_number:
            raise osv.except_osv(_('Warning !'), _(" Serial number is not provided.  Contact your administrator."))

        lot_ids = lot_pool.search(cr, uid, [('name', '=', serial_number)], context=context)
        if not lot_ids:
            raise osv.except_osv(_('Warning !'), _(" Serial Number '%s' does not exist. Please create it first from Traceability menu.") % serial_number)
        # Take only the first stock.production.lot if there is many, it is assumed that name is unique in stock.production.lot
        lot_obj = lot_pool.browse(cr, uid, lot_ids[0], context=context)

        for _obj in self.browse(cr, uid, select, context=context):
            # Check if the stock.picking is of type 'out' and the status is not ('done', 'cancel')
            # If it is not, raise an error.  It is assumed that only one stock.picking is processed at any point of time
            if _obj.type not in ['out', 'internal']:
                raise osv.except_osv(_('Warning !'), _('This is an Incoming Shipment, only Delivery Order or Internal Moves can be processed this way.'))
            else:
                if _obj.type == 'out' and _obj.state in ['done', 'cancel']:
                    raise osv.except_osv(_('Warning !'), _('Only Delivery Orders that are in Done or Cancelled states that can be processed.'))
                if _obj.type == 'internal' and _obj.state in ['done', 'cancel']:
                    raise osv.except_osv(_('Warning !'), _('Only Internal Moves that are in Done or Cancelled states that can be processed.'))

            _doc_name = ((_obj.type == 'out') and _('Delivery Order')) or ((_obj.type == 'internal') and _('Internal Moves')) or _('Incoming Shipment')
            _move_to_process = False
            for _mv in _obj.move_lines:
                _sn = _mv.prodlot_id and _mv.prodlot_id.name or False
                if serial_number == _sn and _obj.type == 'out':
                    # Find if that stock.production.lot has been used in any of the stock.picking's stock.move.  If so, raise an error
                    raise osv.except_osv(_('Warning !'), _('Serial Number %s has been used in %s %s') % (serial_number, _doc_name, _obj.name))
                if serial_number == _sn and _obj.type == 'internal':
                    # Find if that stock.production.lot has been used in any of the stock.picking's stock.move.  If so, raise an error
                    raise osv.except_osv(_('Warning !'), _('Serial Number %s has been used in %s %s') % (serial_number, _doc_name, _obj.name))

                if pick_pool._check_split(_mv) and (_mv.product_id == lot_obj.product_id) and (_mv.product_qty >= 1.0) and (not _mv.prodlot_id):
                    if not _move_to_process:
                        _move_to_process = _mv

            if _move_to_process:
                _mv_ids = _move_to_process.split_move(context=context)
                if _mv_ids:
                    move_pool.write(cr, uid, _mv_ids[0], {'prodlot_id': lot_obj.id}, context=context)
            else:
                raise osv.except_osv(_('Warning !'), _('No move can be associated with Serial Number %s on %s %s.') % (serial_number, _doc_name, _obj.name))

        return True

    def add_move_lines(self, cr, uid, ids, serial_number, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (list, tuple, dict, )):
            select = list(ids)
        else:
            select = [ids]

        if not ids or ids == [None]:
            raise osv.except_osv(_('Warning !'), _('Please fill mandatory fields and click Save button first.'))

        move_pool = self.pool.get('stock.move')
        lot_pool = self.pool.get('stock.production.lot')

        context.update({
            'source_loc_ids_default': [],
            'dest_loc_ids_default': [],
        })
        default_move_vals = move_pool.default_get(cr, uid, ['location_id', 'location_dest_id', 'date_expected'], context=context)

        # Find the if the Serial Number (stock.production.lot) exist.  The given serial number should match name field of stock.production.lot
        if not serial_number:
            raise osv.except_osv(_('Warning !'), _(" Serial number is not provided.  Contact your administrator."))

        lot_ids = lot_pool.search(cr, uid, [('name', '=', serial_number)], context=context)
        if not lot_ids:
            raise osv.except_osv(_('Warning !'), _(" Serial Number '%s' does not exist. Please create it first from Traceability menu.") % serial_number)
        # Take only the first stock.production.lot if there is many, it is assumed that name is unique in stock.production.lot
        lot_obj = lot_pool.browse(cr, uid, lot_ids[0], context=context)

        onchange_vals = move_pool.onchange_product_id(cr, uid, [], lot_obj.product_id.id, False, False, False)

        fields_to_create = {
            'product_id': lot_obj.product_id.id,
            'product_qty': onchange_vals['value']['product_qty'],
            'product_uom': onchange_vals['value']['product_uom'],
            'prodlot_id': lot_obj.id,
            'date_expected': default_move_vals.get('date_expected'),
            'name': onchange_vals['value']['name'],
        }

        for _obj in self.browse(cr, uid, select, context=context):
            # Check if the stock.picking is of type 'out' and the status is not ('done', 'cancel')
            # If it is not, raise an error.  It is assumed that only one stock.picking is processed at any point of time
            if _obj.type not in ['out', 'internal']:
                raise osv.except_osv(_('Warning !'), _('This is an Incoming Shipment, only Delivery Order or Internal Moves can be processed this way.'))
            else:
                if _obj.type == 'internal' and _obj.state in ['done', 'cancel']:
                    raise osv.except_osv(_('Warning !'), _('Only Internal Moves that are not in Done or Cancelled states that can be processed.'))

            _doc_name = ((_obj.type == 'out') and _('Delivery Order')) or ((_obj.type == 'internal') and _('Internal Moves')) or _('Incoming Shipment')
            for _mv in _obj.move_lines:
                _sn = _mv.prodlot_id and _mv.prodlot_id.name or False
                if serial_number == _sn and _obj.type == 'internal' and lot_obj.product_id.lot_split_type == 'single':
                    # Find if that stock.production.lot has been used in any of the stock.picking's stock.move.  If so, raise an error
                    raise osv.except_osv(_('Warning !'), _('Serial Number %s has been used in %s %s') % (serial_number, _doc_name, _obj.name))

            if not _obj.source_warehouse:
                raise osv.except_osv(_('Warning !'), _('Please fill Source Warehouse first.'))
            if not _obj.dest_warehouse:
                raise osv.except_osv(_('Warning !'), _('Please fill Destination Warehouse first.'))

            fields_to_create.update({
                'location_id': _obj.source_warehouse.lot_stock_id and _obj.source_warehouse.lot_stock_id.id,
                'location_dest_id': _obj.dest_warehouse.lot_input_id and _obj.dest_warehouse.lot_input_id.id,
            })

            check_qty = move_pool.onchange_lot_id(cr, uid, [], fields_to_create.get('prodlot_id'), fields_to_create.get('product_qty'), fields_to_create.get('location_id'), fields_to_create.get('product_id'), fields_to_create.get('product_uom'), context=context)
            _obj.write({'move_lines': [(0, 0, fields_to_create)]}, context=context)
            if check_qty.get('warning', False):
                raise osv.except_osv(_('Error !'), _('Insufficient Stock for Serial Number !'))

        return True

    def onchange_source_warehouse(self, cr, uid, ids, source, context=None):
        location_ids = []
        location_ids_default = []
        if source:
            _whse = self.pool.get('stock.warehouse').browse(cr, uid, source, context=context)
            location_ids = _whse.get_all_locations(context=context).get(source, [])
            if _whse.lot_stock_id:
                location_ids_default = _whse.lot_stock_id.get_children(context=context).get(_whse.lot_stock_id.id, [])
        return {'value': {'source_loc_ids': [(6, 0, location_ids)], 'source_loc_ids_default': [(6, 0, location_ids_default)]}}

    def onchange_dest_warehouse(self, cr, uid, ids, destination, context=None):
        location_ids = []
        location_ids_default = []
        if destination:
            _whse = self.pool.get('stock.warehouse').browse(cr, uid, destination, context=context)
            location_ids = _whse.get_all_locations(context=context).get(destination, [])
            if _whse.lot_stock_id:
                location_ids_default = _whse.lot_stock_id.get_children(context=context).get(_whse.lot_stock_id.id, [])
        return {'value': {
            'partner_id': destination and _whse.partner_id and _whse.partner_id.id or False,
            'dest_loc_ids': [(6, 0, location_ids)],
            'dest_loc_ids_default': [(6, 0, location_ids_default)]
        }}

    def action_move(self, cr, uid, ids, context=None):
        for _obj in self.browse(cr, uid, ids, context=context):
            if (_obj.type == 'out') and (not _obj.ready_for_transfer):
                raise orm.except_orm(_('Error'), _('Stock Picking for Sending Goods cannot be processed further if it is not Ready for Transfer.'))

        return super(stock_picking, self).action_move(cr, uid, ids, context=context)

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(stock_picking, self).fields_view_get(cr, user, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            res['arch'] = visible_when_ready(res.get('arch', ''), DELIVER_WIDGETS)
        return res

    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(stock_picking, self).copy_data(cr, uid, id, default=default, context=context)
        res.pop('ready_for_transfer', None)
        return res

    # This is a replacement override of the original do_partial in stock/stock.py
    # The purpose to:
    # - Copy ready_for_transfer flag when a new stock.picking for partial picking
    # - Copy prodlot_id field when a new stock.move for partial picking
    # - Add the splitting without confirm capability
    #
    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        """ Makes partial picking and moves done.
        @param partial_datas : Dictionary containing details of partial picking
                          like partner_id, partner_id, delivery_date,
                          delivery moves with product_id, product_qty, uom
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        else:
            context = dict(context)

        res = {}
        move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.product')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        sequence_obj = self.pool.get('ir.sequence')
        wf_service = netsvc.LocalService("workflow")
        for pick in self.browse(cr, uid, ids, context=context):
            new_picking = None
            complete, too_many, too_few = [], [], []
            copied_move_ids = {}
            move_product_qty, prodlot_ids, product_avail, partial_qty, product_uoms = {}, {}, {}, {}, {}
            for move in pick.move_lines:
                if move.state in ('done', 'cancel'):
                    continue
                partial_data = partial_datas.get('move%s' % (move.id), {})
                product_qty = partial_data.get('product_qty', 0.0)
                move_product_qty[move.id] = product_qty
                product_uom = partial_data.get('product_uom', False)
                product_price = partial_data.get('product_price', 0.0)
                product_currency = partial_data.get('product_currency', False)
                prodlot_id = partial_data.get('prodlot_id')
                prodlot_ids[move.id] = prodlot_id
                product_uoms[move.id] = product_uom
                partial_qty[move.id] = uom_obj._compute_qty(cr, uid, product_uoms[move.id], product_qty, move.product_uom.id)
                if move.product_qty == partial_qty[move.id]:
                    complete.append(move)
                elif move.product_qty > partial_qty[move.id]:
                    too_few.append(move)
                else:
                    too_many.append(move)

                # Average price computation
                if (pick.type == 'in') and (move.product_id.cost_method == 'average'):
                    product = product_obj.browse(cr, uid, move.product_id.id)
                    move_currency_id = move.company_id.currency_id.id
                    context['currency_id'] = move_currency_id
                    qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product.uom_id.id)

                    if product.id not in product_avail:
                        # keep track of stock on hand including processed lines not yet marked as done
                        product_avail[product.id] = product.qty_available

                    if qty > 0:
                        new_price = currency_obj.compute(cr, uid, product_currency,
                                move_currency_id, product_price, round=False)
                        new_price = uom_obj._compute_price(cr, uid, product_uom, new_price,
                                product.uom_id.id)
                        if product_avail[product.id] <= 0:
                            product_avail[product.id] = 0
                            new_std_price = new_price
                        else:
                            # Get the standard price
                            amount_unit = product.price_get('standard_price', context=context)[product.id]
                            new_std_price = ((amount_unit * product_avail[product.id])
                                + (new_price * qty))/(product_avail[product.id] + qty)
                        # Write the field according to price type field
                        product_obj.write(cr, uid, [product.id], {'standard_price': new_std_price})

                        # Record the values that were chosen in the wizard, so they can be
                        # used for inventory valuation if real-time valuation is enabled.
                        move_obj.write(cr, uid, [move.id],
                            {
                                'price_unit': product_price,
                                'price_currency_id': product_currency
                            })

                        product_avail[product.id] += qty

            for move in too_few:
                product_qty = partial_qty[move.id]
                if not new_picking:
                    new_picking_name = pick.name
                    picking_code = (pick.type != 'internal') and ('stock.picking.%s' % (pick.type)) or 'stock.picking'
                    self.write(cr, uid, [pick.id],
                        {
                            'name': sequence_obj.get(cr, uid, picking_code),
                        })
                    context.update({'approval_carry_over': True})
                    new_picking = self.copy(cr, uid, pick.id,
                        {
                            'name': new_picking_name,
                            'move_lines': [],
                            'state': 'draft',
                            # Copy the ready_for_transfer flag
                            'ready_for_transfer': pick.ready_for_transfer
                        }, context=context)
                # assigning state of stock moves
                if move.state not in ['assigned']:
                    move_state = move.state
                else:
                    move_state = 'confirmed'
                if product_qty != 0:
                    defaults = {
                        'product_qty': product_qty,
                        'product_uos_qty': product_qty,  # TODO: put correct uos_qty
                        'picking_id': new_picking,
                        'state': move_state,
                        'move_dest_id': False,
                        'price_unit': move.price_unit,
                        'product_uom': product_uoms[move.id]
                    }
                    prodlot_id = prodlot_ids[move.id]
                    if prodlot_id:
                        defaults.update(prodlot_id=prodlot_id)
                    copy_move_id = move_obj.copy(cr, uid, move.id, defaults)
                    copied_move_ids.update({move.id: copy_move_id})
                move_obj.write(cr, uid, [move.id],
                        {
                            'product_qty': move.product_qty - partial_qty[move.id],
                            'product_uos_qty': move.product_qty - partial_qty[move.id],  # TODO: put correct uos_qty
                            'tracking_id': False,
                        })

            if new_picking:
                move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
            for move in complete:
                defaults = {
                    'product_uom': product_uoms[move.id],
                    'product_qty': move_product_qty[move.id]
                }
                if prodlot_ids.get(move.id):
                    defaults.update({'prodlot_id': prodlot_ids[move.id]})
                move_obj.write(cr, uid, [move.id], defaults)
            for move in too_many:
                product_qty = move_product_qty[move.id]
                defaults = {
                    'product_qty': product_qty,
                    'product_uos_qty': product_qty,  # TODO: put correct uos_qty
                    'product_uom': product_uoms[move.id]
                }
                prodlot_id = prodlot_ids.get(move.id)
                if prodlot_ids.get(move.id):
                    defaults.update(prodlot_id=prodlot_id)
                if new_picking:
                    defaults.update(picking_id=new_picking)
                move_obj.write(cr, uid, [move.id], defaults)

            # At first we confirm the new picking (if necessary)
            if new_picking:
                if context.get('partial_no_confirm'):
                    self.write(cr, uid, [pick.id], {'backorder_id': new_picking})
                    delivered_pack_id = new_picking
                    if pick.state in ['confirmed', 'assigned']:
                        wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
                        for move in pick.move_lines:
                            if move.state not in ['assigned']:
                                backorder_move = copied_move_ids.get(move.id, False)
                                if backorder_move:
                                    move_obj.write(cr, uid, [backorder_move], {'state': move.state}, context=context)
                else:
                    wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
                    # Then we finish the good picking
                    pick.write({'backorder_id': new_picking})
                    if pick.ready_for_transfer:
                        self.write(cr, uid, [new_picking], {'ready_for_transfer': True})
                    self.action_move(cr, uid, [new_picking], context=context)
                    wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
                    wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
                    delivered_pack_id = pick.id
                    back_order_name = self.browse(cr, uid, delivered_pack_id, context=context).name
                    self.message_post(cr, uid, new_picking, body=_("Back order <em>%s</em> has been <b>created</b>.") % (back_order_name), context=context)
            else:
                if not context.get('partial_no_confirm'):
                    self.action_move(cr, uid, [pick.id], context=context)
                    wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
                delivered_pack_id = pick.id

            delivered_pack = self.browse(cr, uid, delivered_pack_id, context=context)
            res[pick.id] = {'delivered_picking': delivered_pack.id or False}

        return res

    def print_serial_barcode(self, cr, uid, ids, context=None):
        # Siapkan informasi object yang akan dicetak.
        _serial_no = []
        for _obj in self.browse(cr, uid, ids, context):
            for _stock_move in _obj.move_lines:
                if _stock_move.prodlot_id:
                    _serial_no.append(_stock_move.prodlot_id.id)

        _serial_no = list(set(_serial_no))
        return self.pool.get('stock.production.lot').print_serial_barcode(cr, uid, _serial_no, context=context)

    def _check_loc_id(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for pick in self.browse(cr, uid, ids, context=context):
            if (pick.type in ['internal']) and not pick.dont_check_constraint:
                for move in pick.move_lines:
                    _loc = move.location_id
                    _whse = _loc.get_warehouse(context=context).get(_loc.id, [])
                    return pick.source_warehouse.id in _whse
        return True

    def _check_dest_id(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for pick in self.browse(cr, uid, ids, context=context):
            if (pick.type in ['internal']) and not pick.dont_check_constraint:
                for move in pick.move_lines:
                    _loc = move.location_dest_id
                    _whse = _loc.get_warehouse(context=context).get(_loc.id, [])
                    return pick.dest_warehouse.id in _whse
        return True

    _constraints = [
        (_check_loc_id, _("One or more of the Move's Source Location is not within the Source Warehouse's locations."), ['location_id']),
        (_check_dest_id, _("One or more of the Move's Destination Location is not within the Destination Warehouse's locations."), ['location_dest_id']),
    ]


class stock_picking_in(orm.Model):
    _inherit = "stock.picking.in"

    def validate_receive(self, cr, uid, ids, name, args, context=None):
        return self.pool.get('stock.picking').validate_receive(cr, uid, ids, name, args, context=context)

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

    _columns = {
        'ready_for_transfer': fields.boolean('Ready for Transfer', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
        'phone': fields.related('partner_id', 'phone', type='char', string='Phone', size=64),
        'mobile': fields.related('partner_id', 'mobile', type='char', string='Mobile', size=64),
        'receive_ok': fields.function(validate_receive, method=True, type='boolean', string='OK to Receive', readonly=True,
            store={
                'stock.production.lot': (_get_sp_from_spl, ['barcode_printed', 'state'], 20),
                'stock.move': (_get_sp_from_sm, ['state'], 20),
            }),
        'has_been_received': fields.boolean('Checked', help="Check this if product has been received by customer"),
    }

    # receive_ok's default is set to be True to support record rules preventing groups to read stock.picking which receive_ok is False
    # but still allow for copying the stock.picking which receive_ok is True.  If not defaulted receive_ok will be False until calculated
    _defaults = {
        'receive_ok': lambda *a: True,
        'ready_for_transfer': lambda *a: False,
    }

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(stock_picking_in, self).fields_view_get(cr, user, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            res['arch'] = visible_when_ready(res.get('arch', ''), DELIVER_WIDGETS)
        return res

    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(stock_picking_in, self).copy_data(cr, uid, id, default=default, context=context)
        res.pop('ready_for_transfer')
        return res

    def print_serial_barcode(self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking').print_serial_barcode(cr, uid, ids, context=context)


class stock_picking_out(orm.Model):
    _inherit = "stock.picking.out"

    def validate_receive(self, cr, uid, ids, name, args, context=None):
        return self.pool.get('stock.picking').validate_receive(cr, uid, ids, name, args, context=context)

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

    _columns = {
        'ready_for_transfer': fields.boolean('Ready for Transfer', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
        'phone': fields.related('partner_id', 'phone', type='char', string='Phone', size=64),
        'mobile': fields.related('partner_id', 'mobile', type='char', string='Mobile', size=64),
        'receive_ok': fields.function(validate_receive, method=True, type='boolean', string='OK to Receive', readonly=True,
            store={
                'stock.production.lot': (_get_sp_from_spl, ['barcode_printed', 'state'], 20),
                'stock.move': (_get_sp_from_sm, ['state'], 20),
            }),
        'has_been_received': fields.boolean('Checked', help="Check this if product has been received by customer"),
    }

    # receive_ok's default is set to be True to support record rules preventing groups to read stock.picking which receive_ok is False
    # but still allow for copying the stock.picking which receive_ok is True.  If not defaulted receive_ok will be False until calculated
    _defaults = {
        'receive_ok': lambda *a: True,
        'ready_for_transfer': lambda *a: False,
    }

    def action_move(self, cr, uid, ids, context=None):
        for _obj in self.browse(cr, uid, ids, context=context):
            if (_obj.type == 'out') and (not _obj.ready_for_transfer):
                raise orm.except_orm(_('Error'), _('Stock Picking for Sending Goods cannot be processed further if it is not Ready for Transfer.'))

        return super(stock_picking_out, self).action_move(cr, uid, ids, context=context)

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(stock_picking_out, self).fields_view_get(cr, user, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            res['arch'] = visible_when_ready(res.get('arch', ''), DELIVER_WIDGETS)
        return res

    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(stock_picking_out, self).copy_data(cr, uid, id, default=default, context=context)
        res.pop('ready_for_transfer')
        return res

    def validate_serial_number(self, cr, uid, ids, serial_number, context=None):
        res = self.pool.get('stock.picking').validate_serial_number(cr, uid, ids, serial_number, context=context)
        return res

    def print_serial_barcode(self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking').print_serial_barcode(cr, uid, ids, context=context)


class stock_move(orm.Model):
    _inherit = "stock.move"

    def _default_location_source(self, cr, uid, context=None):
        location_ids = context.get('source_loc_ids_default', [])
        _loc_obj = self.pool.get('stock.location')
        fin_loc_ids = _loc_obj.get_children(cr, uid, list(set(location_ids)), context=context)
        fin_loc_ids = list(set([item for sublist in fin_loc_ids.values() for item in sublist]))
        return fin_loc_ids and fin_loc_ids[0] or False

    def _default_location_destination(self, cr, uid, context=None):
        location_ids = context.get('dest_loc_ids_default', [])
        _loc_obj = self.pool.get('stock.location')
        fin_loc_ids = _loc_obj.get_children(cr, uid, list(set(location_ids)), context=context)
        fin_loc_ids = list(set([item for sublist in fin_loc_ids.values() for item in sublist]))
        return fin_loc_ids and fin_loc_ids[0] or False

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}

        res = super(stock_move, self).create(cr, uid, vals, context=context)
        _pick_id = vals.get('picking_id', False)
        _pick = _pick_id and self.pool.get('stock.picking').browse(cr, uid, _pick_id, context=context) or False
        if _pick and (_pick.type == 'in') and context.get('runworkflow', True):
            self.action_confirm(cr, uid, [res], context=context)
            self.action_assign(cr, uid, [res])
        return res

    def _check_loc_id(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for _obj in self.browse(cr, uid, ids, context=context):
            if (_obj.picking_id.type in ['internal']) and not _obj.picking_id.dont_check_constraint:
                _whse = _obj.picking_id.source_warehouse
                _loc_ids = _whse and _whse.get_all_locations(context=context).get(_whse.id, []) or []
                return _obj.location_id.id in _loc_ids
        return True

    def _check_dest_id(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for _obj in self.browse(cr, uid, ids, context=context):
            if (_obj.picking_id.type in ['internal']) and not _obj.picking_id.dont_check_constraint:
                _whse = _obj.picking_id.dest_warehouse
                _loc_ids = _whse and _whse.get_all_locations(context=context).get(_whse.id, []) or []
                return _obj.location_dest_id.id in _loc_ids
        return True

    _constraints = [
        (_check_loc_id, _("One or more of the Move's Source Location is not within the Source Warehouse's locations."), ['location_id']),
        (_check_dest_id, _("One or more of the Move's Destination Location is not within the Destination Warehouse's locations."), ['location_dest_id']),
    ]

    _defaults = {
        'location_id': _default_location_source,
        'location_dest_id': _default_location_destination,
    }


class stock_return_picking(osv.osv_memory):
    _inherit = 'stock.return.picking'

    def create_returns(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        pick = self.pool.get('stock.picking').browse(cr, uid, context.get('active_id', False), context=context)
        pick.write({'dont_check_constraint': True}, context=context)
        res = super(stock_return_picking, self).create_returns(cr, uid, ids, context=context)
        pick.write({'dont_check_constraint': False}, context=context)

        new_picking_id = eval(str(res.get('domain')))[0][2]
        new_pick = new_picking_id and self.pool.get('stock.picking').browse(cr, uid, new_picking_id[0], context=context) or False
        if new_pick:
            new_pick.write({
                'dont_check_constraint': False,
                'source_warehouse': pick.dest_warehouse and pick.dest_warehouse.id or False,
                'dest_warehouse': pick.source_warehouse and pick.source_warehouse.id or False,
            }, context=context)

        return res
