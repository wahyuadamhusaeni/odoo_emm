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

from osv import osv, fields
from tools.translate import _
from inventory_account_sql import inventory_acc_sql
from via_reporting_utility.pgsql import list_to_pgTable
from via_jasper_report_utils.framework import register_report_wizard, wizard


RPT_NAME = 'Inventory Accounting'


class via_jasper_report(osv.osv_memory):
    _inherit = 'via.jasper.report'
    _description = 'Inventory Accounting'

via_jasper_report()


class wizard(wizard):
    def onchange_company_ids(cr, uid, ids, com_ids, context=None):
        # Sample com_ids = [(6, 0, [14, 11])]
        if len(com_ids) == 0:
            return {
                'domain': {'prod_ids': [('product_tmpl_id.company_id', '=', False)]},
                'value': {'prod_ids': False},
            }
        return {
            'domain': {'prod_ids': [('product_tmpl_id.company_id', 'in', com_ids[0][2])]},
            'value': {'prod_ids': False},
        }

    _onchange = {
        'company_ids': (onchange_company_ids, 'company_ids', 'context'),
    }

    _visibility = [
        'company_ids',
        'prod_ids',
        ['from_dt', 'to_dt'],
        'prod_group_level',
    ]

    _label = {
        'from_dt': 'Stock Date From',
    }

    _required = ['from_dt', 'to_dt', 'prod_group_level']

    def validate_parameters(self, cr, uid, form, context=None):
        if len(form.company_ids) == 0:
            raise osv.except_osv(_('Caution !'),
                                 _('No page will be printed !'))

        if len(form.prod_ids) == 0:
            raise osv.except_osv(_('Warning !'),
                                 _('Please provide Products to be reported.'))
        form.validate_prod_level(context=context)

    def print_report(self, cr, uid, form, context=None):
        self.validate_parameters(cr, uid, form, context=context)
        form.add_marshalled_data('RPT_SQL', inventory_acc_sql())

register_report_wizard(RPT_NAME, wizard)
