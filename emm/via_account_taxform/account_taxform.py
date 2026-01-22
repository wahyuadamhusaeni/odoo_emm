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

import netsvc
from osv import fields, orm
import decimal_precision as dp
from tools.translate import _


class account_taxform(orm.Model):
    _name = "account.taxform"
    _description = "Tax Form"
    _rec_name = "taxform_id"
    logger = netsvc.Logger()

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for taxform in self.browse(cr, uid, ids, context=context):
            res[taxform.id] = {
                'amount_full': 0.0,
                'amount_untaxed': 0.0,
                'amount_discount': 0.0,
                'amount_base': 0.0,
                'amount_base_disc': 0.0,
                'amount_base_disc_tax': 0.0,
            }

            for line in taxform.taxform_line:
                res[taxform.id]['amount_full'] += line.price_unit * line.quantity
                res[taxform.id]['amount_untaxed'] += line.price_subtotal
                res[taxform.id]['amount_base'] += line.amount_base
                res[taxform.id]['amount_discount'] += line.amount_base_disc - line.amount_base

            res[taxform.id]['amount_base'] += taxform.amount_advance_payment
            res[taxform.id]['amount_base_disc'] = res[taxform.id]['amount_base'] + res[taxform.id]['amount_discount']
            res[taxform.id]['amount_base_disc_tax'] = res[taxform.id]['amount_base_disc'] + taxform.amount_tax

        return res

    def _calculate_ppnbm(self, cr, uid, ids, name, args, context=None):
        res = {}
        for taxform in self.browse(cr, uid, ids, context=context):
            res[taxform.id] = 0.0

            for line in taxform.taxform_ppnbm:
                res[taxform.id] += line.amount_tax

        return res

    def _get_branch_codes(self, cr, uid, context=None):
        res = self.pool.get('code.decode').get_company_selection_for_category(cr, uid, 'via_account_taxform', 'tax_branch_code', context=context)
        return res

    def name_get(self, cr, uid, ids, context=None):
        result = []
        for r in self.browse(cr, uid, ids, context=context):
            result.append((r.id, '%s.%s' % (r.trx_code or '', r.taxform_id or '')))
        return result

    def _compelete_number(self, cr, uid, ids, field_name, field_value, arg, context=None):
        return dict(self.name_get(cr, uid, ids, context=context))

    _columns = {
        'taxform_id': fields.char('Taxform ID', size=32, readonly=True, select=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice ID', select=True),
        'invoice_tax_id': fields.many2one('account.invoice.tax', 'Invoice Tax ID', readonly=True),
        'invoice_date': fields.related('invoice_id', 'date_invoice', type='date', relation='account.invoice', store=True, readonly=True, string='Date', select=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'partner_id': fields.related('invoice_id', 'partner_id', type='many2one', relation='res.partner', string='Partner', store=True, readonly=True, select=True),
        'partner_address_id': fields.many2one('res.partner', 'Partner Address', readonly=True),
        'company_address_id': fields.many2one('res.partner', 'Company Address', readonly=True),
        'company_npwp': fields.related('company_id', 'partner_id', 'vat', type='char', size=32, string='Company NPWP', store=True, readonly=True),
        'partner_npwp': fields.many2one('partner.info', 'Partner NPWP', readonly=True, store=True),
        'taxform_line': fields.one2many('account.taxform.line', 'taxform_id', 'Taxform Lines'),
        'taxform_line_adv': fields.one2many('account.taxform.line', 'taxform_id', 'Taxform Lines Adv'),
        'amount_tax': fields.float('Amount Tax', readonly=True),
        'amount_full': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Full Amount',
            store={
                'account.taxform': (lambda self, cr, uid, ids, c={}: ids, ['taxform_line'], 20),
            },
            multi='all'),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed',
            store={
                'account.taxform': (lambda self, cr, uid, ids, c={}: ids, ['taxform_line'], 20),
            },
            multi='all'),
        'amount_discount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Discount',
            store={
                'account.taxform': (lambda self, cr, uid, ids, c={}: ids, ['taxform_line'], 20),
            },
            multi='all'),
        'amount_advance_payment': fields.float('Amount Advance Payment', readonly=True),
        'amount_base': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Base',
            store={
                'account.taxform': (lambda self, cr, uid, ids, c={}: ids, ['taxform_line'], 20),
            },
            multi='all'),
        'amount_base_disc': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Discounted Amount',
            store={
                'account.taxform': (lambda self, cr, uid, ids, c={}: ids, ['taxform_line'], 20),
            },
            multi='all'),
        'amount_base_disc_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Discounted Amount with Tax',
            store={
                'account.taxform': (lambda self, cr, uid, ids, c={}: ids, ['taxform_line'], 20),
            },
            multi='all'),
        'taxform_taxes': fields.one2many('account.taxform.taxes', 'taxform_id', 'Taxes'),
        'taxform_ppnbm': fields.one2many('account.taxform.taxes', 'taxform_id', 'PPnBM', domain=[('tax_cat', '=', 'ppnbm')]),
        'amount_total_ppnbm': fields.function(_calculate_ppnbm, digits_compute=dp.get_precision('Account'), string='Total PPnBM',
            store={
                'account.taxform': (lambda self, cr, uid, ids, c={}: ids, ['taxform_ppnbm', 'taxform_line'], 30),
            },
            multi=False),
        'state': fields.selection([('draft', 'Draft'), ('printed', 'Printed'), ('canceled', 'Canceled'), ],
            'State', readonly=True, select=True),
        'counter': fields.integer('Counter', readonly=True),
        'due_date_from': fields.function(lambda *a, **k: {}, method=True, type='date', string="Due date from"),
        'due_date_to': fields.function(lambda *a, **k: {}, method=True, type='date', string="Due date to"),
        'user_name': fields.char('Name', size=32, readonly=True, select=True),
        'signature': fields.char('Signature', size=32, readonly=True, select=True),
        'trx_type': fields.selection([
            ('hargajual', 'Harga Jual'),
            ('penggantian', 'Penggantian'),
            ('uangmuka', 'Uang Muka'),
            ('termin', 'Termin')],
            'Taxform Type'),
        'trx_code': fields.char('Transaction Code', size=3),
        'branch_code': fields.selection(_get_branch_codes, 'Branch Code'),
        'complete_number': fields.function(_compelete_number, type='char', method=True, store=False, string='Taxform Number'),
    }

    _defaults = {
        'state': 'draft',
        'counter': 0,
        'taxform_id': '/',
        'trx_type': 'hargajual',
    }

    def get_partner_npwp(self, cr, uid, partner_id, context=None):
        res_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'via_account_taxform', 'partner_parameter_taxform')
        res_id_code = self.pool.get(res_id[0]).browse(cr, uid, res_id[1])
        npwp_crit = [('parameter_id', '=', res_id_code.code), ('partner_id', '=', partner_id)]
        npwp_ids = self.pool.get('partner.info').search(cr, uid, npwp_crit, context=context)

        if len(npwp_ids) == 0:
            raise orm.except_orm(_('Error !'), _('Partner does not have "NPWP" !'))

        # Only return the first record
        return npwp_ids[0]

    def get_company_address(self, cr, uid, company_id, context=None):
        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        company_partner_id = company_obj.partner_id.id

        res = self.pool.get('res.partner').address_get(cr, uid, [company_partner_id], ['default'])
        company_address_id = res['default']

        return company_address_id

    def get_amount_advance(self, cr, uid, invoice_id, context=None):
        amount_advance = 0.0
        _inv_obj = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        for _inv_line_obj in _inv_obj.invoice_line:
            if (len(_inv_line_obj.invoice_line_tax_id) > 0) and (_inv_line_obj.price_subtotal < 0):
                amount_advance += (_inv_line_obj.price_subtotal / (1 - (_inv_line_obj.discount or 0.0)))
        return amount_advance

    def compute_taxes(self, cr, uid, invoice_id, tax_category='', context=None):
        taxes = {}  # This variable will contain the calculcated tax per account tax line in (dpp, tax) tuples
        _tax_obj = self.pool.get('account.tax')
        _inv_obj = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)

        if (not tax_category) or (tax_category in ['vat']):
            # VAT need special treatment not covered in this method
            return []

        for _inv_line_obj in _inv_obj.invoice_line:
            for r in _inv_line_obj.invoice_line_tax_id:
                if r.tax_category == tax_category:
                    taxes[r.id] = {'tax_base': 0.0, 'amount_tax': 0.0}
                    line_tax = _tax_obj.compute_all(cr, uid, [r], _inv_line_obj.price_subtotal, 1)
                    taxes[r.id].update({
                        'tax_base': taxes[r.id].get('tax_base', 0.0) + line_tax.get('total', 0.0),
                        'amount_tax': taxes[r.id].get('amount_tax', 0.0) + line_tax.get('taxes', [])[0].get('amount', 0.0)
                    })

        _created_ids = []
        _taxes_pool = self.pool.get('account.taxform.taxes')
        _tax_ids = taxes.keys()
        for item in _tax_obj.browse(cr, uid, _tax_ids, context=context):
            _created_ids.append(_taxes_pool.create(cr, uid, {
                'invoice_id': invoice_id,
                'tax_cat': tax_category,
                'tax_id': item.id,
                'tariff': item.amount,
                'tax_base': taxes.get(item.id, {}).get('tax_base', 0.0),
                'amount_tax': taxes.get(item.id, {}).get('amount_tax', 0.0),
            }))

        return _created_ids

    def create_taxform_lines(self, cr, uid, invoice_id, context=None):
        res = []
        _line_pool = self.pool.get('account.taxform.line')
        _inv_obj = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        for _inv_line_obj in _inv_obj.invoice_line:
            if (len(_inv_line_obj.invoice_line_tax_id) > 0) and (_inv_line_obj.price_subtotal > 0):
                _val = {'invoice_line_id': _inv_line_obj.id}
                res.append(_line_pool.create(cr, uid, _val, context=context))

        return res

    def get_invoice_info(self, cr, uid, invoice_id, context=None):
        res = {}
        _inv = invoice_id and self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context) or False
        if _inv:
            # Company taxed
            _tax_co = _inv.company_id.legal_id or _inv.company_id or False
            _tax_uid = _inv.company_id.user_id and _inv.company_id.user_id.id or uid
            partner_npwp_id = _inv.partner_id and self.get_partner_npwp(cr, uid, _inv.partner_id.id, context=context) or False

            # Addresses
            partner_address_id = _inv.partner_id and _inv.partner_id.id or False
            company_address_id = _tax_co and self.get_company_address(cr, _tax_uid, _tax_co.id, context=context) or False

            # Signatory
            _doc_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'via_account_taxform', 'doc_type_taxform')
            _coy_npwp_sig = self.pool.get('res.company').get_signatory_by_doc_id(cr, _tax_uid, _tax_co.id, _doc_id[1], context=context) or False

            # Taxes
            taxform_line_ids = _inv and self.create_taxform_lines(cr, uid, _inv.id, context=context) or []
            amount_advance_payment = _inv and self.get_amount_advance(cr, uid, _inv.id, context=context) or 0.0
            ppnbms = _inv and self.compute_taxes(cr, uid, _inv.id, tax_category='ppnbm', context=context) or []

            res = {
                'partner_npwp': partner_npwp_id,
                'partner_address_id': partner_address_id,
                'company_id': _tax_co.id,
                'company_address_id': company_address_id,
                'taxform_line': [(4, lid) for lid in taxform_line_ids],
                'amount_tax': _inv and _inv.amount_tax or 0.0,
                'amount_advance_payment': amount_advance_payment,
                'signature': _coy_npwp_sig and _coy_npwp_sig.signature or '',
                'user_name': _coy_npwp_sig and _coy_npwp_sig.name or '',
                'taxform_taxes': [(4, lid) for lid in ppnbms],
            }
        return res

    def create(self, cr, uid, vals, context=None):
        taxform_id = self.pool.get('account.taxform').search(cr, uid, [('invoice_id', '=', vals['invoice_id'])], context=context)
        res = taxform_id and taxform_id[0] or False
        _inv_id = vals.get('invoice_id', False)

        if not res and _inv_id:
            _vals = self.get_invoice_info(cr, uid, _inv_id, context=context)
            vals.update(_vals)
            _taxform_id = super(account_taxform, self).create(cr, uid, vals, context=context)
            res = _taxform_id

        return res

    def write(self, cr, uid, ids, vals, context=None):
        _inv_id = vals.get('invoice_id', False)
        if _inv_id:
            _vals = self.get_invoice_info(cr, uid, _inv_id, context=context)
            vals.update(_vals)

        res = super(account_taxform, self).write(cr, uid, ids, vals, context=context)
        return res

    def _report_taxform(self, cr, uid, ids, rml='', rpt_name='', context=None):
        if context is None:
            context = {}

        # This method assumes that only 1 report_taxform is to be printed
        res = self.pool.get('account.taxform').browse(cr, uid, ids[0])
        if res['taxform_id'] != '/' and res['state'] != 'canceled':
            counter = res.counter + 1
            self.write(cr, uid, ids, {'state': 'printed', 'counter': counter}, context=context)

        try:
            _template = self.pool.get('ir.model.data').get_object(cr, uid, 'via_account_taxform', 'via_account_taxform_form_template', context=context)
            _template = _template and _template.act_report_id and self.pool.get('ir.actions.report.xml').copy_data(cr, uid, _template.act_report_id.id, context=context) or False

            _datas = {
                'ids': ids,
            }
            _template.update({'datas': _datas, 'context': context.copy()})
            return _template
        except:
            raise orm.except_orm(_('Error !'), _('Cannot load taxform print template!  Contact your administrator'))

    def report_taxform(self, cr, uid, ids, context=None):
        # _rml = 'taxform/report/account_taxform_report.rml'
        # _rpt_name = 'account.taxform.report'
        if context is None:
            context = {}
        _ctx = context.copy()
        _ctx.update({'via_at_variant': 'normal'})
        return self._report_taxform(cr, uid, ids, context=_ctx)

    def report_taxform_one_page(self, cr, uid, ids, context=None):
        # _rml = 'taxform/report/account_taxform_report_one_page.rml'
        # _rpt_name = 'account.taxform.report.one.page'
        if context is None:
            context = {}
        _ctx = context.copy()
        _ctx.update({'via_at_variant': '1page'})
        return self._report_taxform(cr, uid, ids, context=_ctx)

    def report_taxform_preprinted(self, cr, uid, ids, context=None):
        # _rml = 'taxform/report/account_taxform_report_preprinted.rml'
        # _rpt_name = 'account.taxform.report.preprinted'
        if context is None:
            context = {}
        _ctx = context.copy()
        _ctx.update({'via_at_variant': 'preprinted'})
        return self._report_taxform(cr, uid, ids, context=_ctx)

    def action_cancel_taxform(self, cr, uid, ids, context=None):
        _reusable_pool = self.pool.get('account.taxform.reusable.sequences')
        for _obj in self.pool.get('account.taxform').browse(cr, uid, ids, context=context):
            _obj.write({'state': 'canceled'}, context=context)
            _reusable_id = _reusable_pool.search(cr, uid, [('taxform_sequence', '=', _obj.taxform_id)], context=context)
            if _reusable_id:
                _reusable_pool.write(cr, uid, _reusable_id, {'legal_id': _obj.company_id.id, 'reusable': True, }, context=context)
            else:
                _reusable_pool.create(cr, uid, {'legal_id': _obj.company_id.id, 'taxform_sequence': _obj.taxform_id, }, context=context)

        return True

    def _run_action(self, cr, uid, ids, attrs={}, context=None):
        attrs.update({
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'nodestroy': False,
            'target': 'new',
            'domain': '[]',
            'context': {'active_taxform': ids[0]}
        })
        return attrs

    def action_select_existing_sequence(self, cr, uid, ids, context=None):
        _attrs = {
            'name': _("Select Sequence"),
            'res_model': 'account.taxform.select_existing_sequence',
        }
        return self._run_action(cr, uid, ids, attrs=_attrs, context=context)

    def action_call_create_new_sequence(self, cr, uid, ids, context=None):
        _attrs = {
            'name': _("Create New Sequence"),
            'res_model': 'account.taxform.create_new_sequence',
        }
        return self._run_action(cr, uid, ids, attrs=_attrs, context=context)

    def action_create_new_sequence(self, cr, uid, ids, trx_code, branch_code, context=None):
        _seq_pool = self.pool.get('ir.sequence')
        for _obj in self.pool.get('account.taxform').browse(cr, uid, ids, context=context):
            if _obj.taxform_id == '/':
                _uid = _obj.company_id.user_id and _obj.company_id.user_id.id or False
                _seq_id = _obj.company_id.get_taxform_sequence(context=context)
                taxform_id = _seq_pool.get_id(cr, _uid, _seq_id, context=context)
                _obj.write({'taxform_id': taxform_id, 'branch_code': branch_code, 'trx_code': trx_code}, context=context)

        return {
            'name': _("Taxform"),
            'view_mode': 'form',
            'view_type': 'tree, form',
            'res_id': ids[0],
            'res_model': 'account.taxform',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'context': context
        }

    def action_refresh(self, cr, uid, ids, context=None):
        _line_pool = self.pool.get('account.taxform.line')
        for _obj in self.pool.get('account.taxform').browse(cr, uid, ids, context=context):
            _inv_line_ids = map(lambda x: x.id, _obj.invoice_id.invoice_line)
            for _line_obj in _obj.taxform_line:
                _inv_ln_id = _line_obj.invoice_line_id.id
                if _inv_ln_id in _inv_line_ids:
                    # Existing invoice line
                    _inv_line_ids.remove(_inv_ln_id)
                    _inv_info = _line_pool.get_invoice_info(cr, uid, _inv_ln_id, context=context)
                    _line_obj.write(_inv_info)
                else:
                    # Removed invoice line
                    _line_obj.unlink()
            for _inv_line_obj in self.pool.get('account.invoice.line').browse(cr, uid, _inv_line_ids, context=context):
                # New invoice line
                if (len(_inv_line_obj.invoice_line_tax_id) > 0) and (_inv_line_obj.price_subtotal > 0):
                    _val = {'taxform_id': _obj.id, 'invoice_line_id': _inv_line_obj.id}
                    _line_pool.create(cr, uid, _val, context=context)

account_taxform()
