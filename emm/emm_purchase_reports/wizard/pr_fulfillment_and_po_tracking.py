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
from via_reporting_utility.pgsql import list_to_pgTable
from via_jasper_report_utils.framework import register_report_wizard, wizard
from datetime import date


RPT_NAME = 'PR Fulfillment & PO Tracking'


class via_jasper_report(osv.osv_memory):
    _inherit = 'via.jasper.report'
    _description = 'PR Fulfillment & PO Tracking'

via_jasper_report()


class wizard(wizard):
    def onchange_company_ids(cr, uid, ids, com_ids, context=None):
        # Sample com_ids = [(6, 0, [14, 11])]
        if len(com_ids) == 0:
            return {
                'domain': {'dept_ids': [('company_id', '=', False)]},
                'value': {'dept_ids': False},
            }
        return {
            'domain': {'dept_ids': [('company_id', 'in', com_ids[0][2])]},
            'value': {'dept_ids': False},
        }

    def onchange_filter_selection(cr, uid, ids, filter_selection, context=None):
        res = {'value': {}}
        if filter_selection != 'pr':
            res['value'].update({
                'dept_ids': False
            })
        res['value'].update({
            'from_dt': str(date.today()),
            'to_dt': str(date.today()),
            'from_dt_2': str(date.today()),
            'to_dt_2': str(date.today()),
        })
        return res

    _onchange = {
        'company_ids': (onchange_company_ids, 'company_ids', 'context'),
        'filter_selection': (onchange_filter_selection, 'filter_selection', 'context'),
    }

    _visibility = [
        'company_ids',
        ['filter_selection', 'filter_selection_2'],
        'dept_ids',
        ['from_dt', 'to_dt'],
        ['from_dt_2', 'to_dt_2'],
    ]

    _label = {
        'filter_selection': 'Pilih Filter',
        'filter_selection_2': 'Jenis Laporan',
    }

    _selections = {
        'filter_selection': [('pr', 'Purchase Requisition'),
                             ('po', 'Purchase Order')],
        'filter_selection_2': [('val', 'Nilai Rupiah'),
                               ('qty', 'Jumlah Produk')],
    }

    _required = [
        'filter_selection',
        'filter_selection_2',
        'from_dt',
        'to_dt',
        'from_dt_2',
        'to_dt_2',
    ]

    _label = {
        'from_dt': 'PR Date From',
        'from_dt_2': 'PO Date From',
    }

    _attrs = {
        'dept_ids': "{'readonly': [('filter_selection','!=','pr')]}",
        'from_dt': ("{'invisible': [('filter_selection','=','po')],"
                    " 'required': [('filter_selection','=','pr')]}"),
        'to_dt': ("{'invisible': [('filter_selection','=','po')],"
                  " 'required': [('filter_selection','=','pr')]}"),
        'from_dt_2': ("{'invisible': [('filter_selection','!=','po')],"
                      " 'required': [('filter_selection','=','po')]}"),
        'to_dt_2': ("{'invisible': [('filter_selection','!=','po')],"
                    " 'required': [('filter_selection','=','po')]}"),
    }

    _defaults = {
        'filter_selection': lambda self, cr, uid, ctx: 'pr',
        'filter_selection_2': lambda self, cr, uid, ctx: 'qty',
    }

    def validate_parameters(self, cr, uid, form, context=None):
        if len(form.company_ids) == 0:
            raise osv.except_osv(_('Caution !'),
                                 _('No page will be printed !'))

    def print_report(self, cr, uid, form, context=None):
        self.validate_parameters(cr, uid, form, context=context)

        if form.filter_selection == 'po':
            form.write({
                'from_dt': form.from_dt_2,
                'to_dt': form.to_dt_2,
            }, context=context)

        if form.filter_selection_2 == 'val':
            return RPT_NAME + ' (By Value)'
        else:
            return RPT_NAME + ' (By Quantity)'

register_report_wizard(RPT_NAME, wizard)
