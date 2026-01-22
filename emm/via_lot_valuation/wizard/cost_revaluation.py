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

from osv import orm, fields
from tools.translate import _



class cost_revaluation(orm.TransientModel):
    _name = 'cost.revaluation'
    _description = "Wizard to revaluate an invoice."
    _rec_name = 'date'

    _columns = {
        'date': fields.date('Date', help='Date of valuation schedule.'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', size=64, readonly=True,
            help='Display the invoice number related journal entry.'),
        'company_id': fields.many2one('res.company', 'Company', readonly=True,
            help='Company where the user is connected.'),
        'memo': fields.text('Memo', help='Description about the invoice.'),
        'inv_line_ids': fields.one2many('invoice.item', 'item_id', 'Revaluation Items',
            help='List of all the items of Invoice line.')
    }

    _defaults = {
        'date': fields.date.context_today,
    }

    def default_get(self, cr, uid, fields, context=None):
        """
         Get the default value from invoice line
         ----------------------------------------
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: A List of fields
         @param context: A standard dictionary
         @return: Return a dictionary which hold the field value pair.
        """
        res = super(cost_revaluation, self).default_get(cr, uid, fields, context=context)
        account_data = self.pool.get('account.invoice').browse(cr, uid, context.get('active_id'), context=context)
        result = []
        for line in account_data.invoice_line:
            if line.product_id and line.prod_lot_id:
                result.append({
                    'invoice_line_id': line.id,
                    'product_id': line.product_id.id,
                    'lot_id': line.prod_lot_id.id,
                    'qty': line.quantity or 0.0,
                    'uom_id': line.uos_id and line.uos_id.id or False,
                    'cost_price': line.price_unit or 0.0,
                })

        res.update({
            'invoice_id': account_data.id,
            'company_id': account_data.company_id.id,
            'inv_line_ids': result
        })
        return res

    def get_valuation_create(self, cr, uid, ids, context=None):
        """
         Create a record in Draft Valuation Document from Cost Revaluation wizard
         -------------------------------------------------------------------------
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: A List of ids
         @param context: A standard dictionary
         @return: Return a id which created.
        """
        if context is None:
            context = {}

        res = {}
        revaluation_obj = self.pool.get('lot.valuation')
        ccy_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        _co_ccy_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id

        for data in self.browse(cr, uid, ids, context=context):
            for line in data.inv_line_ids:
                if line.lot_id:
                    # Convert to the Company's Currency
                    _std_price = line.invoice_line_id.price_unit
                    _inv_ccy = line.invoice_line_id.invoice_id.currency_id.id
                    if _co_ccy_id != _inv_ccy:
                        _ctx = {'date': line.invoice_line_id.invoice_id.date_invoice}
                        _std_price = ccy_obj.compute(cr, uid, _inv_ccy, _co_ccy_id, _std_price, context=_ctx)

                    # Account for UOM Difference (Invoice Line UOS vs Production Lot's Product UOM)
                    # If Invoice Line UOS is not specified, assume that it will use Product UOM
                    _inv_uom = line.uom_id and line.uom_id.id or line.product_id.uom_id.id or False
                    _prod_uom = line.lot_id.product_id.uom_id.id or False
                    if _inv_uom != _prod_uom:
                        _std_price = uom_obj._compute_price(cr, uid, _inv_uom, _std_price, to_uom_id=_prod_uom)

                    res = {
                        'product_id': line.product_id.id,
                        'lot_id': line.lot_id.id,
                        'date': data.date,
                        'qty': line.qty or 0.0,
                        'product_uom_id': _prod_uom,
                        'existing_cost_price': line.lot_id.cost_price_per_unit or 0.0,
                        'valuation_cost_price': _std_price or 0.0,
                    }
                    revaluation_obj.create(cr, uid, res, context=context)
        return {'type': 'ir.actions.act_window_close'}

cost_revaluation()


class invoice_item(orm.TransientModel):
    _name = 'invoice.item'
    _rec_name = 'product_id'
    _columns = {
        'item_id': fields.many2one('cost.revaluation', 'Item', invisible=True),
        'invoice_line_id': fields.many2one('account.invoice.line', 'Invoice Line'),
        'product_id': fields.many2one('product.product', 'Product', required=True, domain=[('type', '!=', 'service')]),
        'lot_id': fields.many2one('stock.production.lot', 'Serial Number', required=True, help='Product lot number of Product.'),
        'qty': fields.float('Quantity', help='Quantity of product Lot.'),
        'uom_id': fields.many2one('product.uom', 'UOM', help='Uom Of the Product.'),
        'cost_price': fields.float('Cost Price', help='Cost price of the Product'),
    }

invoice_item()
