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
import time
import netsvc
from tools.translate import _


class lot_valuation(orm.Model):
    _name = 'lot.valuation'
    _description = "Lot Valuation/Revaluation"
    _rec_name = 'product_id'

    def _get_qty(self, cr, uid, ids, name, args, context=None):
        """
        A method to get the product's available quantity
        ------------------------------------------------------
        @param self: object pointer
        @param cr: database cursor
        @param uid: current logged in user
        @param ids: Current record(s) Identifier(s)
        @param name: name of the field
        @param args: Other arguments
        @context: Standard Dictionary
        @return: A dictionary holding the id of the record as key and value to be stored in the functional field as value.
        """
        res = {}
        for valuation in self.browse(cr, uid, ids, context=context):
            qty = valuation.lot_id.stock_available
            for move in valuation.lot_id.move_ids:
                if move.picking_id.type == 'out':
                    qty += move.product_qty
                elif move.picking_id.type in ('in', 'internal'):
                    if move.location_dest_id.usage != 'internal':
                        qty += move.product_qty
            res[valuation.id] = qty
        return res

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True, domain=[('type', '!=', 'service')],
            help='Product to be used in the Valuation'),
        'lot_id': fields.many2one('stock.production.lot', 'Serial Number', required=True,
            help='Production Lot no of the product in the valuation'),
        'date': fields.date('Date', help='Date when the valuation is performed'),
        'qty': fields.function(_get_qty, string='Quantity',
            help='Available Quantity of Product'),
        'product_uom_id': fields.many2one('product.uom', 'Uom', readonly=True,
            help='Unit of Measure for the valuation product'),
        'existing_cost_price': fields.float('Existing Cost Price',
            help="Existing Cost Price of the Product, in Company's Operating Currency"),
        'valuation_cost_price': fields.float('Valuation Cost Price',
            help="The New Cost Price To be updated in the valuation, in Company's Operating Currency"),
        'state': fields.selection([('draft', 'Draft'), ('scheduled', 'Scheduled'), ('done', 'Done'), ('cancel', 'Canceled')],
            'State', readonly=True, help='State of the valuation'),
        'warning': fields.text('Warning', readonly=True, help='This field contains the configuration warning!'),
        'account_move_ids': fields.many2many('account.move', 'lot_valuation_account_move_rel', 'lot_valuation_id', 'account_move_id', 'Journal Entries', readonly=True),
    }

    _defaults = {
        'date': fields.date.context_today,
        'state': 'draft',
    }

    def onchange_product_id(self, cr, uid, ids, product_id):
        """
        This Method Changes the UoM in the valuation related to the product.
        It updates the existing cost price if the cost method is standard or average
        ----------------------------------------------------------------------------
        @param self: object pointer
        @param cr: database cursor
        @param uid: current logged in user
        @param ids: Current record(s) Identifier(s)
        @param product_id: Identifier of the Product
        @return A dictionary that contains a nested dictionary having field value pair
        """
        res = {}
        product = self.pool.get('product.product').browse(cr, uid, product_id)
        res['value'] = {'lot_id': False, 'existing_cost_price': 0.0}
        if product_id:
            res['value'].update({'product_uom_id': product.uom_id.id})
            if product.cost_method in ('standard', 'average'):
                res['value'].update({'existing_cost_price': product.standard_price})
        return res

    def create(self, cr, uid, vals, context=None):
        """
        Overridden create method to update the UoM related to product in valuation
        --------------------------------------------------------------------------
        @param self: object pointer
        @param cr: database cursor
        @param uid: current logged in user
        @param vals: Dictionary of fields and their values to create the record
        @param context: Standard Dictionary
        @return id: Identifier of the newly created record
        """
        _product_id = vals.get('product_id', False)
        if _product_id:
            _tmp = self.onchange_product_id(cr, uid, [], _product_id)
            _tmp = _tmp and _tmp['value'] and _tmp['value'].get('product_uom_id', False)
            vals.update({'product_uom_id': _tmp})
        return super(lot_valuation, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """
        Overridden write method to update the UoM related to product in valuation
        -------------------------------------------------------------------------
        @param self: object pointer
        @param cr: database cursor
        @param uid: current logged in user
        @param ids: Current record(s) Identifier(s)
        @param vals: Dictionary of fields and their values to update the record
        @param context: Standard Dictionary
        @return True
        """
        _product_id = vals.get('product_id', False)
        if _product_id:
            _tmp = self.onchange_product_id(cr, uid, ids, _product_id)
            _tmp = _tmp and _tmp['value'] and _tmp['value'].get('product_uom_id', False)
            vals.update({'product_uom_id': _tmp})
        return super(lot_valuation, self).write(cr, uid, ids, vals, context=context)

    def onchange_lot_id(self, cr, uid, ids, lot_id):
        """
        It updates the existing cost price if the cost method is fifo, lifo or lot based
        -------------------------------------------------------------------------------
        @param self: object pointer
        @param cr: database cursor
        @param uid: current logged in user
        @param ids: Current record(s) Identifier(s)
        @param lot_id: Identifier of the Production Lot
        @return dictionary that contains a nested dictionary having field value pairs
        """
        res = {}
        lot = lot_id and self.pool.get('stock.production.lot').browse(cr, uid, lot_id) or False
        if lot:
            _tmp = lot.product_id and lot.product_id.id or False
            if _tmp:
                _tmp = self.onchange_product_id(cr, uid, ids, lot.product_id.id)
                _tmp = _tmp and _tmp['value'] and _tmp['value'].get('existing_cost_price', False)

            res['value'] = {'existing_cost_price': _tmp or lot.cost_price_per_unit}
        return res

    def valuation_done(self, cr, uid, ids, context=None):
        """
        This method changes the prices and sends the valuation to Done state.
        It also creates valuation moves for the price differences in the locaitons.
        ---------------------------------------------------------------------------
        @param self: object pointer
        @param cr: database cursor
        @param uid: current logged in user
        @param ids: Current record(s) Identifier(s)
        @param context: Standard Dictionary
        @return True/False
        """
        if context is None:
            context = {}
        acc_mov_obj = self.pool.get('account.move')
        acc_mov_line_obj = self.pool.get('account.move.line')
        user_obj = self.pool.get('res.users')
        stock_obj = self.pool.get('stock.move')
        prod_obj = self.pool.get('product.product')
        uom_obj = self.pool.get('product.uom')
        user = user_obj.browse(cr, uid, uid, context=context)
        journal_codename = 'valuation_journal'  # Default Domain configuration code to be used

        for valuation in self.browse(cr, uid, ids, context=context):
            product_in_acct = valuation.product_id.property_stock_account_input.id or valuation.product_id.categ_id.property_stock_account_input_categ.id
            product_out_acct = valuation.product_id.property_stock_account_output.id or valuation.product_id.categ_id.property_stock_account_output_categ.id
            diff = valuation.valuation_cost_price - valuation.existing_cost_price
            valuation_journal_id = user.company_id.get_journal_for(journal_codename, context=context)
            _account_move_to_link = []
            if diff != 0.0:
                # Account for UOM Difference (Valuation UOM vs Production Lot's Product UOM)
                # If Valuation UOM is not specified, assume that it will use Product UOM
                _val_uom = valuation.product_uom_id and valuation.product_uom_id.id or valuation.product_id.uom_id.id or False
                _prod_uom = valuation.lot_id and valuation.lot_id.product_id.uom_id.id or valuation.product_id.uom_id.id or False
                _uom_diff = (_val_uom != _prod_uom)
                _new_prd_uom = _uom_diff and uom_obj._compute_price(cr, uid, _val_uom, valuation.valuation_cost_price, to_uom_id=_prod_uom) or valuation.valuation_cost_price or 0.0
                _ext_prd_uom = _uom_diff and uom_obj._compute_price(cr, uid, _val_uom, valuation.existing_cost_price, to_uom_id=_prod_uom) or valuation.existing_cost_price or 0.0

                if valuation.product_id.cost_method in ('average'):
                    datas = {
                        'new_price': _new_prd_uom,
                        'stock_output_account': product_in_acct,
                        'stock_input_account': product_out_acct,
                        'stock_journal': valuation_journal_id
                    }
                    prod_obj.do_change_standard_price(cr, uid, [valuation.product_id.id], datas, context=context)
                else:
                    if valuation.product_id.is_lot_based:
                        valuation.lot_id.write({'cost_price_per_unit': _new_prd_uom}, context=context)
                    elif valuation.product_id.cost_method == 'standard':
                        valuation.product_id.write({'standard_price': _new_prd_uom, 'old_cost_price': _ext_prd_uom}, context=context)

                    for move in valuation.lot_id.move_ids:
                        if move.state == 'done' and not(move.location_id.usage == 'internal' and move.location_dest_id.usage == 'internal'):
                            journal_id, acc_src, acc_dest, acc_valuation = stock_obj._get_accounting_data_for_valuation(cr, uid, move, context)
                            if move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal':
                                src_account = acc_src
                                dest_account = acc_valuation
                            elif move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal':
                                src_account = acc_valuation
                                dest_account = acc_dest
                            elif move.location_id.usage != 'internal' and move.location_dest_id.usage != 'internal':
                                src_account = acc_src
                                dest_account = acc_dest

                            # Account for UOM Difference (Valuation UOM vs Stock Move's UOM)
                            # If Valuation or Stock Move UOM is not specified, assume that it will use respective Product UOM
                            _sm_uom = move.prodlot_id and move.prodlot_id.product_id.uom_id.id or valuation.product_id.uom_id.id or False
                            _sm_uom_diff = (_val_uom != _sm_uom)
                            _diff_sm_uom = _sm_uom_diff and uom_obj._compute_price(cr, uid, _val_uom, diff, to_uom_id=_sm_uom) or diff or 0.0

                            # Create the move lines with the product and location amount
                            # with the diff amount of valuation price and the existing cost price
                            # In Stock Move UOM terms
                            diff_amt = _diff_sm_uom * move.product_qty
                            if not diff_amt:
                                # Do not process entries with no difference
                                continue

                            move_vals = {
                                'journal_id': valuation_journal_id,
                                'ref': 'Stock Valuation',
                            }
                            move_id = acc_mov_obj.create(cr, uid, move_vals, context=context)
                            _account_move_to_link.append(move_id)

                            vals = {
                                'name': 'Lot Valuation',
                                'credit': 0.0,
                                'debit': 0.0,
                                'product_id': valuation.product_id.id,
                                'product_uom_id': _sm_uom,
                                'quantity': move.product_qty,
                                'prod_lot_id': valuation.lot_id and valuation.lot_id.id,
                            }
                            dr1_vals = vals.copy()
                            cr1_vals = vals.copy()
                            if diff > 0.0:
                                # If the price was increased it will make
                                cr1_vals.update({'credit': diff_amt, 'account_id': src_account, 'move_id': move_id})
                                dr1_vals.update({'debit': diff_amt, 'account_id': dest_account, 'move_id': move_id})
                            else:
                                diff_amt = abs(diff_amt)
                                cr1_vals.update({'debit': diff_amt, 'account_id': src_account, 'move_id': move_id})
                                dr1_vals.update({'credit': diff_amt, 'account_id': dest_account, 'move_id': move_id})
                            acc_mov_line_obj.create(cr, uid, cr1_vals, context=context)
                            acc_mov_line_obj.create(cr, uid, dr1_vals, context=context)
                            acc_mov_obj.post(cr, uid, [move_id], context=context)
            self.write(cr, uid, valuation.id, {'state': 'done', 'account_move_ids': [(6, 0, _account_move_to_link)], 'warning': 'Valuation performed successfully'}, context=context)
        return True

    def check_accounts(self, cr, uid, ids, context=None):
        """
        This Method is used to validate the transitions of workflow.
        It checks for the product valuation accounts and location's valuation accounts.
        If the accounts are not properly configured the transition will not be completed.
        It also checks the Valuation Journal in the Company.
        ---------------------------------------------------------------------------------
        @param self: object pointer
        @param cr: database cursor
        @param uid: current logged in user
        @param ids: Identifier of the current records
        @context: Standard Dictionary
        @return True/False
        """
        valuation = self.browse(cr, uid, ids[0], context=context)
        product = valuation.product_id
        product_in_acct = product.property_stock_account_input
        product_out_acct = product.property_stock_account_output
        prod_categ_in_acct = product.categ_id.property_stock_account_input_categ
        prod_categ_out_acct = product.categ_id.property_stock_account_output_categ
        prod_categ_valuation_acct = product.categ_id.property_stock_valuation_account_id
        warn_flag = True
        warning_message = ''

        # Check Valuation Type
        if product.valuation != 'real_time':
            warning_message += _("Valuation can't be performed because valuation in product is not Real Time(automated)")
            warn_flag = False

        # Check Accounts for all the locations and products/product categories in the moves related to the lot selected in the valuation and based on the location usage(type).
        for move in valuation.lot_id.move_ids:
            loc_in_id = move.location_id.valuation_out_account_id
            loc_out_id = move.location_dest_id.valuation_in_account_id
            if move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal':
                if not (loc_in_id or product_in_acct or prod_categ_in_acct):
                        warning_message += "\n" + "Valuation can't be performed because valuation account in location %s or product %s needs to be configured!" % (move.location_id.name, move.product_id.name)
                if not prod_categ_valuation_acct:
                        warning_message += "\n" + "Valuation can't be performed because valuation account in product category: %s needs to be configured!" % move.product_id.categ_id.name
            elif move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal':
                if not prod_categ_valuation_acct:
                        warning_message += "\n" + "Valuation can't be performed because valuation account in product category: %s needs to be configured!" % move.product_id.categ_id.name
                if not (loc_out_id or product_out_acct or prod_categ_out_acct):
                        warning_message += "\n" + "Valuation can't be performed because valuation account in location %s or product %s needs to be configured!" % (move.location_dest_id.name, move.product_id.name)
            elif move.location_id.usage != 'internal' and move.location_dest_id.usage != 'internal':
                if not (loc_in_id or product_in_acct or prod_categ_in_acct):
                        warning_message += "\n" + "Valuation can't be performed because valuation account in location %s or product %s needs to be configured!" % (move.location_id.name, move.product_id.name)
                if not (loc_out_id or product_out_acct or prod_categ_out_acct):
                        warning_message += "\n" + "Valuation can't be performed because valuation account in location %s or product %s needs to be configured!" % (move.location_dest_id.name, move.product_id.name)

        # Check the Valuation Journal in the company configured or not.
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        journal_codename = 'valuation_journal'  # Default Domain configuration code to be used
        journal_id = user.company_id.get_journal_for(journal_codename, context=context)
        if not journal_id:
            warning_message += "\n" + _("Valuation can't be performed because Valuation Journal is not configured in the Company!")
            warn_flag = False
        if not warn_flag:
            self.write(cr, uid, [valuation.id], {'warning': warning_message}, context=context)
        return warn_flag

    def valuate_all_stock(self, cr, uid):
        """
        The Scheduler process used to process all the scheduled valuations.
        -------------------------------------------------------------------
        @param self: object pointer
        @param cr: database cursor
        @param uid: current logged in user
        @return True/False
        """
        wf_service = netsvc.LocalService('workflow')
        valuation_ids = self.search(cr, uid, [('state', '=', 'scheduled')])
        for valuation_id in valuation_ids:
            wf_service.trg_validate(uid, 'lot.valuation', valuation_id, 'done', cr)
        return True

lot_valuation()
