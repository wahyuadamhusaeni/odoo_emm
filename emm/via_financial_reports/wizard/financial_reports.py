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
    from osv import fields, osv
    from tools.translate import _
    from account_tree import account_tree
    import decimal_precision as dp
    from via_reporting_utility.pgsql import list_to_pgTable
    from via_jasper_report_utils import utility as jasper_report
except ImportError:
    import openerp
    from openerp import release
    from openerp import pooler
    from openerp.osv import fields, osv
    from openerp.tools.translate import _
    from openerp.addons.account_tree import account_tree
    from openerp.addons import decimal_precision as dp
    from openerp.addons.via_reporting_utility.pgsql import list_to_pgTable
    from openerp.addons.via_jasper_report_utils import utility as jasper_report

from datetime import date
import time


def _service_names_filter(service_names, context):
    rpt_output = context.get('via_financial_reports.rpt_output', None)
    if rpt_output is None:
        return service_names

    rpt_landscape = context.get('via_financial_reports.rpt_landscape', False)
    rpt_format = context.get('via_financial_reports.rpt_format', False)
    rpt_drcr = context.get('via_financial_reports.rpt_drcr', False)
    rpt_with_move = context.get('via_financial_reports.rpt_with_move', False)

    if rpt_output in ('xls', 'csv'):
        service_names = filter(lambda sn: '_pageless_' in sn, service_names)
    elif rpt_output == 'pdf':
        service_names = filter(lambda sn: '_pageless_' not in sn,
                               service_names)
        if rpt_landscape:
            service_names = filter(lambda sn: '_landscape_' in sn,
                                   service_names)
        else:
            service_names = filter(lambda sn: '_landscape_' not in sn,
                                   service_names)
        if rpt_format:
            service_names = filter(lambda sn: '_large_' in sn, service_names)
        else:
            service_names = filter(lambda sn: '_small_' in sn, service_names)

    if rpt_drcr:
        service_names = filter(lambda sn: '_nodrcr_' not in sn,
                               service_names)
    else:
        service_names = filter(lambda sn: '_nodrcr_' in sn, service_names)

    if rpt_with_move:
        service_names = filter(lambda sn: '_with_moves_' in sn,
                               service_names)
    else:
        service_names = filter(lambda sn: '_with_moves_' not in sn,
                               service_names)

    return service_names


