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
    import pooler
    from osv import osv, fields, orm
    if release.major_version == '6.1':
        import openerp.modules as addons
    else:
        import addons
    from via_jasper_report_utils import utility
    from tools.translate import _
    from tools import DEFAULT_SERVER_DATE_FORMAT
except ImportError:
    import openerp
    from openerp import release
    from openerp import pooler
    from openerp.osv import osv, fields, orm
    import openerp.modules as addons
    from openerp.addons.via_jasper_report_utils import utility
    from openerp.tools.translate import _
    from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

import calendar
from lxml import etree
import re
import os
import glob
from datetime import date
from datetime import datetime
from copy import deepcopy
from via_reporting_utility.pgsql import list_to_pgTable
from via_jasper_report_utils import framework
from via_jasper_report_utils.framework import register_report_wizard, normalize_rpt_name  # wizard

_report_wizard_registry = framework._report_wizard_registry


class wizard(framework.wizard):
    _onchange = {}
    _visibility = []
    _required = []
    _readonly = []
    _attrs = {}
    _domain = {
        'fiscalyear_id': "[('company_id','=',company_id)]",
        'from_period_id': "[('fiscalyear_id','=',fiscalyear_id)]",
        'to_period_id': "[('fiscalyear_id','=',fiscalyear_id)]",
        'reporting_tree_id': "[('company_id','=',False)]",
        'reporting_tree_node_ids': "[('tree_id','=',reporting_tree_id),('children','=',False)]",
        'analytic_acc_ids': "[('company_id','=',False)]",
        'acc_ids': "[('company_id','=',False)]",
        'journal_ids': "[('company_id','=',False)]",
        'fiscalyear_id_2': "[('company_id','=',company_id)]",
        'from_period_id_2': "[('fiscalyear_id','=',fiscalyear_id_2)]",
        'to_period_id_2': "[('fiscalyear_id','=',fiscalyear_id_2)]",
    }
    _current_domain = {}

    _label = {}

    _defaults = {}

    _selections = {}

    _tree_columns = {
        'reporting_tree_node_ids': ['name'],
    }


def dt(date_string):
    return datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()


