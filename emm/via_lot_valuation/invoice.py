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


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    def action_date_assign(self, cr, uid, ids, *args):
        """
        When you validate a supplier invoice the product's price should be updated
        -------------------------------------------------------------------------
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current Logged in User
        @param ids : Identifiers of the current Invoices
        @param args : Other Args
        @return True
        """
        prod_obj = self.pool.get('product.product')
        ccy_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')

        _co_ccy_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        for invoice in self.browse(cr, uid, ids):
            # Update the cost price of the product if supplier invoice is validated
            if (invoice.type == 'in_invoice'):
                for inv_line in invoice.invoice_line:
                    if inv_line.product_id.is_lot_based:
                        # Convert to the Company's Currency
                        _std_price = inv_line.price_unit
                        if _co_ccy_id != invoice.currency_id.id:
                            _ctx = {'date': invoice.date_invoice}
                            _std_price = ccy_obj.compute(cr, uid, invoice.currency_id.id, _co_ccy_id, _std_price, context=_ctx)

                        # Account for UOM Difference (Invoice Line UOS vs Product's UOM)
                        # If Invoice Line UOS is not specified, assume that it will use Product UOM
                        _inv_uom = inv_line.uos_id and inv_line.uos_id.id or inv_line.product_id.uom_id.id or False
                        _prod_uom = inv_line.product_id.uom_id.id or False
                        if _inv_uom != _prod_uom:
                            _std_price = uom_obj._compute_price(cr, uid, _inv_uom, _std_price, to_uom_id=_prod_uom)

                        vals = {'standard_price': _std_price}
                        prod_obj.write(cr, uid, [inv_line.product_id.id], vals)
        return super(account_invoice, self).action_date_assign(cr, uid, ids, *args)

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        res = super(account_invoice, self).line_get_convert(cr, uid, x, part, date, context=None)
        res.update({
            'prod_lot_id': x.get('prod_lot_id', False),
        })
        return res

account_invoice()


class account_invoice_line(orm.Model):
    _inherit = 'account.invoice.line'

    _columns = {
        'prod_lot_id': fields.many2one('stock.production.lot', 'Serial Number', help='Production Lot to be selected on Invoice'),
        'cost_method': fields.related('product_id', 'cost_method', type='char', size=64, string='Cost Method')
    }

    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None):
        """
        This method gets the cost method of the product when selected in the invoice line
        ----------------------------------------------------------------------------------
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current Logged in User
        @param ids : Identifiers of the current Invoices
        @param product : Product in the invoice line
        @param uom : Product's UoM
        @param qty : Quantity of the Product
        @param name : Name/Description of Product
        @param type : Invoice Type
        @param partner_id : Customer/Supplier
        @param fposition_id : Fiscal Position
        @param price_unit : Unit Price in the Invoice Line
        @param currency_id : Currency of the Invoice
        @param context : Standard Dictionary
        @param company_id : Company
        @return A dictionaty containing value/warning as key and a dictionary containing field,value pair or warning-message dictionary.
        """
        res = super(account_invoice_line, self).product_id_change(cr, uid, ids, product, uom, qty, name, type, partner_id=partner_id, fposition_id=fposition_id, price_unit=price_unit, currency_id=currency_id, context=context, company_id=company_id)
        if product:
            product_rec = self.pool.get('product.product').browse(cr, uid, product, context=context)
            res['value'].update({'cost_method': product_rec and product_rec.cost_method or ''})
        return res

    def move_line_get_item(self, cr, uid, line, context=None):
        res = super(account_invoice_line, self).move_line_get_item(cr, uid, line, context=None)
        res.update({
            'prod_lot_id': line.prod_lot_id and line.prod_lot_id.id or False,
        })
        return res

account_invoice_line()


class account_move_line(orm.Model):
    _inherit = 'account.move.line'

    _columns = {
        'prod_lot_id': fields.many2one('stock.production.lot', 'Serial Number', help='Production Lot to be related with Stock Move'),
    }

account_move_line()
