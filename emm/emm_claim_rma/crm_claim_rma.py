# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 - 2014 Vikasa Infinity Anugrah <http: //www.infi-nity.com>
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
#    along with this program.  If not, see http: //www.gnu.org/licenses/.
#
##############################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _

CLAIM_TYPES = [
    ('customer', 'Customer'),
    ('supplier', 'Supplier'),
    ('other', 'Other')
]

__module__ = __package__.split('.')[-1]


class crm_claim(orm.Model):
    _inherit = 'crm.claim'

    def _get_default_warehouse(self, cr, uid, context=None):
        usr_pool = self.pool.get('res.users')
        usr_obj = usr_pool.browse(cr, uid, uid, context=context)
        wh_obj = self.pool.get('stock.warehouse')
        wh_ids = wh_obj.search(cr, uid, [('company_id', '=', usr_obj.company_id.id)], context=context)
        if not wh_ids:
            raise orm.except_orm(_('Error!'), _('User\'s current company does not have warehouse setup.  Please set up warehouse for company %s before proceeding.') % (usr_obj.company_id.name))
        return wh_ids[0]

    def _get_sequence_claim_number(self, cr, uid, context=None):
        _seq_code = False
        res = '/'
        try:
            _seq_code = self.pool.get('ir.model.data').get_object(cr, uid, 'emm_claim_rma', 'ir_seq_claim', context=context)
        except ValueError:
            pass
        except Exception:
            raise
        finally:
            if _seq_code:
                res = self.pool.get('ir.sequence').get(cr, uid, _seq_code.code, context=context) or '/'
        return res

    def _get_sequence_rma_number(self, cr, uid, context=None):
        _seq_code = self.pool.get('ir.model.data').get_object(cr, uid, 'emm_claim_rma', 'ir_seq_rma', context=context)
        res = self.pool.get('ir.sequence').get(cr, uid, _seq_code.code, context=context) or '/'
        return res

    def _get_selection(self, cr, uid, context=None):
        return self.pool.get('code.decode').get_selection_for_category(cr, uid, 'emm_claim_rma', 'claim_type_parameter', context=context)

    def _get_picking(self, cr, uid, ids, context=None):
        result = [_obj.claim_id.id for _obj in self.pool.get('stock.picking').browse(cr, uid, ids, context=context) if _obj.claim_id]
        return list(set(result))

    def _get_invoice(self, cr, uid, ids, context=None):
        result = [_obj.claim_id.id for _obj in self.pool.get('account.invoice').browse(cr, uid, ids, context=context) if _obj.claim_id]
        return list(set(result))

    def returned_field(self, cr, uid, ids, name, args, context=None):
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = {
                "returned": False,
                "ready_to_receive": False
            }
            for picking in _obj.picking_ids:
                if (picking.type == 'in'):
                    if picking.state in ['done']:
                        res[_obj.id]['returned'] = True
                    elif picking.state in ['assigned']:
                        res[_obj.id]['ready_to_receive'] = True
        return res

    def refund_field(self, cr, uid, ids, name, args, context=None):
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = bool(len([line.id for line in _obj.refund_ids if (line.state == 'paid')]))
        return res

    def _check_drafts_field(self, cr, uid, ids, name, args, context=None):
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = _obj.prodlot_id and _obj.prodlot_id._check_drafts(context=context).get(_obj.prodlot_id.id, False) or False
        return res

    def _check_other_claims_field(self, cr, uid, ids, name, args, context=None):
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = self.check_other_claims(cr, uid,
                claim_id=_obj.id,
                prodlot_id=_obj.prodlot_id and _obj.prodlot_id.id or False,
                product_id=_obj.prodlot_id and _obj.prodlot_id.product_id and _obj.prodlot_id.product_id.id or False,
                partner_ids=_obj.partner_id and [_obj.partner_id.id] or [],
                context=context)
        return res

    # Check whether there are other Claim with the same Serial Number, Product and Partner in non Cancelled state
    def check_other_claims(self, cr, uid, claim_id=None, prodlot_id=None, product_id=None, partner_ids=None, context=None):
        _other_claims = []
        _dom = []
        if prodlot_id:
            _dom.append(('prodlot_id', '=', prodlot_id))
        if product_id:
            _dom.append(('product_id', '=', product_id))
        if partner_ids:
            _dom.append(('partner_id', 'in', partner_ids))
        if claim_id:
            _dom.append(('id', '!=', claim_id))
        if _dom:
            _dom.append(('state', 'not in', ['cancel']))
            _other_claims = self.search(cr, uid, _dom, context=context)
        return len(_other_claims) or False

    _columns = {
        'claim_number': fields.char('Claim Number', readonly=True, states={'draft': [('readonly', False)]}, required=True, select=True,
            help="Company internal unique claim number"),
        'rma_number': fields.char('RMA Number', size=64, select=True, readonly=True, help="RMA number for this claim"),
        'claim_type': fields.selection(CLAIM_TYPES, string='Claim Type', required=True, readonly=True,
            help="Customer: from customer to company.\n Supplier: from company to supplier."),
        'claim_method': fields.selection(_get_selection, 'Claim Method', readonly=True, states={'draft': [('readonly', False)], 'open': [('readonly', False)]}, help="Methods of claim and its resolution."),
        'product_id': fields.many2one('product.product', 'Product',
            help='The product being claimed.'),
        'serial_number': fields.char('Serial Number', size=64,
            help='Type in the Serial Number to search.'),
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial Number',
            help='Serial Number being claimed..'),
        'invoice_line': fields.many2many('account.invoice.line', string='Invoices',
            help='Customer Invoice Lines of the claimed product/serial number'),
        'claimed_moves': fields.many2many('stock.move', string='Claimed Products',
            help='Stock Moves of the claimed product/serial number'),
        'delivery_address_id': fields.many2one('res.partner', string='Partner delivery address',
            help="This address will be used to deliver repaired or replacement products."),
        'warehouse_id': fields.many2one('stock.warehouse', string='Warehouse',
            required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'refund_ids': fields.one2many('account.invoice', 'claim_id', 'Refunds'),
        'picking_ids': fields.one2many('stock.picking', 'claim_id', 'Stock Moves'),
        'returned': fields.function(returned_field, method=True, type='boolean',
            store={
                'crm.claim': (lambda self, cr, uid, ids, c={}: ids, ['picking_ids'], 20),
                'stock.picking': (_get_picking, None, 20)
            }, string='Returned', readonly=True, multi="picking_flag"),
        'ready_to_receive': fields.function(returned_field, method=True, type='boolean',
            store={
                'crm.claim': (lambda self, cr, uid, ids, c={}: ids, ['picking_ids'], 20),
                'stock.picking': (_get_picking, None, 20)
            }, string='Ready to Receive', readonly=True, multi="picking_flag"),
        'refund': fields.function(refund_field, method=True, type='boolean',
            store={
                'crm.claim': (lambda self, cr, uid, ids, c={}: ids, ['invoice_ids'], 20),
                'account.invoice': (_get_invoice, None, 20),
            }, string='Refund', readonly=True),
        'has_drafts': fields.function(_check_drafts_field, method=True, type='boolean', string='Has Draft Documents', readonly=True),
        'has_other_claim': fields.function(_check_other_claims_field, method=True, type='boolean', string='Has Other Claims', readonly=True),
        'note': fields.text('Note', readonly=True, states={'draft': [('readonly', False)], 'open': [('readonly', False)]}),
    }

    _defaults = {
        'claim_type': 'customer',
        'claim_number': '/',
        'state': 'draft',
        'returned': False,
        'refund': False,
        'warehouse_id': _get_default_warehouse,
        'rma_number': False,
        'ready_to_receive': False,
    }

    _sql_constraints = [
        ('company_number_uniq', 'unique(claim_number, company_id)', 'Claim Number must be unique in each Company!'),
    ]

    def button_dummy(self, cr, uid, ids, context=None):
        return True

    # Generate and assign RMA Number
    def generate_rma(self, cr, uid, ids, context=None):
        for claim in self.browse(cr, uid, ids, context=context):
            _new_claim_number = self._get_sequence_rma_number(cr, uid, context=context)
            claim.write({'rma_number': _new_claim_number})
        return True

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if isinstance(ids, (int, long)):
            ids = [ids]

        for _obj in self.browse(cr, uid, ids, context=context):
            res.append((_obj.id, "[{0}] {1}".format(_obj.claim_number or '', _obj.name)))

        return res

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}

        # Additional defaults
        _default = {
            'refund_ids': [],
            'picking_ids': [],
            'claimed_moves': [],
            'invoice_line': [],
            'rma_number': False,
        }
        default.update(_default)
        _stage_default = self._defaults.get('stage_id', False)
        if _stage_default:
            if callable(_stage_default):
                _stage_default = self._defaults['stage_id'](self, cr, uid, context)
                default.update({'stage_id': _stage_default})

        return super(crm_claim, self).copy_data(cr, uid, id, default=default, context=context)

    def onchange_claim_type(self, cr, uid, ids, claim_type, context=None):
        _dom = {'partner_id': [('id', '=', 0)]}
        _val = {'partner_id': False}
        _domain = []
        if claim_type:
            if claim_type in ['customer', 'other']:
                _domain.append(('customer', '=', True))

            if claim_type in ['supplier', 'other']:
                _domain.append(('supplier', '=', True))

            if len(_domain) > 1:
                _domain.insert(0, '|')

            if _domain:
                _dom = {'partner_id': _domain}

        return {'domain': _dom, 'value': _val}

    def onchange_partner_id(self, cr, uid, ids, part, email=False, context=None):
        res = super(crm_claim, self).onchange_partner_id(cr, uid, ids, part, email=email)

        if part:
            _val = res.get('value', {})
            _curr_email = _val.get('email_from', False)
            _curr_phone = _val.get('partner_phone', False)

            # Try to get the information from parent if not specified
            _part_obj = self.pool.get('res.partner').browse(cr, uid, part, context=context)
            if (not (_curr_email and _curr_phone)) and _part_obj.parent_id:
                _curr_email = ((not _curr_email) and _part_obj.parent_id.email) or _curr_email
                _curr_phone = ((not _curr_phone) and _part_obj.parent_id.phone) or _curr_phone

            # Try to get the information from the children under if still not specified
            if (not (_curr_email and _curr_phone)):
                for _children in _part_obj.child_ids:
                    _curr_email = ((not _curr_email) and _children.email) or _curr_email
                    _curr_phone = ((not _curr_phone) and _children.phone) or _curr_phone

            # Try to get the information from the children under the same parent if still not specified
            if (not (_curr_email and _curr_phone)) and _part_obj.parent_id:
                for _children in _part_obj.parent_id.child_ids:
                    _curr_email = ((not _curr_email) and _children.email) or _curr_email
                    _curr_phone = ((not _curr_phone) and _children.phone) or _curr_phone

            res['value'].update({
                'email_from': _curr_email,
                'partner_phone': _curr_phone,
            })

        return res

    def onchange_process_serial_number(self, cr, uid, ids, serial_number, product_id, partner_id, warehouse_id, context=None):
        # _prodlot_pool = self.pool.get('stock.production.lot')
        _val = {}
        _warning = {}
        _search_dom = [('state', '=', 'done'), ('picking_id.type', '=', 'out')]

        # Filtering based on serial_number and product_id(if given by user)
        _search_dom.append(['prodlot_id.name', 'ilike', serial_number])
        if product_id:
            _search_dom.append(['prodlot_id.product_id', '=', product_id])

        # Choose company (implemented as parent_id in res.partner) of partner_id if any
        _partners = [0]
        _partner_id = partner_id and self.pool.get('res.partner').browse(cr, uid, partner_id, context=context) or False
        if _partner_id:
            _partners = [partner_id]
            if _partner_id.parent_id:
                _partners.append(_partner_id.parent_id.id)
                _partners.extend([_child.id for _child in _partner_id.parent_id.child_ids])
            _search_dom.append(('picking_id.partner_id', 'in', _partners))

        # Filtering based on state of stock_move, partner_id, type of stock_picking, and latest date
        _move_id = self.pool.get('stock.move').search(cr, uid, _search_dom, limit=1, order='date DESC', context=context)

        _move = _move_id and self.pool.get('stock.move').browse(cr, uid, _move_id[0], context=context) or False
        if _move:
            if not _partner_id:
                _warning = {
                    'title': _('Warning'),
                    'message': _('No Partner is specified. Please specify Partner first.'),
                }
            else:
                _val = {'claimed_moves': [(6, 0, _move_id)]}
                _val.update({'prodlot_id': _move.prodlot_id and _move.prodlot_id.id or False})

                # Look for account.invoice.line according to the choosen stock.move
                _invoice_line_id = []
                delivery_address_id = False
                for line in _move.sale_line_id.invoice_lines or []:
                    if line.invoice_id.state not in ['draft', 'cancel']:
                        _invoice_line_id.append(line.id)
                        delivery_address_id = line.invoice_id.partner_id.id

                if _invoice_line_id:
                    _val.update({'invoice_line': [(6, 0, _invoice_line_id)]})

                if delivery_address_id:
                    _val.update({'delivery_address_id': delivery_address_id})

                if _move.prodlot_id:
                    _val.update({'serial_number': _move.prodlot_id.name})
                    _val.update({'has_draft': _move.prodlot_id._check_drafts(context=context).get(_move.prodlot_id.id, False)})
                    _val.update({'product_id': _move.prodlot_id.product_id and _move.prodlot_id.product_id.id or False})
                    _has_other_claims = self.check_other_claims(cr, uid,
                        claim_id=ids and ids[0] or False, prodlot_id=_move.prodlot_id.id,
                        product_id=_val.get('product_id', False), partner_ids=_partners, context=context)
                    _val.update({'has_other_claim': _has_other_claims})

        elif _partner_id:
            if product_id:
                _warning = {
                    'title': _('Warning'),
                    'message': _('No Transferred Delivery Order to %s is found for Serial Number with "%s" pattern for the specified product.') % (_partner_id.name, serial_number, ),
                }
            else:
                _warning = {
                    'title': _('Warning'),
                    'message': _('No Transferred Delivery Order to %s is found for Serial Number with "%s" pattern.') % (_partner_id.name, serial_number, ),
                }
        else:
            _warning = {
                'title': _('Warning'),
                'message': _('No Transferred Delivery Order is found for Serial Number with "%s" pattern for the specified product.') % (serial_number, ),
            }

        return {'value': _val, 'warning': _warning}

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

        # Because claimed_moves and invoice_line are readonly, vals has to be updated.
        serial_number = vals.get('serial_number', '')
        product_id = vals.get('product_id', False)
        partner_id = vals.get('partner_id', False)
        warehouse_id = vals.get('warehouse_id', False)
        _to_update = self.onchange_process_serial_number(cr, uid, [], serial_number, product_id, partner_id, warehouse_id, context=context)
        vals.update(_to_update.get('value', {}))
        vals.update({'claim_number': self._get_sequence_claim_number(cr, uid, context=context)})

        return super(crm_claim, self).create(cr, uid, vals, context=context)

    def message_get_reply_to(self, cr, uid, ids, context=None):
        return [claim.section_id.message_get_reply_to()[0]
                if claim.section_id else False
                for claim in self.browse(cr, uid, ids, context=context)]

    def message_get_suggested_recipients(self, cr, uid, ids, context=None):
        recipients = super(crm_claim, self).message_get_suggested_recipients(cr, uid, ids, context=context)
        try:
            for _obj in self.browse(cr, uid, ids, context=context):
                if _obj.partner_id:
                    self._message_add_suggested_recipient(cr, uid, recipients, _obj, partner=_obj.partner_id, reason=_('Customer'))
                elif _obj.email_from:
                    self._message_add_suggested_recipient(cr, uid, recipients, _obj, email=_obj.email_from, reason=_('Customer Email'))
        except orm.except_orm:
            # No recipients found, maybe due to access right
            pass
        return recipients

    # 7.c.i Create a new method that creates an account.invoice.refund object and fill in
    # field created in 7.b.i with account.invoice.lines related to the crm.claim.
    # Then call the new action and pass the created account.invoice.refund to the action.
    def create_refund(self, cr, uid, ids, context=None):
        _refund_obj = self.pool.get('account.invoice.refund')

        _invoice_line_id = []
        for item in self.browse(cr, uid, ids, context=context):
            if not item.rma_number:
                raise orm.except_orm(_('Error'), _('Please Generate RMA number before creating refunds!'))
            _invoice_line_id.extend(list(set([line.id for line in item.invoice_line])))

        _refund_id = _refund_obj.create(cr, uid, {'invoice_lines': [(6, 0, _invoice_line_id)]}, context=context)

        try:
            _form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'emm_claim_rma', 'view_account_invoice_refund')[1]
        except ValueError:
            _form_id = False

        return {
            'name': _("Refund Invoice"),
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(_form_id, 'form')],
            'view_id': _form_id,
            'res_id': _refund_id,
            'res_model': 'account.invoice.refund',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': context
        }

    def create_return(self, cr, uid, ids, context=None):
        _obj = self.pool.get('ir.model.data').get_object(cr, uid, __module__, 'action_claim_picking_in', context=context)

        for item in self.browse(cr, uid, ids, context=context):
            if not item.rma_number:
                raise orm.except_orm(_('Error'), _('Please Generate RMA number before creating refunds!'))

        ctx = context.copy()
        ctx.update(eval(_obj.context))

        return {
            'name': _("Return"),
            'view_mode': 'form',
            'view_type': 'tree, form',
            'res_model': 'claim.create.picking',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': ctx,
        }

    def create_delivery(self, cr, uid, ids, context=None):
        _obj = self.pool.get('ir.model.data').get_object(cr, uid, __module__, 'action_claim_picking_out', context=context)

        for item in self.browse(cr, uid, ids, context=context):
            if not item.rma_number:
                raise orm.except_orm(_('Error'), _('Please Generate RMA number before creating refunds!'))

        ctx = context.copy()
        ctx.update(eval(_obj.context))

        return {
            'name': _("Return"),
            'view_mode': 'form',
            'view_type': 'tree, form',
            'res_model': 'claim.create.picking',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': ctx,
        }

    def case_open(self, cr, uid, ids, context=None):
        for claim in self.browse(cr, uid, ids, context=context):
            partner_id = claim.partner_id
            serial_number = claim.serial_number
            product_id = claim.product_id

            if not claim.claimed_moves:
                raise orm.except_orm(_('Error'), _('No item found in Claimed Moves table'))
            else:
                for move in claim.claimed_moves:
                    if move.partner_id.id == partner_id.id and move.prodlot_id.name == serial_number and move.product_id.id == product_id.id:
                        rv = super(crm_claim, self).case_open(cr, uid, ids, context=context)
                    elif move.prodlot_id.name != serial_number:
                        raise orm.except_orm(_('Error'), _('The given Serial Number doesn\'t match with item(s) in Claimed Moves'))
                    elif move.partner_id.id != partner_id.id:
                        raise orm.except_orm(_('Error'), _('The given Partner doesn\'t match with item(s) in Claimed Moves'))
                    else:
                        raise orm.except_orm(_('Error'), _('The given Product doesn\'t match with item(s) in Claimed Moves'))
        return rv