class via_jasper_report(osv.osv_memory):
    _inherit = "via.jasper.report"
    _description = 'Standard VIA wizard for generating Jasper Reports Account'

    _columns = {
        'reporting_tree_id': fields.many2one('via.reporting.tree', 'Reporting Tree'),
        'reporting_tree_node_ids': fields.many2many('via.reporting.tree.node',
                                                    'via_report_reporting_tree_node_rel',
                                                    'via_report_id',
                                                    'tree_node_id',
                                                    string='Reporting Tree Node'),
        'analytic_acc_ids': fields.many2many('account.analytic.account',
                                             'via_report_analytic_acc_rel',
                                             'via_report_id',
                                             'analytic_acc_id',
                                             string='Analytic Accounts'),
        'acc_ids': fields.many2many('account.account',
                                    'via_report_acc_rel',
                                    'via_report_id',
                                    'acc_id',
                                    string='Accounts'),
        'acc_ids_empty_is_all': fields.boolean('Accounts When Empty Means All'),
        'journal_ids': fields.many2many('account.journal',
                                        'via_report_journal_rel',
                                        'via_report_id',
                                        'journal_id',
                                        string='Journals'),
        'journal_ids_empty_is_all': fields.boolean('Journals When Empty Means All'),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year'),
        'fiscalyear_id_2': fields.many2one('account.fiscalyear', 'Fiscal Year'),
        'target_move': fields.selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                         ], 'Target Moves'),
        'display_move': fields.boolean('Show Move'),
        'display_drcr': fields.boolean('Show Debit & Credit'),
        'from_period_id': fields.many2one('account.period', 'Start Period'),
        'from_period_id_2': fields.many2one('account.period', 'Start Period'),
        'to_period_id': fields.many2one('account.period', 'End Period'),
        'to_period_id_2': fields.many2one('account.period', 'End Period'),
    }

    def default_fiscalyear_id(self, cr, uid, context=None, company_id=None):
        if company_id:
            com_id = company_id
        else:
            com_id = self.pool.get('res.users').browse(cr, uid, uid,
                                                       context=context).company_id.id
        now = str(date.today())
        crit = [('company_id', '=', com_id), ('date_start', '<', now), ('date_stop', '>', now)]
        fiscalyear_pool = self.pool.get('account.fiscalyear')
        fiscalyears = fiscalyear_pool.search(cr, uid, crit, limit=1)
        return fiscalyears and fiscalyears[0] or False

    _defaults = {
        'fiscalyear_id': default_fiscalyear_id,
        'target_move': 'posted',
    }

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(via_jasper_report, self).default_get(cr, uid, fields_list, context=context)

        rpt_name = context.get('via_jasper_report_utils_account.rpt_name', False)
        if rpt_name:
            rpt_defaults = getattr(_report_wizard_registry[normalize_rpt_name(rpt_name)], '_defaults', {})
            for field_name, field_default in rpt_defaults.iteritems():
                res[field_name] = field_default(self, cr, uid, context)

        return res

    # Related to analytic_acc_ids
    def get_analytic_acc_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.analytic_acc_ids) == 0:
            _default_domain = form.get_current_domain('analytic_acc_ids')
            crit = _default_domain or [('company_id', 'in', [com_id.id for com_id in form.company_ids])]
            return self.pool.get('account.analytic.account').search(cr, uid,
                                                                    crit,
                                                                    context=context)
        else:
            return [analytic_acc_id.id for analytic_acc_id in form.analytic_acc_ids]

    def get_analytic_acc_names(self, cr, uid, ids, when_empty='All',
                               context=None):
        form = self.get_form(cr, uid, ids, context=context)

        return ([analytic_acc_id.name for analytic_acc_id in form.analytic_acc_ids]
                or [when_empty])
    # Related to analytic_acc_ids [END]

    # Related to reporting_tree_id and reporting_tree_node_ids
    def get_reporting_tree_node_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.reporting_tree_node_ids) == 0:
            _default_domain = form.get_current_domain('journal_ids')
            crit = _default_domain or [('tree_id', '=', form.reporting_tree_id.id)]
            return self.pool.get('via.reporting.tree.node').search(cr, uid,
                                                                   crit,
                                                                   context=context)
        else:
            return [node_id.id for node_id in form.reporting_tree_node_ids]

    def get_reporting_tree_node_names(self, cr, uid, ids, when_empty='All',
                                      context=None):
        form = self.get_form(cr, uid, ids, context=context)

        return ([node_id.name for node_id in form.reporting_tree_node_ids]
                or [when_empty])
    # Related to reporting_tree_id and reporting_tree_node_ids [END]

    # Related to journal_ids
    def get_journal_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.journal_ids) == 0:
            _default_domain = form.get_current_domain('journal_ids')
            crit = _default_domain or [('company_id', 'in', [com_id.id for com_id in form.company_ids])]
            return self.pool.get('account.journal').search(cr, uid,
                                                           crit,
                                                           context=context)
        else:
            return [journal_id.id for journal_id in form.journal_ids]

    def get_journal_names(self, cr, uid, ids, when_empty='All', context=None):
        form = self.get_form(cr, uid, ids, context=context)

        return ([journal_id.name for journal_id in form.journal_ids]
                or [when_empty])
    # Related to journal_ids [END]

    # Related to acc_ids
    def get_acc_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.acc_ids) == 0:
            _default_domain = form.get_current_domain('acc_ids')
            crit = _default_domain or [('company_id', 'in', [com_id.id for com_id in form.company_ids])]
            return self.pool.get('account.account').search(cr, uid,
                                                           crit,
                                                           context=context)
        else:
            return [acc_id.id for acc_id in form.acc_ids]

    def get_acc_names(self, cr, uid, ids, when_empty='All', context=None):
        form = self.get_form(cr, uid, ids, context=context)

        return (['%s %s' % (acc_id.code, acc_id.name) for acc_id in form.acc_ids]
                or [when_empty])
    # Related to acc_ids [END]

    def print_report(self, cr, uid, ids, context=None, data=None):
        o = self.browse(cr, uid, ids[0], context=context)
        default_date = date.today()

        # Related to reporting_tree_id and reporting_tree_node_ids
        o.add_marshalled_data('REPORTING_TREE_ID', o.reporting_tree_id.id)
        o.add_marshalled_data('REPORTING_TREE_NAME', o.reporting_tree_id.name or '')
        o.add_marshalled_data('REPORTING_TREE_NODE_IDS', ','.join('%d' % node_id
                                                    for node_id in o.get_reporting_tree_node_ids(context=context)))
        o.add_marshalled_data('REPORTING_TREE_NODE_NAMES', ', '.join(o.get_reporting_tree_node_names(context=context)))

        # Related to analytic_acc_ids
        o.add_marshalled_data('ANALYTIC_ACC_IDS', ','.join('%d' % analytic_acc_id
                                         for analytic_acc_id in o.get_analytic_acc_ids(context=context)))
        o.add_marshalled_data('ANALYTIC_ACC_NAMES', ', '.join(o.get_analytic_acc_names(context=context)))
        # Related to acc_ids
        if o.acc_ids_empty_is_all and len(o.acc_ids) == 0:
            param_acc_ids = 'NULL'
        else:
            param_acc_ids = ','.join('%d' % acc_id
                                     for acc_id in o.get_acc_ids(context=context))
        o.add_marshalled_data('ACC_IDS', param_acc_ids)
        o.add_marshalled_data('ACC_NAMES', ', '.join(o.get_acc_names(context=context)))
        # Related to journal_ids
        if o.journal_ids_empty_is_all and len(o.journal_ids) == 0:
            param_journal_ids = 'NULL'
        else:
            param_journal_ids = ','.join('%d' % journal_id
                                         for journal_id in o.get_journal_ids(context=context))
        o.add_marshalled_data('JOURNAL_IDS', param_journal_ids)
        o.add_marshalled_data('JOURNAL_NAMES', ', '.join(o.get_journal_names(context=context)))
        # Related fiscalyear
        fiscalyear_start_dt = (o.fiscalyear_id.period_ids
                               and dt(o.fiscalyear_id.period_ids[0].date_start)
                               or default_date)
        fiscalyear_stop_dt = (o.fiscalyear_id.period_ids
                              and dt(o.fiscalyear_id.period_ids[-1].date_stop)
                              or default_date)
        fiscalyear_start_dt_2 = (o.fiscalyear_id_2.period_ids
                                 and dt(o.fiscalyear_id_2.period_ids[0].date_start)
                                 or default_date)
        fiscalyear_stop_dt_2 = (o.fiscalyear_id_2.period_ids
                                and dt(o.fiscalyear_id_2.period_ids[-1].date_stop)
                                or default_date)
        o.add_marshalled_data('FISCALYEAR_ID', o.fiscalyear_id.id)
        o.add_marshalled_data('FISCALYEAR_NAME', o.fiscalyear_id.name or '')
        o.add_marshalled_data('FISCALYEAR_START_YR', fiscalyear_start_dt.year)
        o.add_marshalled_data('FISCALYEAR_START_MO', fiscalyear_start_dt.month)
        o.add_marshalled_data('FISCALYEAR_START_DY', fiscalyear_start_dt.day)
        o.add_marshalled_data('FISCALYEAR_STOP_YR', fiscalyear_stop_dt.year)
        o.add_marshalled_data('FISCALYEAR_STOP_MO', fiscalyear_stop_dt.month)
        o.add_marshalled_data('FISCALYEAR_STOP_DY', fiscalyear_stop_dt.day)
        o.add_marshalled_data('FISCALYEAR_ID_2', o.fiscalyear_id_2.id)
        o.add_marshalled_data('FISCALYEAR_NAME_2', o.fiscalyear_id_2.name or '')
        o.add_marshalled_data('FISCALYEAR_START_YR_2', fiscalyear_start_dt_2.year)
        o.add_marshalled_data('FISCALYEAR_START_MO_2', fiscalyear_start_dt_2.month)
        o.add_marshalled_data('FISCALYEAR_START_DY_2', fiscalyear_start_dt_2.day)
        o.add_marshalled_data('FISCALYEAR_STOP_YR_2', fiscalyear_stop_dt_2.year)
        o.add_marshalled_data('FISCALYEAR_STOP_MO_2', fiscalyear_stop_dt_2.month)
        o.add_marshalled_data('FISCALYEAR_STOP_DY_2', fiscalyear_stop_dt_2.day)
        o.add_marshalled_data('TARGET_MOVE', o.target_move or '')
        o.add_marshalled_data('TARGET_MOVE_NAME', (o.target_move or '').capitalize())
        o.add_marshalled_data('DISPLAY_MOVE', o.display_move)
        o.add_marshalled_data('DISPLAY_DRCR', o.display_drcr)

        return super(via_jasper_report, self).print_report(cr, uid, ids, context=context, data=data)

via_jasper_report()
