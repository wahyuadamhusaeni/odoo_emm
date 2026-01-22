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

from osv import fields, orm
from tools.translate import _


class purchase_requisition_line(orm.Model):
    _inherit = "purchase.requisition.line"

    _columns = {
        'notes': fields.text('Notes'),
    }

purchase_requisition_line()


class purchase_requisition(orm.Model):
    _inherit = "purchase.requisition"

    def create(self, cr, user, vals, context=None):
        if ('name' not in vals):
            _seq_code = self.pool.get('ir.model.data').get_object(cr, user, 'purchase_requisition', 'seq_type_purchase_requisition', context=context)
            vals['name'] = self.pool.get('ir.sequence').get(cr, user, _seq_code.code)
        new_id = super(purchase_requisition, self).create(cr, user, vals, context)
        return new_id

    def make_purchase_order(self, cr, uid, ids, partner_id, context=None):
        """
        Create New RFQ for Supplier

       This method overrides the original one written in
       purchase_requistion/purchase_requisition.py to enable the transfer of
       purchase.requisition.line Notes field to purchase.order.line
        """
        if context is None:
            context = {}
        assert partner_id, 'Supplier should be specified'
        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        fiscal_position = self.pool.get('account.fiscal.position')
        supplier = res_partner.browse(cr, uid, partner_id, context=context)
        delivery_address_id = res_partner.address_get(cr, uid, [supplier.id], ['delivery'])['delivery']
        supplier_pricelist = supplier.property_product_pricelist_purchase or False
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            if supplier.id in filter(lambda x: x, [rfq.state not in ('cancel') and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
                raise orm.except_orm(_('Warning'), _('You have already one %s purchase order for this partner, you must cancel this purchase order to create a new quotation.') % rfq.state)
            location_id = requisition.warehouse_id.lot_input_id.id
            purchase_id = purchase_order.create(cr, uid, {
                'origin': requisition.name,
                'partner_id': supplier.id,
                'partner_address_id': delivery_address_id,
                'pricelist_id': supplier_pricelist.id,
                'location_id': location_id,
                'company_id': requisition.company_id.id,
                'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
                'requisition_id': requisition.id,
                'notes': requisition.description,
                'warehouse_id': requisition.warehouse_id.id,
            })
            res[requisition.id] = purchase_id
            for line in requisition.line_ids:
                product = line.product_id
                seller_price, qty, default_uom_po_id, date_planned = self._seller_details(cr, uid, line, supplier, context=context)
                taxes_ids = product.supplier_taxes_id
                taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
                purchase_order_line.create(cr, uid, {
                    'order_id': purchase_id,
                    'name': product.partner_ref,
                    'product_qty': qty,
                    'product_id': product.id,
                    'product_uom': default_uom_po_id,
                    'price_unit': seller_price,
                    'date_planned': date_planned,
                    'notes': unicode(' - ').join([str(line.notes or '').strip(), str(product.description_purchase or '').strip()]),
                    'taxes_id': [(6, 0, taxes)],
                }, context=context)

        return res

purchase_requisition()
