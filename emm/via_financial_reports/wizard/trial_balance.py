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

try:
    import release
    from osv import osv, fields
    from tools.translate import _
    from via_jasper_report_utils_account.framework import register_report_wizard  # wizard
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import osv, fields
    from openerp.tools.translate import _
    from openerp.addons.via_jasper_report_utils_account.framework import register_report_wizard  # wizard

import _financial_reports


RPT_NAME = 'Trial Balance'


class via_jasper_report(osv.osv_memory):
    _inherit = 'via.jasper.report'
    _description = 'Trial Balance'

    _columns = {
    }

    # DO NOT use the following default dictionary. Use the one in class wizard.
    # The following is presented for your information regarding the system-
    # wide defaults.
    _defaults = {
    }

via_jasper_report()


class wizard(_financial_reports.wizard):

    _visibility = [
        ['company_id', 'reporting_tree_id'],
        ['fiscalyear_id', 'target_move'],
        'use_indentation',
        'no_wrap',
        ['as_of_dt'],
        ['rpt_output', 'display_large'],
        ['reference_label', 'display_comparison'],
        'notebook:first_notebook',

        # Optional references
        {
            'notebook:first_notebook': [
                ('Filters', [
                    'date_filter',
                    ['from_dt', 'to_dt'],
                    ['from_period_id', 'to_period_id'],
                ]),
                ('Journals', [
                    'journal_ids',
                ]),
                ('Accounts', [
                    'acc_ids',
                ]),
                ('Comparison', [
                    ['comparison_label', 'fiscalyear_id_2'],
                    'date_filter_2',
                    ['from_dt_2', 'to_dt_2'],
                    ['from_period_id_2', 'to_period_id_2'],
                ]),
            ]
        }
    ]

    # Override this method to return a tuple (callable, context) used to filter
    # a list of report service names that are available under a particular
    # report name (e.g., RPT_NAME + ' (By Value)' has rpt_a4_portrait,
    # rpt_a4_landscape, and rpt_a3_landscape). The callable must have the
    # following signature:
    #     lambda service_names, context
    #
    # Later on the callable will be given a list of report service names in
    # service_names and a context that is found in the tuple (callable,
    # context) in context (i.e., the context in the tuple is prepared in this
    # method to provide information needed by the callable).
    #
    # The callable must then return just a single report service name.
    #
    def get_service_name_filter(self, cr, uid, form, context=None):
        def service_name_filter(service_names, context):
            names = filter(lambda nm: nm.find('trial_balance_') == 0,
                           service_names)
            if form.rpt_output != 'pdf':
                return names

            if form.display_large:
                return filter(lambda nm: nm.find('_a3_landscape') != -1, names)
            else:
                return filter(lambda nm: nm.find('_a3_landscape') == -1, names)
        return (service_name_filter, context)

register_report_wizard(RPT_NAME, wizard)
