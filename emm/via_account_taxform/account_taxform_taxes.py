# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
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


class account_taxform_taxes(orm.Model):
    _name = "account.taxform.taxes"
    _description = "Taxes related to a taxform"
    logger = netsvc.Logger()

    def _get_tax_category(self, cr, uid, context=None):
        res = self.pool.get('code.decode').get_company_selection_for_category(cr, uid, 'via_account_taxform', 'tax_category', context=context)
        return res

    def onchange_tax_amount(self, cr, uid, ids, tax_id, tax_base, context=None):
        _tax_pool = self.pool.get('account.tax')
        _obj = tax_id and _tax_pool.browse(cr, uid, tax_id, context=context) or False

        rv = {}
        if _obj:
            amount_tax = _tax_pool.compute_all(cr, uid, [_obj], tax_base, 1.0)
            amount_tax = amount_tax.get('total_included', 0.0) - amount_tax.get('total', 0.0)
            rv['value'] = {'tariff': _obj.amount, 'amount_tax': amount_tax}

        return rv

    def create(self, cr, uid, vals, context=None):
        _upd = self.onchange_tax_amount(cr, uid, [], vals.get('tax_id', False), vals.get('tax_base', 0.0), context=context)
        _upd = _upd.get('value', {})
        vals.update(_upd)
        return super(account_taxform_taxes, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        rv = False
        for _obj in self.browse(cr, uid, ids, context=context):
            if ('tax_id' in vals) or ('tax_base' in vals):
                _tax_id = vals.get('tax_id', _obj.tax_id and _obj.tax_id.id or False)
                _tax_base = vals.get('tax_base', _obj.tax_base)
                _upd = self.onchange_tax_amount(cr, uid, [], _tax_id, _tax_base, context=context)
                _upd = _upd.get('value', {})
                _vals = vals.copy()
                _vals.update(_upd)
                rv = super(account_taxform_taxes, self).write(cr, uid, [_obj.id], _vals, context=context)

        return rv

    _columns = {
        'taxform_id': fields.many2one('account.taxform', 'Taxform Id'),
        'invoice_id': fields.related('taxform_id', 'invoice_id', type="many2one", relation='account.invoice', store=True, string='Invoice'),
        'tax_cat': fields.selection(_get_tax_category, 'Tax Category'),
        'tax_id': fields.many2one('account.tax', 'Tax Id', store=True, required=True),
        'tariff': fields.related('tax_id', 'amount', type='float', string='Tariff', store=True, select=True),
        'tax_base': fields.float('Tax Base Amount', digits_compute=dp.get_precision('Account')),
        'amount_tax': fields.float('Tax Amount', digits_compute=dp.get_precision('Account'))
    }

    _defaults = {
        'tax_cat': 'ppnbm',
    }

account_taxform_taxes()
