# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 - 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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
from tools.translate import _
import decimal_precision as dp
import logging


class product_product(orm.Model):
    _inherit = "product.product"

    def _get_split_qty(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = False
            if _obj.lot_split_type == 'lu':
                if not _obj.packaging:
                    raise orm.except_orm(_('Error :'), _("Product '%s' has 'Lot split type' = 'Logistical Unit' but is missing packaging information.") % (_obj.name))
                res[_obj.id] = _obj.packaging[0].qty
            elif _obj.lot_split_type == 'single':
                res[_obj.id] = 1

        return res

    _columns = {
        'split_qty': fields.function(_get_split_qty, type='float',  digits_compute=dp.get_precision('Product Unit of Measure'), string='Split Quantity'),
    }


class stock_move(orm.Model):
    _inherit = 'stock.move'

    def _file_import_hook(self, cr, uid, config_id=False, context=None):
        """
        This method is called to process every line of the file being imported
        """
        if context is None:
            context = {}

        vals = context.get('line_data', False)
        if not (vals and isinstance(vals, (dict, ))):
            raise orm.except_orm(_('Error!!'), _('No recognizeable data is to be processed.'))

        _picking_obj = self.pool.get('stock.picking')
        _doc_name = context.get('id', False)
        _picking_ids = []
        if _doc_name:
            _picking_ids = [_doc_name]
        else:
            _doc_name = context.get('name', '')
            _picking_ids = _picking_obj.name_search(cr, uid, name=_doc_name, context=context, limit=1)
        if not _picking_ids:
            context.update({'abort': True})
            raise orm.except_orm(_('Error!!'), _('Stock Picking %s not found and cannot be processed.') % (_doc_name))

        _picking = _picking_obj.browse(cr, uid, int(_picking_ids[0]), context=context)
        context.update({'res_id': 'stock.picking,{0}'.format(_picking_ids[0])})
        if not _picking:
            context.update({'abort': True})
            raise orm.except_orm(_('Error!!'), _('The specified Stock Picking %s is not found.') % (_doc_name))

        _doc_name = _picking.name
        if _picking.state in ('cancel', 'done'):
            context.update({'abort': True})
            raise orm.except_orm(_('Error!!'), _('The specified Stock Picking %s is either in Cancelled or Transferred state and cannot be processed.') % (_doc_name))

        _lot_id = vals.get('prodlot_id', False)
        _lot_obj = self.pool.get('stock.production.lot')
        _lot = _lot_id and isinstance(_lot_id, (int, long, )) and _lot_obj.browse(cr, uid, _lot_id, context=context) or False
        if not _lot:
            raise orm.except_orm(_('Error!!'), _('Serial Number ID %s is not found and cannot be processed.') % (str(_lot_id)))

        _picking_lots = {x.prodlot_id.id: x.prodlot_id.name for x in _picking.move_lines if x.state not in ('cancel') and x.prodlot_id}
        if _lot_id in _picking_lots:
            raise orm.except_orm(_('Error!!'), _('Serial Number %s has been used in Stock Picking %s.') % (_picking_lots[_lot_id], _doc_name))

        _lot_prd = _lot.product_id
        _match = False
        _uom_obj = self.pool.get('product.uom')
        for _line in _picking.move_lines:
            if (_picking_obj._check_split(_line) and
               (_line.product_id == _lot_prd) and
               (not _line.prodlot_id)):
                _line_qty_in_std_uom = _uom_obj._compute_qty_obj(cr, uid, _line.product_uom, _line.product_qty, _lot_prd.uom_id, context=context)
                if (_line_qty_in_std_uom >= _lot.product_id.split_qty):
                    _match = _line
        if _match:
            _mv_ids = _match.split_move(context=context)
        else:
            # Create a new move
            _packaging = (_lot_prd.lot_split_type == 'lu') and _lot_prd.packaging and _lot_prd.packaging[0] or False
            _qty = _packaging and _packaging.qty or 1.0

            _ctx = context.copy()
            _ctx.update({'picking_type': _picking.type})
            _vals = {
                'product_id': _lot_prd.id,
                'partner_id': _picking.partner_id and _picking.partner_id.id or False,
                'location_id': self._default_location_source(cr, uid, context=_ctx),
                'location_dest_id': self._default_location_destination(cr, uid, context=_ctx),
            }

            _ocv = self.onchange_product_id(cr, uid, [],
                                            prod_id=_vals.get('product_id', False),
                                            loc_id=_vals.get('location_id', False),
                                            loc_dest_id=_vals.get('location_dest_id', False),
                                            partner_id=_vals.get('partner_id', False))
            _ocv = _ocv.get('value', {})
            for x in vals.keys():
                _ocv.pop(x, None)
            _vals.update(_ocv)

            _vals.update({
                'picking_id': _picking.id,
                'product_qty': _qty,
                'product_uom': _lot_prd.uom_id and _lot_prd.uom_id.id or False,
                'product_uos': _lot_prd.uos_id and _lot_prd.uos_id.id or False,
                'product_packaging': _packaging and _packaging.id or False,
            })

            _ocv = self.onchange_quantity(cr, uid, [],
                                          _vals.get('product_id', False),
                                          _vals.get('product_qty', False),
                                          _vals.get('product_uom', False),
                                          _vals.get('product_uos', False))
            _ocv = _ocv.get('value', {})
            for x in vals.keys():
                _ocv.pop(x, None)
            _vals.update(_ocv)

            # Use the user inputed data as master value
            _vals.update(vals)

            _mv_ids = self.create(cr, uid, _vals, context=_ctx)
            _mv_ids = [_mv_ids]

        if _mv_ids:
            self.write(cr, uid, _mv_ids[0], {'prodlot_id': _lot.id}, context=context)

        _doc_ids = context.get('doc_ids')
        _doc_ids = isinstance(_doc_ids, (list, tuple, )) and list(_doc_ids) or []
        _doc_ids.append(_picking.id)
        context.update({'doc_ids': _doc_ids})

        return True

    def _post_import_hook(self, cr, uid, config_id=False, context=None):
        """
        This method is called after every line in the imported file has been processed.
        CURRENTLY DOES NOTHING
        """
        return True


class stock_inventory_line(orm.Model):
    _inherit = 'stock.inventory.line'

    def _file_import_hook(self, cr, uid, config_id=False, context=None):
        """
        This method is called to process every line of the file being imported
        """
        if context is None:
            context = {}

        vals = context.get('line_data', False)
        if not (vals and isinstance(vals, (dict, ))):
            raise orm.except_orm(_('Error!!'), _('No recognizeable data is to be processed.'))

        _sinv_obj = self.pool.get('stock.inventory')
        _doc_name = context.get('id', False)
        _sinv_ids = []
        if _doc_name:
            _sinv_ids = [_doc_name]
        else:
            _doc_name = context.get('name', '')
            _sinv_ids = _sinv_obj.name_search(cr, uid, name=_doc_name, context=context, limit=1)
        if not _sinv_ids:
            context.update({'abort': True})
            raise orm.except_orm(_('Error!!'), _('Stock Inventory %s not found and cannot be processed.') % (_doc_name))

        _sinv = _sinv_obj.browse(cr, uid, int(_sinv_ids[0]), context=context)
        context.update({'res_id': 'stock.inventory,{0}'.format(_sinv_ids[0])})
        if not _sinv:
            context.update({'abort': True})
            raise orm.except_orm(_('Error!!'), _('The specified Stock Inventory %s is not found.') % (_doc_name))

        _doc_name = _sinv.name
        if _sinv.state in ('cancel', 'done'):
            context.update({'abort': True})
            raise orm.except_orm(_('Error!!'), _('The specified Stock Inventory %s is either in Cancelled or Transferred state and cannot be processed.') % (_doc_name))

        _lot_id = vals.get('prod_lot_id', False)
        _lot_obj = self.pool.get('stock.production.lot')
        _lot = _lot_id and isinstance(_lot_id, (int, long, )) and _lot_obj.browse(cr, uid, _lot_id, context=context) or False
        if not _lot:
            raise orm.except_orm(_('Error!!'), _('Serial Number ID %s is not found and cannot be processed.') % (str(_lot_id)))

        _sinv_lots = {x.prod_lot_id.id: x.prod_lot_id.name for x in _sinv.inventory_line_id if x.prod_lot_id}
        if _lot_id in _sinv_lots.keys():
            raise orm.except_orm(_('Error!!'), _('Serial Number %s has been used in Stock Picking %s.') % (_sinv_lots[_lot_id], _doc_name))

        # Create a new move
        _lot_prd = _lot.product_id
        _packaging = (_lot_prd.lot_split_type == 'lu') and _lot_prd.packaging and _lot_prd.packaging[0] or False
        _qty = _packaging and _packaging.qty or 1.0

        _ctx = context.copy()
        _vals = {
            'product_id': _lot_prd.id,
            'location_id': self._default_stock_location(cr, uid, context=_ctx),
            'inventory_id': _sinv.id,
            'product_uom': _lot_prd.uom_id and _lot_prd.uom_id.id or False,
            'product_qty': _qty,
            'prod_lot_id': _lot.id,
        }

        _mv_ids = self.create(cr, uid, _vals, context=_ctx)
        _mv_ids = [_mv_ids]

        _doc_ids = context.get('doc_ids')
        _doc_ids = isinstance(_doc_ids, (list, tuple, )) and list(_doc_ids) or []
        _doc_ids.append(_sinv.id)
        context.update({'doc_ids': _doc_ids})

        return True

    def _post_import_hook(self, cr, uid, config_id=False, context=None):
        """
        This method is called after every line in the imported file has been processed.
        CURRENTLY DOES NOTHING
        """
        return True