class via_financial_reports(osv.osv_memory):
    _name = 'via.financial.reports'
    _description = 'VIA Financial Reports'

    def onchange_fiscalyear_id(self, cr, uid, ids, fiscalyear_id=False, filter='filter_no', context=None):
        res = {'value': {}}
        data = self.onchange_filter(cr, uid, ids, filter, fiscalyear_id, context)
        if 'value' in data:
            res['value'].update(data['value'])
        else:
            res['value'].update({'period_from': False,
                                 'period_to': False,
                                 'date_from': False,
                                 'date_to': False})
        return res

    def onchange_cmp1_fiscalyear_id(self, cr, uid, ids, fiscalyear_id=False, filter='filter_no', context=None):
        res = {'value': {}}
        data = self.onchange_cmp1_filter(cr, uid, ids, filter, fiscalyear_id, context)
        if 'value' in data:
            res['value'].update(data['value'])
        else:
            res['value'].update({'cmp1_period_from': False,
                                 'cmp1_period_to': False,
                                 'cmp1_date_from': False,
                                 'cmp1_date_to': False})
        return res

    def onchange_filter(self, cr, uid, ids, filter='filter_no', fiscalyear_id=False, context=None):
        res = {}
        if filter == 'filter_no':
            res['value'] = {'period_from': False, 'period_to': False, 'date_from': False, 'date_to': False}
        if filter == 'filter_date':
            res['value'] = {'period_from': False, 'period_to': False, 'date_from': time.strftime('%Y-01-01'), 'date_to': time.strftime('%Y-%m-%d')}
        if filter == 'filter_period' and fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               ORDER BY p.date_start ASC
                               LIMIT 1) AS period_start
                UNION
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.date_start < NOW()
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''', (fiscalyear_id, fiscalyear_id))
            periods = [i[0] for i in cr.fetchall()]
            if periods:
                if len(periods) > 1:
                    start_period = periods[0]
                    end_period = periods[1]
                elif len(periods) == 1:
                    start_period = periods[0]
                    end_period = periods[0]
            res['value'] = {'period_from': start_period, 'period_to': end_period, 'date_from': False, 'date_to': False}
        return res

    def onchange_cmp1_filter(self, cr, uid, ids, filter='filter_no', fiscalyear_id=False, context=None):
        res = {}
        if filter == 'filter_no':
            res['value'] = {'cmp1_period_from': False, 'cmp1_period_to': False, 'cmp1_date_from': False, 'cmp1_date_to': False}
        if filter == 'filter_date':
            res['value'] = {'cmp1_period_from': False, 'cmp1_period_to': False, 'cmp1_date_from': time.strftime('%Y-01-01'), 'cmp1_date_to': time.strftime('%Y-%m-%d')}
        if filter == 'filter_period' and fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               ORDER BY p.date_start ASC
                               LIMIT 1) AS period_start
                UNION
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.date_start < NOW()
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''', (fiscalyear_id, fiscalyear_id))
            periods = [i[0] for i in cr.fetchall()]
            if periods:
                if len(periods) > 1:
                    start_period = periods[0]
                    end_period = periods[1]
                elif len(periods) == 1:
                    start_period = periods[0]
                    end_period = periods[0]
            res['value'] = {'cmp1_period_from': start_period, 'cmp1_period_to': end_period, 'cmp1_date_from': False, 'cmp1_date_to': False}
        return res

    def onchange_chart_id(self, cr, uid, ids, chart_id, filter='filter_no', cmp1_filter='filter_no', context=None):
        if not chart_id:
            return {}
        account = self.pool.get('account.account').browse(cr, uid, chart_id, context=context)

        now = time.strftime('%Y-%m-%d')
        fy_pool = self.pool.get('account.fiscalyear')
        fiscalyears = fy_pool.search(cr, uid, [('date_start', '<', now),
                                               ('date_stop', '>', now),
                                               ('company_id', '=', account.company_id.id)],
                                     limit=1)
        fiscalyear_id = fiscalyears and fiscalyears[0] or False
        res = {'value': {'leaf_company_chart_account': len(account.company_id.child_ids) == 0,
                         'fiscalyear_id': fiscalyear_id,
                         'cmp1_fiscalyear_id': fiscalyear_id,
                         'company_id': account.company_id.id}}

        data = self.onchange_filter(cr, uid, ids, filter, fiscalyear_id, context)
        if 'value' in data:
            res['value'].update(data['value'])
        else:
            res['value'].update({'period_from': False,
                                 'period_to': False,
                                 'date_from': False,
                                 'date_to': False})
        cmp1_data = self.onchange_cmp1_filter(cr, uid, ids, cmp1_filter, fiscalyear_id, context)
        if 'value' in cmp1_data:
            res['value'].update(cmp1_data['value'])
        else:
            res['value'].update({'cmp1_period_from': False,
                                 'cmp1_period_to': False,
                                 'cmp1_date_from': False,
                                 'cmp1_date_to': False})

        return res

    def onchange_cmp1_enabled(self, cr, uid, ids, context=None):
        return {'value': {'display_move': False}}

    def onchange_company_id(self, cr, uid, ids, company_id, filter='filter_no', cmp1_filter='filter_no', context=None):
        if not company_id:
            return {}

        now = time.strftime('%Y-%m-%d')
        fy_pool = self.pool.get('account.fiscalyear')
        fiscalyears = fy_pool.search(cr, uid, [('date_start', '<', now),
                                               ('date_stop', '>', now),
                                               ('company_id', '=', company_id)],
                                     limit=1)
        fiscalyear_id = fiscalyears and fiscalyears[0] or False

        accounts = self.pool.get('account.account').search(cr, uid,
                                                           [('parent_id', '=', False),
                                                            ('company_id', '=', company_id)],
                                                           limit=1)
        chart_account_id = accounts and accounts[0] or False
        res = {'value': {'fiscalyear_id': fiscalyear_id,
                         'cmp1_fiscalyear_id': fiscalyear_id,
                         'chart_account_id': chart_account_id,
                         'tree_id': False}}

        data = self.onchange_filter(cr, uid, ids, filter, fiscalyear_id, context)
        if 'value' in data:
            res['value'].update(data['value'])
        else:
            res['value'].update({'period_from': False,
                                 'period_to': False,
                                 'date_from': False,
                                 'date_to': False})
        cmp1_data = self.onchange_cmp1_filter(cr, uid, ids, cmp1_filter, fiscalyear_id, context)
        if 'value' in cmp1_data:
            res['value'].update(cmp1_data['value'])
        else:
            res['value'].update({'cmp1_period_from': False,
                                 'cmp1_period_to': False,
                                 'cmp1_date_from': False,
                                 'cmp1_date_to': False})

        return res

    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1)
        return fiscalyears and fiscalyears[0] or False

    def _get_account(self, cr, uid, context=None):
        accounts = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', False)], limit=1)
        return accounts and accounts[0] or False

    _columns = {
        'chart_account_id': fields.many2one('account.account',
                                            'Chart of account',
                                            help='Select Charts of Accounts',
                                            domain=[('parent_id', '=', False)],
                                            required=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal year',
                                         help='Keep empty for all open fiscal year',
                                         required=True),
        'filter': fields.selection([('filter_no', 'No Filters'),
                                    ('filter_date', 'Date'),
                                    ('filter_period', 'Periods')], 'Filter by',
                                   required=True),
        'period_from': fields.many2one('account.period', 'Start period'),
        'period_to': fields.many2one('account.period', 'End period'),
        'journal_ids': fields.many2many('account.journal',
                                        'account_common_journal_rel',
                                        'account_id', 'journal_id', 'Journals'),
        'date_from': fields.date('Start Date'),
        'date_to': fields.date('End Date'),
        'target_move': fields.selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                        ], 'Target Moves', required=True),
        'name': fields.char('Report name', readonly=True, required=True, size=256),
        'account_ids': fields.many2many('account.account',
                                        'account_common_account_rel',
                                        'report_id', 'account_id', 'Accounts'),
        'rpt_output': fields.selection(jasper_report.get_outputs_selection,
                                       'Output Format', required=True),
        # Checksum makes sense on a leaf company but not on a consolidation
        # company in a multi-currency setting because of the following:
        # 1. When an account is not included in the CoA, what currency conversion
        #    shall be applied to its move lines?
        # 2. When the above problem is solved by keeping checksum specific to
        #    each company (no conversion happens), the checksum will never be
        #    valid when used in a parent company as illustrated below:
        #    Com C
        #    +- Com D
        #       +- Com E
        #    The original amount at Com D is the sum of Com D move lines and
        #    Com E move lines that have been converted to Com D currency. But,
        #    the checksum of Com D only considers Com D move lines. Thus,
        #    discrepancy will always exist.
        'display_checksum': fields.boolean('Show checksum', help="Can only be used on leaf company"),
        'display_drcr': fields.boolean('Show debit & credit'),
        'display_move': fields.boolean('Show move'),
        'display_type': fields.boolean('Landscape Mode'),
        'display_format': fields.boolean('Large format'),
        'use_indentation': fields.boolean('Indent account name based on depth'),
        'no_wrap': fields.boolean('No wrap'),
        'arg': fields.text('Free Argument'),
        'account_tree': fields.text('Account Tree'),
        'report_parameters_left': fields.text('Report Parameters Right'),
        'report_parameters_right': fields.text('Report Parameters Left'),
        'separator_nr': fields.integer('Separator Number'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'leaf_company_chart_account': fields.boolean('Leaf Company Owned CoA', readonly=True),
        'decimal_precision': fields.integer('Decimal Precision', required=True,
                                            readonly=True),
        'oerp_user': fields.many2one('res.users', 'Printed by', required=True,
                                     readonly=True),
        'display_account': fields.selection([('bal_all', 'All'),
                                             ('bal_movement', 'With movements'),
                                             ('bal_solde', 'With balance is not equal to 0'),
                                             ],'Display accounts',
                                            required=True),
        'tree_type_name': fields.char('Name', size=128, select=True),
        'tree_id': fields.many2one('via.reporting.tree', 'Reporting Tree',
                                   domain=("[('company_id','=',company_id),"
                                           "('tree_type_id.name','=',tree_type_name)]")),
        'cmp1_enabled': fields.boolean('Enable Comparison'),
        'label': fields.char('Reference Label', size=128),
        'cmp1_label': fields.char('Comparison Label', size=128),
        'cmp1_fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal year',
                                              help='Keep empty for all open fiscal year',
                                              required=True),
        'cmp1_filter': fields.selection([('filter_no', 'No Filters'),
                                         ('filter_date', 'Date'),
                                         ('filter_period', 'Periods')], 'Filter by',
                                        required=True),
        'cmp1_period_from': fields.many2one('account.period', 'Start period'),
        'cmp1_period_to': fields.many2one('account.period', 'End period'),
        'cmp1_date_from': fields.date('Start Date'),
        'cmp1_date_to': fields.date('End Date'),
        'bs_as_of': fields.date('B/S As-Of'),
    }

    _defaults = {
        'rpt_output': 'xls',
        'display_drcr': False,
        'display_move': lambda self, cr, uid, ctx: ctx.get('via_jasper_report_utils.rpt_name', False) in ('General Ledger', 'General Ledger/Trial Balance'),
        #'display_checksum': lambda self, cr, uid, ctx: ctx.get('via_jasper_report_utils.rpt_name', False) not in ('Balance Sheet', 'Profit/Loss'),
        'display_checksum': False,  # Disabled to ease the development of multi-currency (issue #2055)
        'use_indentation': lambda self, cr, uid, ctx: ctx.get('via_jasper_report_utils.rpt_name', False) not in ('General Ledger', 'General Ledger/Trial Balance'),
        'decimal_precision': lambda self, cr, uid, ctx: dp.get_precision('Account')(cr)[1],
        'name': lambda self, cr, uid, ctx: ctx.get('via_jasper_report_utils.rpt_name', False),
        'display_type': False,
        'display_format': False,
        'no_wrap': lambda self, cr, uid, ctx: ctx.get('via_jasper_report_utils.rpt_name', False) in ('General Ledger', 'General Ledger/Trial Balance'),
        'oerp_user': lambda self, cr, uid, ctx: uid,
        'display_account': 'bal_all',
        'fiscalyear_id': _get_fiscalyear,
        'filter': 'filter_no',
        'cmp1_fiscalyear_id': _get_fiscalyear,
        'cmp1_filter': 'filter_no',
        'chart_account_id': _get_account,
        'target_move': 'posted',
        'company_id': lambda self, cr, uid, ctx: ctx.get('via_jasper_report_utils.rpt_name', False) not in ('Balance Sheet', 'Profit/Loss', 'General Ledger/Trial Balance') and self.pool.get('res.users').browse(cr, uid, uid, context=ctx).company_id.id,
        'leaf_company_chart_account': lambda self, cr, uid, ctx: (self._get_account(cr, uid, context=ctx)
                                                                  and self.pool.get('account.account').browse(cr,
                                                                                                              uid,
                                                                                                              self._get_account(cr,
                                                                                                                                uid,
                                                                                                                                context=ctx),
                                                                                                              context=ctx).company_id.child_ids == []),
        'tree_type_name': lambda self, cr, uid, ctx: ctx.get('via_reporting_tree.tree_type_name', False),
        'bs_as_of': fields.date.context_today,
    }

    def write(self, cr, uid, ids, vals, context=None):
        if 'date_to' not in vals:
            vals['date_to'] = False
        if 'date_from' not in vals:
            vals['date_from'] = False
        if 'period_to' not in vals:
            vals['period_to'] = False
        if 'period_from' not in vals:
            vals['period_from'] = False
        return super(via_financial_reports, self).write(cr, uid, ids,
                                                        vals, context=None)

    def _assert_within_fiscalyear(self, cr, uid, date_from, date_to,
                                  fiscalyear_id, context):
        if not date_from or not date_to:
            return
        fy_pool = self.pool.get('account.fiscalyear')
        fy = fy_pool.browse(cr, uid, fiscalyear_id, context=context)
        if not (fy.date_start <= date_from <= date_to <= fy.date_stop):
            raise osv.except_osv(_('Error !'),
                                 _("Start date and end date of date filter must"
                                   " be within those of the fiscal year and"
                                   " start date cannot be later than end date"))

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        form = self.browse(cr, uid, ids[0], context=context)
        self._assert_within_fiscalyear(cr, uid, form.date_from,
                                       form.date_to, form.fiscalyear_id.id,
                                       context)
        context['via_financial_reports.form'] = form
        context['via_financial_reports.form.bs_as_of'] = form.bs_as_of
        root_account_id = form.chart_account_id and form.chart_account_id.id or 0
        rpt_name = context['via_jasper_report_utils.rpt_name']
        arg = None
        display_account = form.display_account
        if display_account == 'bal_all':
            display_checksum = form.display_checksum
        else:
            display_checksum = False

        # The use of the following filters destroy tree structure
        journal_ids = form.journal_ids
        account_ids = form.account_ids
        if display_account != 'bal_all' or journal_ids or account_ids:
            form.write({'use_indentation': False}, context=context)

        (arg,
         tree,
         separator_nr) = self._get_data(cr, uid, root_account_id,
                                        rpt_name, display_checksum,
                                        form.display_move,
                                        form.cmp1_enabled,
                                        context)
        del context['via_financial_reports.form']

        report_parameters_left = list_to_pgTable(context.get('via_financial_reports.report_parameters_left', ''),
                                                 't',
                                                 [('ord', 'INTEGER'),
                                                  ('key', 'TEXT'),
                                                  ('value', 'TEXT')])
        report_parameters_right = list_to_pgTable(context.get('via_financial_reports.report_parameters_right', ''),
                                                  't',
                                                  [('ord', 'INTEGER'),
                                                   ('key', 'TEXT'),
                                                   ('value', 'TEXT')])
        form.write({'arg': arg,
                    'account_tree': tree,
                    'separator_nr': separator_nr,
                    'report_parameters_left': report_parameters_left,
                    'report_parameters_right': report_parameters_right, },
                   context=context)

        rpt_landscape = form.display_type
        rpt_format = form.display_format
        rpt_drcr = form.display_drcr
        if rpt_name in ('Trial Balance', 'General Ledger'):
            rpt_drcr = True
        if rpt_name in ('General Ledger', 'General Ledger/Trial Balance'):
            rpt_with_move = True
        else:
            rpt_with_move = form.display_move
        rpt_output = form.rpt_output

        service_names_filter_ctx = {
            'via_financial_reports.rpt_output': rpt_output,
            'via_financial_reports.rpt_landscape': rpt_landscape,
            'via_financial_reports.rpt_drcr': rpt_drcr,
            'via_financial_reports.rpt_with_move': rpt_with_move,
            'via_financial_reports.rpt_format': rpt_format,
        }
        service_name = jasper_report.get_service_name(cr, uid, rpt_name,
                                                      rpt_output,
                                                      _service_names_filter,
                                                      service_names_filter_ctx)

        data = {
            'form': {
                'id': form.id
            },
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': service_name,
            'datas': data,
        }

    def _get_data(self, cr, uid, root_account_id, rpt_name, display_checksum,
                  display_move, cmp1_enabled, context):
        at = account_tree(display_checksum)
        if rpt_name in ('VIA Combined Balance Sheet', 'Balance Sheet'):
            ((pl_type, pl_account_id, shorter, shorter_end),
             tree,
             separator_nr) = at.report_balance_sheet(self.pool, cr, uid,
                                                     root_account_id, context)
            if pl_type is None:
                if pl_account_id == 1:
                    com_pool = self.pool.get('res.company')
                    com_names = [x[1]
                                 for x in com_pool.name_get(cr, uid, tree,
                                                            context=context)]
                    raise osv.except_osv(_('Error !'),
                                         _("Companies '%s' do not have reserve account"
                                           % "', '".join(com_names)))
                elif pl_account_id == 2:
                    acc_pool = self.pool.get('account.account')
                    reserve_acc_names = [x[1]
                                         for x in acc_pool.name_get(cr, uid, tree,
                                                                    context=context)]
                    raise osv.except_osv(_('Error !'),
                                         _("Reserve account(s) '%s' cannot be"
                                           " found in asset or liability branch."
                                           " The reserve account(s) may have not"
                                           " been mapped to the consolidating"
                                           " company or may have the wrong"
                                           " parent account(s)")
                                         % "', '".join(reserve_acc_names))
                elif pl_account_id == 3:
                    com_pool = self.pool.get('res.company')
                    msgs = []
                    for (cid, missing_head_accs) in tree.iteritems():
                        com_name = com_pool.name_get(cr, uid, [cid],
                                                     context=context)[0][1]
                        msgs.append(_("company '%s' has not set its '%s' head"
                                      " account(s)") % (com_name,
                                                        "', '".join(missing_head_accs)))
                    raise osv.except_osv(_('Error !'), ", ".join(msgs))
                elif pl_account_id == 4:
                    acc_pool = self.pool.get('account.account')
                    acc = acc_pool.browse(cr, uid, root_account_id,
                                          context=context)
                    raise osv.except_osv(_('Error !'),
                                         ("Account '%s %s' is a descendant of root account '%s %s',"
                                          " but company '%s' is not a descendant of root company '%s'"
                                          % (tree.code, tree.name,
                                             acc.code, acc.name,
                                             tree.company_id.name,
                                             acc.company_id.name)))
                elif pl_account_id == 5:
                    com_pool = self.pool.get('res.company')
                    com_names = [x[1]
                                 for x in com_pool.name_get(cr, uid, tree,
                                                            context=context)]
                    raise osv.except_osv(_('Error !'),
                                         _("Companies '%s' do not have currency gain/loss account"
                                           % "', '".join(com_names)))
                elif pl_account_id == 6:
                    acc_pool = self.pool.get('account.account')
                    xgl_acc_names = [x[1]
                                     for x in acc_pool.name_get(cr, uid, tree,
                                                                context=context)]
                    raise osv.except_osv(_('Error !'),
                                         _("Currency gain/loss account(s) '%s' cannot be"
                                           " found in asset or liability branch."
                                           " The currency gain/loss account(s) may have not"
                                           " been mapped to the consolidating"
                                           " company or may have the wrong"
                                           " parent account(s)")
                                         % "', '".join(xgl_acc_names))
            arg = ','.join([pl_type, str(pl_account_id), shorter, str(shorter_end)])
            if rpt_name == 'Balance Sheet':
                type_cast = tree[0]
                linearized_tree = tree[1]
                prms_left = context['via_financial_reports.report_parameters_left']
                prms_right = context['via_financial_reports.report_parameters_right']
                if cmp1_enabled:
                    context['via_financial_reports.cmp1_phase'] = True
                    (unused,
                     cmp1_tree,
                     unused) = at.report_balance_sheet(self.pool, cr, uid,
                                                       root_account_id, context)
                    del context['via_financial_reports.cmp1_phase']
                    linearized_tree.extend(cmp1_tree[1])
                    prms_left.extend(context['via_financial_reports.report_parameters_left'])
                    prms_right.extend(context['via_financial_reports.report_parameters_right'])
                tree = list_to_pgTable(linearized_tree, 't', type_cast)
                context['via_financial_reports.report_parameters_left'] = prms_left
                context['via_financial_reports.report_parameters_right'] = prms_right
        elif rpt_name in ('VIA Combined Profit/Loss', 'Profit/Loss'):
            (profit_loss_line,
             tree,
             separator_nr) = at.report_profit_loss(self.pool, cr, uid,
                                                   root_account_id, context)
            if profit_loss_line is None:
                com_pool = self.pool.get('res.company')
                msgs = []
                for (cid, missing_head_accs) in tree.iteritems():
                    com_name = com_pool.name_get(cr, uid, [cid],
                                                 context=context)[0][1]
                    msgs.append(_("company '%s' has not set its '%s' head"
                                  " account(s)") % (com_name,
                                                    "', '".join(missing_head_accs)))
                raise osv.except_osv(_('Error !'), ", ".join(msgs))
            if tree is None:
                acc_pool = self.pool.get('account.account')
                acc = acc_pool.browse(cr, uid, root_account_id,
                                      context=context)
                raise osv.except_osv(_('Error !'),
                                     ("Account '%s %s' is a descendant of root account '%s %s',"
                                      " but company '%s' is not a descendant of root company '%s'"
                                      % (separator_nr.code, separator_nr.name,
                                         acc.code, acc.name,
                                         separator_nr.company_id.name,
                                         acc.company_id.name)))
            arg = profit_loss_line
            if rpt_name == 'Profit/Loss':
                type_cast = tree[0]
                linearized_tree = tree[1]
                prms_left = context['via_financial_reports.report_parameters_left']
                prms_right = context['via_financial_reports.report_parameters_right']
                if cmp1_enabled:
                    context['via_financial_reports.cmp1_phase'] = True
                    (unused,
                     cmp1_tree,
                     unused) = at.report_profit_loss(self.pool, cr, uid,
                                                     root_account_id, context)
                    del context['via_financial_reports.cmp1_phase']
                    linearized_tree.extend(cmp1_tree[1])
                    prms_left.extend(context['via_financial_reports.report_parameters_left'])
                    prms_right.extend(context['via_financial_reports.report_parameters_right'])
                tree = list_to_pgTable(linearized_tree, 't', type_cast)
                context['via_financial_reports.report_parameters_left'] = prms_left
                context['via_financial_reports.report_parameters_right'] = prms_right
        elif (rpt_name in ('Trial Balance', 'General Ledger', 'General Ledger/Trial Balance')):
            context['via_financial_reports.gl_new'] = (rpt_name in ('General Ledger', 'General Ledger/Trial Balance'))
            if context['via_financial_reports.gl_new']:
                context['via_financial_reports.gl_new_move_lines'] = {}
            if display_move or context['via_financial_reports.gl_new']:
                (move_lines,
                 tree,
                 separator_nr) = at.report_general_ledger_with_move(self.pool,
                                                                    cr, uid,
                                                                    root_account_id,
                                                                    context)
                arg = move_lines
                if rpt_name == 'General Ledger/Trial Balance':
                    type_cast = tree[0]
                    linearized_tree = tree[1]
                    prms_left = context['via_financial_reports.report_parameters_left']
                    prms_right = context['via_financial_reports.report_parameters_right']
                    if cmp1_enabled:
                        context['via_financial_reports.gl_new_move_lines'] = {}
                        context['via_financial_reports.cmp1_phase'] = True
                        (unused,
                         cmp1_tree,
                         unused) = at.report_general_ledger_with_move(self.pool,
                                                                      cr, uid,
                                                                      root_account_id,
                                                                      context)
                        del context['via_financial_reports.cmp1_phase']
                        linearized_tree.extend(cmp1_tree[1])
                        prms_left.extend(context['via_financial_reports.report_parameters_left'])
                        prms_right.extend(context['via_financial_reports.report_parameters_right'])
                    tree = list_to_pgTable(linearized_tree, 't', type_cast)
                    context['via_financial_reports.report_parameters_left'] = prms_left
                    context['via_financial_reports.report_parameters_right'] = prms_right
            else:
                (unused,
                 tree,
                 separator_nr) = at.report_general_ledger(self.pool, cr,
                                                          uid,
                                                          root_account_id,
                                                          context)
                arg = None
            if tree is None:
                acc_pool = self.pool.get('account.account')
                acc = acc_pool.browse(cr, uid, root_account_id,
                                      context=context)
                raise osv.except_osv(_('Error !'),
                                     ("Account '%s %s' is a descendant of root account '%s %s',"
                                      " but company '%s' is not a descendant of root company '%s'"
                                      % (separator_nr.code, separator_nr.name,
                                         acc.code, acc.name,
                                         separator_nr.company_id.name,
                                         acc.company_id.name)))
        else:
            raise osv.except_osv(_('Error !'),
                                 _('Unrecognized report name: %s' % rpt_name))
        return (arg, tree, separator_nr)

