# -*- encoding: utf-8 -*-
###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
#
###############################################################################

from osv import osv, fields
from tools.translate import _
import decimal_precision as dp
from tracking_by_qty_sql import tracking_by_qty_sql
from via_jasper_report_utils.framework import register_report_wizard, wizard


RPT_NAME = 'Sales Tracking by Quantity'


class via_jasper_report(osv.osv_memory):
    _inherit = 'via.jasper.report'
    _description = 'Sales Tracking by Quantity'

    _columns = {
    }

    _defaults = {
    }

via_jasper_report()


class wizard(wizard):

    def onchange_company_ids(cr, uid, ids, com_ids, context=None):
        # Sample com_ids = [(6, 0, [14, 11])]
        if len(com_ids) == 0:
            return {
                'domain': {'customer_ids': [('company_id','=',False),('customer','=',True)]},
                'value': {'customer_ids': False},
            }
        return {
            'domain': {'customer_ids': [('company_id','in',com_ids[0][2]),('customer','=',True)]},
            'value': {'customer_ids': False},
        }

    _onchange = {
        'company_ids': (onchange_company_ids, 'company_ids', 'context'),
    }

    _visibility = [
        'company_ids',
        'customer_ids',
        ['from_dt','to_dt'],
    ]

    _required = [
    ]

    _readonly = [
    ]

    _attrs = {
    }

    _domain = {
    }

    _label = {
    }

    _defaults = {
    }

    _states = [
    ]

    _tree_columns = {
    }

    def validate_parameters(self, cr, uid, form, context=None):
        if len(form.company_ids) == 0:
            raise osv.except_osv(_('Caution !'),
                                 _('No page will be printed !'))

    def print_report(self, cr, uid, form, context=None):
        self.validate_parameters(cr, uid, form, context=context)

        _uom = dp.get_precision('Product Unit of Measure')(cr) or [2]
        _uom = _uom and _uom[1] or 0
        if _uom == 0:
            digits_uom = ('0' * _uom)
        else:
            digits_uom = '.' + ('0' * _uom)
        form.add_marshalled_data('DIGITS_UOM', digits_uom)
        form.add_marshalled_data('SQL_PARAMS', tracking_by_qty_sql())

register_report_wizard(RPT_NAME, wizard)
