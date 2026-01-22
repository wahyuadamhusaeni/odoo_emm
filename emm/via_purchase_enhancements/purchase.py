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
from osv import fields
from tools.translate import _


class purchase_order(orm.Model):
    _inherit = 'purchase.order'

    def _prepare_order_picking(self, cr, uid, order, context=None):
        res = super(purchase_order, self)._prepare_order_picking(cr, uid, order, context=context)
        res.update({'partner_id': order.partner_id.id, })
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
            args.insert(pos, ('purchase_info.value', 'ilike', _name_filter))
            args.insert(pos, '|')

        return super(purchase_order, self).search(cr, uid, args, offset, limit,
                   order, context=context, count=count)

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not context:
            context = {}
        if not args:
            args = []
        args = args[:]

        if name:
            ids = self.search(cr, uid, [('partner_ref', '=', name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('purchase_info.value', 'ilike', name)] + args, limit=limit, context=context)
                if not ids:
                    ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_type:
                raise orm.except_orm(_('Error !'), _('You can not confirm purchase order without selecting (Purchase Order) Type.'))

        rv = super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)

        for po in self.browse(cr, uid, ids, context=context):
            if po.state == 'confirmed':
                _new_po_number = self.pool.get('ir.sequence').get_id(cr, uid, po.order_type.sequence_id.id, code_or_id='id', context=context) or ''
                po.write({'order_number': _new_po_number})

        return rv

    def _get_default_type(self, cr, uid, *args):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        _order_type_id = self.pool.get('purchase.order.type').search(cr, uid, [('company_id', '=', user.company_id.id)])
        return _order_type_id and _order_type_id[0] or False

    def onchange_dest_address_id(self, cr, uid, ids, adr_id):
        rv = {}
        # If the specified adr_id had not changed, don't execute the on_change
        if ids and ids[0]:
            _po = self.pool.get('purchase.order').browse(cr, uid, ids[0])
            if (adr_id == _po.dest_address_id.id):
                return rv

        rv = super(purchase_order, self).onchange_dest_address_id(cr, uid, ids, adr_id)

        return rv

    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id):
        rv = {}
        # If the specified warehouse_id had not changed, don't execute the on_change
        if ids and ids[0]:
            _po = self.pool.get('purchase.order').browse(cr, uid, ids[0])
            if (warehouse_id == _po.warehouse_id.id):
                return rv

        rv = super(purchase_order, self).onchange_warehouse_id(cr, uid, ids, warehouse_id)

        return rv

    def onchange_partner_id(self, cr, uid, ids, part):
        rv = {}
        # If the specified part had not changed, don't execute the on_change
        if ids and ids[0]:
            _po = self.pool.get('purchase.order').browse(cr, uid, ids[0])
            if (part == _po.partner_id.id):
                return rv

        rv = super(purchase_order, self).onchange_partner_id(cr, uid, ids, part)

        return rv

    def get_purchase_info_by_name(self, cr, uid, ids, info_name='', context=None):
        if not context:
            context = {}
        if isinstance(ids, (list, tuple, dict, )):
            select = list(ids)
        else:
            select = [ids]

        res = dict.fromkeys(ids, '')
        _info_code = ''
        for _selection in self.pool.get('purchase.info')._columns['parameter_id'].selection(self, cr, uid):
            if info_name == _selection[1]:
                _info_code = _selection[0]
                break

        if _info_code:
            for po in self.browse(cr, uid, select, context=context):
                for _info in po.purchase_info:
                    if _info.parameter_id == _info_code:
                        res[po.id] = _info.value

        return isinstance(ids, (int, long, )) and res[ids] or res

    def get_purchase_info_by_id(self, cr, uid, ids, info_id='', context=None):
        if not context:
            context = {}
        if isinstance(ids, (list, tuple, dict, )):
            select = list(ids)
        else:
            select = [ids]

        res = dict.fromkeys(ids, '')

        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr, uid, [('model', '=', 'code.decode'), ('name', '=', info_id)], context=context)
        resource_id = model_data_ids and obj_model.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id'] or False

        if resource_id:
            _selection = self.pool.get('code.decode').browse(cr, uid, resource_id, context=context)
            for po in self.browse(cr, uid, select, context=context):
                for _info in po.purchase_info:
                    if _info.parameter_id == _selection.code:
                        res[po.id] = _info.value

        return isinstance(ids, (int, long, )) and res[ids] or res

    def _paid(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for purchase in self.browse(cursor, user, ids, context=context):
            paid = True
            for invoice in purchase.invoice_ids:
                if invoice.state != 'paid':
                    paid = False
                    break
            res[purchase.id] = paid
        return res

    _columns = {
        # For PO type and numbering
        'order_type': fields.many2one('purchase.order.type', 'Type', readonly=True, states={'draft': [('readonly', False)]}, help="Purchase Order Type."),
        'order_number': fields.char('Order Number', size=64, select=True, readonly=True, help="Unique fiscal order number created when order is confirmed"),

        # For Purchase Order References
        'purchase_info': fields.one2many('purchase.info', 'purchase_order_id', 'Purchase Order Info'),
        'paid': fields.function(_paid, string='Invoice Paid', type='boolean', help="It indicates that an invoice has been paid"),
    }

    _defaults = {
        # 'order_type': _get_default_type,
    }

purchase_order()


class purchase_order_line(orm.Model):
    _inherit = 'purchase.order.line'

    _columns = {
        'notes': fields.text('Notes'),
    }

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        """
        The purpose of this enhancement is to prevent the changing description, tax and price if the
        product (id) is not really changed as this method is used by the view when the following
        fields changed: product_id, product_qty, and product_uom (via onchange_product_uom).
        """
        _orig_product_id = False
        if ids:
            _pol = self.pool.get('purchase.order.line').browse(cr, uid, ids[0])
            _orig_product_id = _pol and _pol.product_id and _pol.product_id.id or False

        res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, context=context)

        if (product_id == _orig_product_id):
            if ('name' in res['value']):
                del res['value']['name']
            if ('taxes_id' in res['value']):
                del res['value']['taxes_id']
            if ('price_unit' in res['value']):
                del res['value']['price_unit']
        return res

purchase_order_line()