via_financial_reports()


# The following is to pass the account tree data to the jasper reports
class ir_actions_report_xml(osv.osv):
    _inherit = 'ir.actions.report.xml'

    def register_all(self, cr):
        res = super(ir_actions_report_xml, self).register_all(cr)

        cr.execute("SELECT *"
                   " FROM ir_act_report_xml r"
                   "  INNER JOIN ir_model_data d"
                   "   ON r.id = d.res_id"
                   " WHERE d.module = 'via_financial_reports'"
                   "  AND d.model = 'ir.actions.report.xml'"
                   "  AND POSITION('via_financial_reports/report/trial_balance/' IN report_file) != 1"
                   "  AND POSITION('via_financial_reports/report/general_ledger/' IN report_file) != 1"
                   "  AND POSITION('via_financial_reports/report/cash_flow/' IN report_file) != 1"
                   " ORDER BY r.id")
        records = cr.dictfetchall()

        class account_tree_parser(object):
            def __init__(self, cr, uid, ids, data, context):
                id_ = data['form']['id']
                pool = pooler.get_pool(cr.dbname).get('via.financial.reports')
                o = pool.browse(cr, uid, id_, context)

                self.parameters = {}
                if o.arg is None:
                    self.parameters['ARG'] = ''
                else:
                    self.parameters['ARG'] = o.arg
                self.parameters['ACCOUNT_TREE'] = o.account_tree
                self.parameters['REPORT_PARAMETERS_LEFT'] = o.report_parameters_left
                self.parameters['REPORT_PARAMETERS_RIGHT'] = o.report_parameters_right
                self.parameters['REPORT_PARAMETERS'] = (o.report_parameters_left
                                                        + "," + o.report_parameters_right)
                if o.separator_nr is None:
                    self.parameters['SEPARATOR_NR'] = -1
                else:
                    self.parameters['SEPARATOR_NR'] = o.separator_nr
                self.parameters['USE_INDENTATION'] = o.use_indentation
                self.parameters['OERP_USER'] = o.oerp_user.name
                self.parameters['NO_WRAP'] = o.no_wrap
                self.parameters['DISPLAY_MOVE'] = int(o.display_move)
                if o.rpt_output == 'pdf' or o.name in ('General Ledger', 'General Ledger/Trial Balance'):
                    decimal_place = 0
                else:
                    decimal_place = o.decimal_precision
                if decimal_place > 0:
                    decimal_str = '.' + '0' * decimal_place
                else:
                    decimal_str = ''
                self.parameters['DECIMAL_PRECISION'] = (0 if o.rpt_output == 'pdf'
                                                        else o.decimal_precision)
                self.parameters['DECIMAL_FORMAT_STRING'] = ',##0' + decimal_str
                self.parameters['DECIMAL_ROUNDING_MODE'] = 'HALF_UP'

            def get(self, key, default):
                if key == 'parameters':
                    return self.parameters
                else:
                    return default

        from jasper_reports.jasper_report import report_jasper

        for record in records:
            name = 'report.%s' % record['report_name']
            report_jasper(name, record['model'], account_tree_parser)

        return res

ir_actions_report_xml()
