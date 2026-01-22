# -*- encoding: utf-8 -*-
###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2011 - 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

try:
    import release
    from osv import fields, osv
    from tools.translate import _
    from via_reporting_utility.currency import get_currency_toolkit
    from via_reporting_utility.currency import chained_currency_converter
    from via_reporting_utility.pgsql import list_to_pgTable
    from via_reporting_utility.company import get_company_ids
    from via_reporting_utility.nested_dict import NestedDictCat, NestedDict
    from via_reporting_tree.specialization_link_account import AccountTreeNodeValue
    import pooler
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import fields, osv
    from openerp.tools.translate import _
    from openerp.addons.via_reporting_utility.currency import get_currency_toolkit
    from openerp.addons.via_reporting_utility.currency import chained_currency_converter
    from openerp.addons.via_reporting_utility.pgsql import list_to_pgTable
    from openerp.addons.via_reporting_utility.company import get_company_ids
    from openerp.addons.via_reporting_utility.nested_dict import NestedDictCat, NestedDict
    from openerp.addons.via_reporting_tree.specialization_link_account import AccountTreeNodeValue
    from openerp import pooler

from time import strftime, strptime
from datetime import date

# General ledger is the source data to produce Profit & Loss and Balance Sheet
# financial reports. Therefore, the amount to be included in the retained
# earnings account in the Balance Sheet report should be taken by summing all
# accounts in the general ledger paying attention to the account report type,
# whether the account type is income or expense, instead of paying attention to
# the tree structure of the Profit & Loss accounts.


class CompanyHierarchyError(Exception):
    def __init__(self, account):
        self.account = account

    def __str__(self):
        return repr(self.account)


class account_tree:
    def __init__(self, display_checksum):
        self.display_checksum = display_checksum

    # Data carried by a tree node
    IDX_ACCOUNT = 0
    IDX_CHILDREN = 1
    IDX_LEVEL = 2
    IDX_DEBIT = 3
    IDX_CREDIT = 4
    IDX_CURRENCY = 5
    IDX_TOTAL_TEXT = 6
    IDX_COMPANY = 7
    IDX_TYPE = 8
    IDX_TOTAL = 9
    IDX_DONT_CALCULATE = 10
    IDX_FORCE_MULTICOMPANY = 11
    IDX_MOVE_COUNT = 12
    IDX_REPORT_TYPE = 13
    IDX_BB_DEBIT = 14
    IDX_BB_CREDIT = 15
    IDX_CONSOL_CHILDREN = 16

    # Data carried by a company total dictionary entry
    IDX_TOTAL_DEBIT = 0
    IDX_TOTAL_CREDIT = 1
    IDX_TOTAL_MOVEMENT = 2
    IDX_TOTAL_BEGINNING_BALANCE_DEBIT = 3
    IDX_TOTAL_BEGINNING_BALANCE_CREDIT = 4
    IDX_TOTAL_BEGINNING_BALANCE = 5
    IDX_TOTAL_ENDING_BALANCE = 6
    IDX_TOTAL_LINEARIZE_ME = 7

    # Account internal types
    VIEW_ACC = 'view'
    CONS_ACC = 'consolidation'

    # Account report types
    ASSET_ACC = 'asset'
    LIABILITY_ACC = 'liability'
    INCOME_ACC = 'income'
    EXPENSE_ACC = 'expense'

    # Report parameter key, value, and order
    PRM_POS_LEFT = 0
    PRM_POS_RIGHT = 1
    PRM_VAL_ALL = 'All'

    PRM_KEY_REPORT_NAME = 'Report Name'
    PRM_ORD_REPORT_NAME = 2
    PRM_POS_REPORT_NAME = PRM_POS_LEFT
    PRM_KEY_COMPANY_NAME = 'Company Name'
    PRM_ORD_COMPANY_NAME = 1
    PRM_POS_COMPANY_NAME = PRM_POS_LEFT
    PRM_KEY_CURRENCY = 'Currency'
    PRM_ORD_CURRENCY = 3
    PRM_POS_CURRENCY = PRM_POS_LEFT
    PRM_KEY_LABEL = 'Reference'
    PRM_ORD_LABEL = 4
    PRM_POS_LABEL = PRM_POS_LEFT
    PRM_KEY_FY = 'Fiscal Year'
    PRM_ORD_FY = 5
    PRM_POS_FY = PRM_POS_LEFT
    PRM_KEY_PERIOD = 'Fiscal Period'
    PRM_ORD_PERIOD = 6
    PRM_POS_PERIOD = PRM_POS_LEFT
    PRM_KEY_DATE = 'Move Date'
    PRM_ORD_DATE = 7
    PRM_POS_DATE = PRM_POS_LEFT
    PRM_KEY_ACCS = 'Accounts'
    PRM_ORD_ACCS = 8
    PRM_POS_ACCS = PRM_POS_RIGHT
    PRM_KEY_TARGET_MOVE = 'Move Status'
    PRM_ORD_TARGET_MOVE = 9
    PRM_POS_TARGET_MOVE = PRM_POS_RIGHT
    PRM_KEY_JRNLS = 'Journals'
    PRM_ORD_JRNLS = 10
    PRM_POS_JRNLS = PRM_POS_RIGHT
    PRM_KEY_CMP1_SPACING = None
    PRM_ORD_CMP1_SPACING = 11
    PRM_POS_CMP1_SPACING = PRM_POS_RIGHT
    PRM_KEY_CMP1_LABEL = 'Comparison'
    PRM_ORD_CMP1_LABEL = 12
    PRM_POS_CMP1_LABEL = PRM_POS_RIGHT
    PRM_KEY_CMP1_FY = 'Fiscal Year'
    PRM_ORD_CMP1_FY = 13
    PRM_POS_CMP1_FY = PRM_POS_RIGHT
    PRM_KEY_CMP1_PERIOD = 'Fiscal Period'
    PRM_ORD_CMP1_PERIOD = 14
    PRM_POS_CMP1_PERIOD = PRM_POS_RIGHT
    PRM_KEY_CMP1_DATE = 'Move Date'
    PRM_ORD_CMP1_DATE = 15
    PRM_POS_CMP1_DATE = PRM_POS_RIGHT
    PRM_VAL_TIME_FMT = '%d %b %Y'
    PRM_OERP_TIME_FMT = '%Y-%m-%d'

    def get_move_lines_FROM_and_WHERE(self, pool, cr, uid,
                                      beginning_balance_moves=False,
                                      context=None):
        '''Return the SQL FROM and WHERE clauses based on user report generation
           parameters given through the report generation wizard. The clauses
           are used to obtain the general ledger move lines.'''
        fiscalyear_clause = "AND f.state = 'draft'"
        target_move_clause = ''
        journal_selection_clause = ''
        account_selection_clause = ''
        journal_simulation_clause = ''
        period_selection_clause = ''
        date_clause = ''

        report_parameters_left = []
        report_parameters_right = []
        report_parameters = [report_parameters_left, report_parameters_right]
        context['via_financial_reports.report_parameters_left'] = report_parameters_left
        context['via_financial_reports.report_parameters_right'] = report_parameters_right

        # Not every setup has account_simulation installed
        journal_simulation_domain = [('model', '=', 'account.journal'),
                                     ('name', '=', 'state')]
        if pool.get('ir.model.fields').search(cr, uid,
                                              journal_simulation_domain,
                                              context=context):
            journal_simulation_clause = "AND j.state = 'valid'"

        date_clause = ''
        period_selection_clause = ''
        form = context.get('via_financial_reports.form', None)
        if form is not None:
            gl_new = context.get('via_financial_reports.gl_new', False)
            cmp1_phase = context.get('via_financial_reports.cmp1_phase', False)

            def add_report_prm(prm_name, val):
                if bool(cmp1_phase) ^ bool('CMP1_' in prm_name):
                    return
                try:
                    eval('report_parameters[self.PRM_POS_' + prm_name + ']'
                         '.append((self.PRM_ORD_' + prm_name + ','
                         ' self.PRM_KEY_' + prm_name + ', val))',
                         {'self': self, 'report_parameters': report_parameters,
                          'val': val})
                except AttributeError as e:
                    if 'account_tree instance has no attribute ' not in str(e):
                        raise e
                    pass

            rpt_name = form.name or 'N/A'
            add_report_prm('REPORT_NAME', rpt_name)

            acc_pool = pool.get('account.account')
            root_acc = form.chart_account_id
            add_report_prm('COMPANY_NAME', root_acc.company_id.name)
            add_report_prm('CURRENCY', root_acc.company_id.currency_id.name)

            display_account = form.display_account or 'N/A'
            if display_account == 'bal_all':
                display_account_val = 'All'
            elif display_account == 'bal_movement':
                display_account_val = 'With movements'
            elif display_account == 'bal_solde':
                display_account_val = 'With balance is not equal to 0'
            else:
                display_account_val = 'N/A'
            if rpt_name not in ('Balance Sheet', 'Profit/Loss', 'General Ledger/Trial Balance'):
                add_report_prm('DISPLAY_ACCOUNT', display_account_val)

            target_move = form.target_move or False
            if target_move == 'posted':
                target_move_clause = "AND m.state = 'posted'"
            add_report_prm('TARGET_MOVE', (target_move.capitalize()
                                           or self.PRM_VAL_ALL))

            if form.cmp1_enabled:
                add_report_prm('LABEL', form.label or '')
                if cmp1_phase:
                    add_report_prm('CMP1_SPACING', None)
                    add_report_prm('CMP1_LABEL', form.cmp1_label or '')

            if cmp1_phase:
                fy = form.cmp1_fiscalyear_id
            else:
                fy = form.fiscalyear_id
            fiscalyear_clause = ("AND m.date >= '%s' AND m.date <= '%s'"
                                 % (str(fy.date_start), str(fy.date_stop)))
            fy_date_start = strftime(self.PRM_VAL_TIME_FMT,
                                     strptime(fy.date_start,
                                              self.PRM_OERP_TIME_FMT))
            fy_date_stop = strftime(self.PRM_VAL_TIME_FMT,
                                    strptime(fy.date_stop,
                                             self.PRM_OERP_TIME_FMT))
            add_report_prm(('CMP1_' if cmp1_phase else '')
                           + 'FY', ('%s (%s %s %s)' % (fy.name,
                                                       fy_date_start,
                                                       unichr(0x2013),
                                                       fy_date_stop)))

            jrnls = form.journal_ids or False
            if jrnls:
                journal_ids = [jrnl.id for jrnl in jrnls]
                journal_selection_clause = ('INNER JOIN '
                                            + list_to_pgTable(journal_ids, 'js', [('id', 'INTEGER')])
                                            + ' ON j.id = js.id')
                jrnl_names = ', '.join(jrnl.code for jrnl in jrnls)
                add_report_prm('JRNLS', jrnl_names)
            else:
                add_report_prm('JRNLS', self.PRM_VAL_ALL)

            accs = form.account_ids or False
            if (form.name or 'N/A') in ('Trial Balance',
                                        'General Ledger',
                                        'General Ledger/Trial Balance'):
                if accs:
                    account_ids = [acc.id for acc in accs]
                    account_selection_clause = ('INNER JOIN '
                                                + list_to_pgTable(account_ids, 'accs', [('id', 'INTEGER')])
                                                + ' ON acc.id = accs.id')
                    acc_names = ', '.join(acc.code + ' ' + acc.name for acc in accs)
                    add_report_prm('ACCS', acc_names)
                else:
                    add_report_prm('ACCS', self.PRM_VAL_ALL)

            if cmp1_phase:
                date_from = form.cmp1_date_from or False
                date_to = form.cmp1_date_to or False
            else:
                date_from = form.date_from or False
                date_to = form.date_to or False
            if date_from and date_to:
                date_from_str = strftime(self.PRM_VAL_TIME_FMT,
                                         strptime(date_from,
                                                  self.PRM_OERP_TIME_FMT))
                date_to_str = strftime(self.PRM_VAL_TIME_FMT,
                                       strptime(date_to,
                                                self.PRM_OERP_TIME_FMT))
                add_report_prm(('CMP1_' if cmp1_phase else '')
                               + 'DATE', ('%s %s %s' % (date_from_str,
                                                        unichr(0x2013),
                                                        date_to_str)))
                if beginning_balance_moves:
                    date_clause = ("AND m.date >= '" + fy.date_start + "'"
                                   " AND m.date < '" + date_from + "'")
                else:
                    date_clause = ("AND m.date >= '" + date_from + "'"
                                   " AND m.date <= '" + date_to + "'")

            if cmp1_phase:
                period_from = form.cmp1_period_from and form.cmp1_period_from.id or False
                period_to = form.cmp1_period_to and form.cmp1_period_to.id or False
            else:
                period_from = form.period_from and form.period_from.id or False
                period_to = form.period_to and form.period_to.id or False
            period_ids = False
            period_pool = pool.get('account.period')
            if period_from and period_to:
                period_ids = period_pool.build_ctx_periods(cr, uid, period_from,
                                                           period_to)
            if period_ids and type(period_ids) == list and len(period_ids):
                endpoints = period_pool.browse(cr, uid, [period_ids[0],
                                                         period_ids[-1]],
                                               context=context)
                period_start = (endpoints[0].name
                                + ((' (' + strftime(self.PRM_VAL_TIME_FMT,
                                                    strptime(endpoints[0].date_start,
                                                             self.PRM_OERP_TIME_FMT)) + ')')))
                period_stop = (endpoints[-1].name
                               + ((' (' + strftime(self.PRM_VAL_TIME_FMT,
                                                   strptime(endpoints[-1].date_stop,
                                                            self.PRM_OERP_TIME_FMT)) + ')')))
                add_report_prm(('CMP1_' if cmp1_phase else '')
                               + 'PERIOD', ('%s %s %s' % (period_start,
                                                          unichr(0x2013),
                                                          period_stop)))
                if beginning_balance_moves:
                    period_selection_clause = ("AND m.date >= '%s' AND m.date < '%s'"
                                               % (str(fy.date_start),
                                                  str(endpoints[0].date_start)))
                else:
                    period_selection_clause = ("AND m.date >= '%s' AND m.date <= '%s'"
                                               % (str(endpoints[0].date_start),
                                                  str(endpoints[-1].date_stop)))
        # When there is no time filter, report only within one fiscal year
        if len(date_clause) == 0 and len(period_selection_clause) == 0:
            if beginning_balance_moves:
                date_clause = 'AND FALSE'
            else:
                date_clause = ("AND m.date >= '" + fy.date_start + "'"
                               " AND m.date < '" + fy.date_stop + "'")
        return ('''
 account_move_line l
 INNER JOIN account_move m ON l.move_id = m.id
 INNER JOIN account_journal j ON l.journal_id = j.id
 INNER JOIN account_account acc ON l.account_id = acc.id
 INNER JOIN account_period p ON l.period_id = p.id
 INNER JOIN account_fiscalyear f ON p.fiscalyear_id = f.id
 %(journal_selection_clause)s
 %(account_selection_clause)s
''' % {
    'journal_selection_clause': journal_selection_clause,
    'account_selection_clause': account_selection_clause,
}, '''
 l.state != 'draft'
 %(target_move_clause)s
 %(fiscalyear_clause)s
 %(period_selection_clause)s
 %(date_clause)s
 %(journal_simulation_clause)s
''' % {
    'fiscalyear_clause': fiscalyear_clause,
    'target_move_clause': target_move_clause,
    'period_selection_clause': period_selection_clause,
    'date_clause': date_clause,
    'journal_simulation_clause': journal_simulation_clause,
})

    def get_beginning_balance_FROM_and_WHERE(self, pool, cr, uid, context=None):
        return self.get_move_lines_FROM_and_WHERE(pool, cr, uid,
                                                  beginning_balance_moves=True,
                                                  context=context)

    def create_total(self, dr=0.0, cr=0.0, mv=0.0, bd=0.0, bc=0.0, bb=0.0, eb=0.0,
                     lm=False):
        return [dr, cr, mv, bd, bc, bb, eb, lm]

    def read_total(self, total, field):
        if field == 'dr':
            return total[self.IDX_TOTAL_DEBIT]
        elif field == 'cr':
            return total[self.IDX_TOTAL_CREDIT]
        elif field == 'mv':
            return total[self.IDX_TOTAL_MOVEMENT]
        elif field == 'bd':
            return total[self.IDX_TOTAL_BEGINNING_BALANCE_DEBIT]
        elif field == 'bc':
            return total[self.IDX_TOTAL_BEGINNING_BALANCE_CREDIT]
        elif field == 'bb':
            return total[self.IDX_TOTAL_BEGINNING_BALANCE]
        elif field == 'eb':
            return total[self.IDX_TOTAL_ENDING_BALANCE]
        elif field == 'lm':
            return total[self.IDX_TOTAL_LINEARIZE_ME]
        else:
            raise Exception('Unknown field name "%s"' % field)

    def update_total(self, total,
                     new_dr=None, new_cr=None, new_mv=None,
                     new_bd=None, new_bc=None, new_bb=None, new_eb=None,
                     new_lm=None):
        if new_dr is not None:
            total[self.IDX_TOTAL_DEBIT] = new_dr
        if new_cr is not None:
            total[self.IDX_TOTAL_CREDIT] = new_cr
        if new_mv is not None:
            total[self.IDX_TOTAL_MOVEMENT] = new_mv
        if new_bd is not None:
            total[self.IDX_TOTAL_BEGINNING_BALANCE_DEBIT] = new_bd
        if new_bc is not None:
            total[self.IDX_TOTAL_BEGINNING_BALANCE_CREDIT] = new_bc
        if new_bb is not None:
            total[self.IDX_TOTAL_BEGINNING_BALANCE] = new_bb
        if new_eb is not None:
            total[self.IDX_TOTAL_ENDING_BALANCE] = new_eb
        if new_lm is not None:
            total[self.IDX_TOTAL_LINEARIZE_ME] |= new_lm

    def reset_total(self, total):
        for i in range(len(total)):
            total[i] = 0.0
        total[self.IDX_TOTAL_LINEARIZE_ME] = False

    def get_account_move_lines(self, pool, cr, uid, account_ids,
                               needed_account_ids, context=None):
        '''Return general ledger move lines as the following tuple:
           (account_id, move_line_id, debit, credit, currency_id).
           This is originally used to populate general ledger with
           moves report. The currency_id is needed to make all numbers
           appearing in the general ledger report have the same currency
           for ease of reading.'''

        account_currency_dict = dict(map(lambda e: [e[0], (e[1], e[2])],
                                         needed_account_ids))

        res = {}
        if context.get('via_financial_reports.gl_new', False):
            res = context.get('via_financial_reports.gl_new_move_lines')
            if not (context.get('via_financial_reports.form', False)
                    and context['via_financial_reports.form'].display_move):
                return res

        (move_line_FROM,
         move_line_WHERE) = self.get_move_lines_FROM_and_WHERE(pool, cr, uid,
                                                               context=context)
        q = '''
SELECT
 t.account_id AS account_id,
 data.move_line_id AS move_line_id,
 COALESCE(data.move_line_debit, 0.0) AS move_line_debit,
 COALESCE(data.move_line_credit, 0.0) AS move_line_credit,
 data.move_line_currency AS move_line_currency,
 data.company_id AS move_line_com_id,
 data.move_line_date AS move_line_date,
 data.move_line_name AS move_line_name,
 aat.conversion_method AS conversion_method,
 aat.name AS aat_name,
 acc.code || ' ' || acc.name AS acc_name
FROM
 %(account_ids_table)s
 INNER JOIN account_account acc
  ON t.account_id = acc.id
 INNER JOIN account_account_type aat
  ON acc.user_type = aat.id
 LEFT JOIN (SELECT
             l.account_id AS account_id,
             l.id AS move_line_id,
             l.debit AS move_line_debit,
             l.credit AS move_line_credit,
             a.currency_id AS move_line_currency,
             l.date AS move_line_date,
             l.company_id AS company_id,
             l.name AS move_line_name
            FROM
             %(move_line_FROM)s
             INNER JOIN account_account a
              ON l.account_id = a.id
            WHERE
             %(move_line_WHERE)s) data
 ON t.account_id = data.account_id
ORDER BY
 move_line_com_id, move_line_date, move_line_name
''' % {
    'account_ids_table': list_to_pgTable(account_ids, 't',
                                         [('account_id', 'INTEGER')]),
    'move_line_FROM': move_line_FROM,
    'move_line_WHERE': move_line_WHERE,
}
        cr.execute(q)

        for record in cr.dictfetchall():
            move_lines = res.setdefault(record['account_id'], [])
            if record['move_line_id']:
                acc_id = record['account_id']
                curr_list = account_currency_dict[acc_id][0]
                conversion_method = record['conversion_method']

                if conversion_method == 'trx_rate':
                    conversion_date = record['move_line_date']
                elif conversion_method == 'rpt_rate':
                    conversion_date = context.get('via_financial_reports.form.bs_as_of',
                                                  str(date.today()))
                else:
                    raise osv.except_osv(_('Error !'),
                                         _('Account type "%s" of account "%s"'
                                           ' has no conversion  method !'
                                           % (record['aat_name'],
                                              record['acc_name'])))

                record['move_line_debit'] = chained_currency_converter(curr_list,
                                                                       record['move_line_debit'],
                                                                       conversion_date)
                record['move_line_credit'] = chained_currency_converter(curr_list,
                                                                        record['move_line_credit'],
                                                                        conversion_date)
                move_lines.append(record)
        return res

    def get_com_parents(self, pool, cr, uid, root_com_id, context=None):
        '''Return a dictionary whose keys are the ID of the given root_com_id
           and the IDs of the companies that are the descendants of root_com_id.
           The value of each key is a list of company IDs that are the ancestors
           of the corresponding company.'''
        def _get_com_parents(root_com, ancestors, res):
            res[root_com.id] = ancestors[:]
            ancestors.append(root_com.id)
            for child_com in root_com.child_ids:
                _get_com_parents(child_com, ancestors, res)
            del ancestors[-1]
        res = {}
        _get_com_parents(pool.get('res.company').browse(cr, uid, root_com_id,
                                                        context=context),
                         [], res)
        return res

    def get_gl_report_type_total(self, pool, cr, uid, root_com_id, context=None):
        '''Return a dictionary whose keys are the ID of the given root_com_id and
           the IDs of the companies that are the descendants of root_com_id. The
           value of each key is a dictionary whose keys are the four report types
           and the values are dr-cr-bal lists containing the total of all move
           lines of a certain report type of the corresponding company and its
           descendants.'''
        com_parents = self.get_com_parents(pool, cr, uid, root_com_id, context)
        com_ids = [cid for cid in com_parents.iterkeys()]

        (move_line_FROM,
         move_line_WHERE) = self.get_move_lines_FROM_and_WHERE(pool, cr, uid,
                                                               context=context)
        (bb_FROM,
         bb_WHERE) = self.get_beginning_balance_FROM_and_WHERE(pool, cr, uid,
                                                               context=context)
        q = '''
SELECT
 COALESCE(data.account_id, beginning_balance.account_id) AS account_id,
 COALESCE(data.debit, 0) AS debit,
 COALESCE(data.credit, 0) AS credit,
 COALESCE(beginning_balance.debit, 0) AS bb_debit,
 COALESCE(beginning_balance.credit, 0) AS bb_credit,
 acc_type.report_type AS report_type,
 com_t.com_id AS cid,
 com.currency_id AS currency_id
FROM
 (SELECT
   l.account_id AS account_id,
   SUM(l.debit) AS debit,
   SUM(l.credit) AS credit
  FROM
   %(move_line_FROM)s
  WHERE
   %(move_line_WHERE)s
  GROUP BY l.account_id) data
 FULL JOIN (SELECT
             l.account_id AS account_id,
             SUM(l.debit) AS debit,
             SUM(l.credit) AS credit
            FROM
             %(bb_FROM)s
            WHERE
             %(bb_WHERE)s
            GROUP BY l.account_id) beginning_balance
  ON data.account_id = beginning_balance.account_id
 INNER JOIN account_account acc
  ON acc.id = COALESCE(data.account_id,
                       beginning_balance.account_id)
 INNER JOIN (SELECT aat.id AS id, at_nm.report_type AS report_type
             FROM account_account_type aat
              INNER JOIN account_account_financial_report_type afr_2_aat
               ON aat.id = afr_2_aat.account_type_id
              INNER JOIN account_financial_report afr
               ON afr_2_aat.report_id = afr.id
              INNER JOIN ir_model_data imd
               ON (afr.id = imd.res_id
                   AND imd.module = 'account')
              INNER JOIN UNNEST(ARRAY[('account_financial_report_assets0'::TEXT, 'asset'::TEXT),
                                      ('account_financial_report_liability0'::TEXT, 'liability'::TEXT),
                                      ('account_financial_report_income0'::TEXT, 'income'::TEXT),
                                      ('account_financial_report_expense0'::TEXT, 'expense'::TEXT)]) at_nm (xml_id TEXT, report_type TEXT)
               ON (imd.name = at_nm.xml_id)) acc_type
  ON acc.user_type = acc_type.id
 INNER JOIN %(com_ids_table)s
  ON com_t.com_id = acc.company_id
 INNER JOIN res_company com
  ON com.id = com_t.com_id
WHERE
 acc_type.report_type IN %(report_types)s
GROUP BY
 COALESCE(data.account_id, beginning_balance.account_id),
 COALESCE(data.debit, 0),
 COALESCE(data.credit, 0),
 COALESCE(beginning_balance.debit, 0),
 COALESCE(beginning_balance.credit, 0),
 acc_type.report_type,
 com_t.com_id,
 com.currency_id
''' % {
    'com_ids_table': list_to_pgTable(com_ids, 'com_t', [('com_id', 'INTEGER')]),
    'move_line_FROM': move_line_FROM,
    'move_line_WHERE': move_line_WHERE,
    'bb_FROM': bb_FROM,
    'bb_WHERE': bb_WHERE,
    'report_types': str((self.ASSET_ACC, self.LIABILITY_ACC,
                         self.INCOME_ACC, self.EXPENSE_ACC)),
}
        cr.execute(q)

        # Get each company GL report type totals
        report_type_total = dict([cid, {
            self.ASSET_ACC: self.create_total(),
            self.LIABILITY_ACC: self.create_total(),
            self.INCOME_ACC: self.create_total(),
            self.EXPENSE_ACC: self.create_total(),
        }] for cid in com_ids)
        for record in cr.dictfetchall():
            cid = record['cid']
            report_type = record['report_type']
            currency_id = record['currency_id']
            dr = record['debit']
            cr = record['credit']
            bd = record['bb_debit']
            bc = record['bb_credit']
            self.update_idx_total(report_type_total[cid][report_type], dr, cr,
                                  bd, bc, True)
            # Update the ancestors as well
            for ancestor_cid in com_parents[cid]:
                self.update_idx_total(report_type_total[ancestor_cid][report_type],
                                      dr, cr, bd, bc, True)

        return report_type_total

    def get_gl_profit_loss(self, gl_report_type_total):
        '''Return a dictionary whose keys are those in the given
           gl_report_type_total and whose values is the following tuple:
           (profit_loss_type, profit_loss) where profit_loss is a dr-cr-bal
           list.'''
        res = {}
        for (cid, com_report_type_total) in gl_report_type_total.iteritems():
            profit_loss = self.create_total()

            com_total_income = com_report_type_total[self.INCOME_ACC]
            com_total_expense = com_report_type_total[self.EXPENSE_ACC]

            income_abs_bal = abs(self.read_total(com_total_income, 'mv'))
            expense_abs_bal = abs(self.read_total(com_total_expense, 'mv'))
            income_abs_bb = abs(self.read_total(com_total_income, 'bb'))
            expense_abs_bb = abs(self.read_total(com_total_expense, 'bb'))

            self.update_idx_total(profit_loss, expense_abs_bal, income_abs_bal,
                                  expense_abs_bb, income_abs_bb, True)

            if self.read_total(profit_loss, 'mv') <= 0.0:
                mv_profit_loss_type = 'profit'
            else:
                mv_profit_loss_type = 'loss'
            if self.read_total(profit_loss, 'eb') <= 0.0:
                eb_profit_loss_type = 'profit'
            else:
                eb_profit_loss_type = 'loss'

            res[cid] = ((mv_profit_loss_type, eb_profit_loss_type), profit_loss)
        return res

    def get_account_data_rpt_rate(self, pool, cr, uid, needed_account_ids,
                                  context=None):
        if len(needed_account_ids) == 0:
            return {}

        (move_line_FROM,
         move_line_WHERE) = self.get_move_lines_FROM_and_WHERE(pool, cr, uid,
                                                               context=context)
        (bb_FROM,
         bb_WHERE) = self.get_beginning_balance_FROM_and_WHERE(pool, cr, uid,
                                                               context=context)
        account_currency_dict = dict(map(lambda e: [e[0], e[1]],
                                         needed_account_ids))
        account_ids = account_currency_dict.keys()
        q = '''
SELECT
 t.account_id AS account_id,
 COALESCE(data.debit, 0) AS debit,
 COALESCE(data.credit, 0) AS credit,
 COALESCE(data.move_count, 0) AS move_count,
 COALESCE(beginning_balance.debit, 0) AS bb_debit,
 COALESCE(beginning_balance.credit, 0) AS bb_credit
FROM
 %(account_ids_table)s
 LEFT JOIN (SELECT
             l.account_id AS account_id,
             SUM(l.debit) AS debit,
             SUM(l.credit) AS credit,
             COUNT(l.id) AS move_count
            FROM
             %(move_line_FROM)s
            WHERE
             %(move_line_WHERE)s
            GROUP BY l.account_id) data
 ON t.account_id = data.account_id
 LEFT JOIN (SELECT
             l.account_id AS account_id,
             SUM(l.debit) AS debit,
             SUM(l.credit) AS credit
            FROM
             %(bb_FROM)s
            WHERE
             %(bb_WHERE)s
            GROUP BY l.account_id) beginning_balance
 ON t.account_id = beginning_balance.account_id
''' % {
    'account_ids_table': list_to_pgTable(account_ids, 't', [('account_id', 'INTEGER')]),
    'move_line_FROM': move_line_FROM,
    'move_line_WHERE': move_line_WHERE,
    'bb_FROM': bb_FROM,
    'bb_WHERE': bb_WHERE,
}
        cr.execute(q)

        conversion_date = context.get('via_financial_reports.form.bs_as_of',
                                      str(date.today()))
        res = {}
        for record in cr.dictfetchall():
            acc_id = record['account_id']
            curr_list = account_currency_dict[acc_id]
            record['debit'] = chained_currency_converter(curr_list,
                                                         record['debit'],
                                                         conversion_date)
            record['credit'] = chained_currency_converter(curr_list,
                                                          record['credit'],
                                                          conversion_date)
            record['bb_debit'] = chained_currency_converter(curr_list,
                                                            record['bb_debit'],
                                                            conversion_date)
            record['bb_credit'] = chained_currency_converter(curr_list,
                                                             record['bb_credit'],
                                                             conversion_date)
            res[acc_id] = record
        return res

    def get_account_data_trx_rate(self, pool, cr, uid, needed_account_ids,
                                  context=None):
        if len(needed_account_ids) == 0:
            return {}

        (move_line_FROM,
         move_line_WHERE) = self.get_move_lines_FROM_and_WHERE(pool, cr, uid,
                                                               context=context)
        (bb_FROM,
         bb_WHERE) = self.get_beginning_balance_FROM_and_WHERE(pool, cr, uid,
                                                               context=context)
        account_currency_dict = dict(map(lambda e: [e[0], e[1]],
                                         needed_account_ids))
        account_ids = account_currency_dict.keys()
        res = dict([k, {'account_id': k,
                        'debit': 0.0,
                        'credit': 0.0,
                        'move_count': 0,
                        'bb_debit': 0.0,
                        'bb_credit': 0.0}]
                   for k in account_currency_dict.iterkeys())

        q = '''
SELECT
 t.account_id AS account_id,
 COALESCE(data.debit, 0) AS debit,
 COALESCE(data.credit, 0) AS credit,
 data.move_count AS move_count,
 data.date AS date
FROM
 %(account_ids_table)s
 INNER JOIN (SELECT
              l.account_id AS account_id,
              l.debit AS debit,
              l.credit AS credit,
              1 AS move_count,
              l.date AS date
             FROM
              %(move_line_FROM)s
             WHERE
              %(move_line_WHERE)s) data
 ON t.account_id = data.account_id
''' % {
    'account_ids_table': list_to_pgTable(account_ids, 't', [('account_id', 'INTEGER')]),
    'move_line_FROM': move_line_FROM,
    'move_line_WHERE': move_line_WHERE,
}
        cr.execute(q)
        for record in cr.dictfetchall():
            acc_id = record['account_id']
            res_entry = res[acc_id]
            curr_list = account_currency_dict[acc_id]
            res_entry['debit'] += chained_currency_converter(curr_list,
                                                             record['debit'],
                                                             record['date'])
            res_entry['credit'] += chained_currency_converter(curr_list,
                                                              record['credit'],
                                                              record['date'])
            res_entry['move_count'] += 1

        q_bb = '''
SELECT
 t.account_id AS account_id,
 COALESCE(beginning_balance.debit, 0) AS bb_debit,
 COALESCE(beginning_balance.credit, 0) AS bb_credit,
 beginning_balance.date AS bb_date
FROM
 %(account_ids_table)s
 INNER JOIN (SELECT
              l.account_id AS account_id,
              l.debit AS debit,
              l.credit AS credit,
              l.date AS date
             FROM
              %(bb_FROM)s
             WHERE
              %(bb_WHERE)s) beginning_balance
 ON t.account_id = beginning_balance.account_id
''' % {
    'account_ids_table': list_to_pgTable(account_ids, 't', [('account_id', 'INTEGER')]),
    'bb_FROM': bb_FROM,
    'bb_WHERE': bb_WHERE,
}
        cr.execute(q_bb)
        for record in cr.dictfetchall():
            acc_id = record['account_id']
            res_entry = res[acc_id]
            curr_list = account_currency_dict[acc_id]
            res_entry['bb_debit'] += chained_currency_converter(curr_list,
                                                                record['bb_debit'],
                                                                record['bb_date'])
            res_entry['bb_credit'] += chained_currency_converter(curr_list,
                                                                 record['bb_credit'],
                                                                 record['bb_date'])

        return res

    def get_account_data(self, pool, cr, uid, needed_account_ids, context=None):
        res = {}
        res.update(self.get_account_data_rpt_rate(pool, cr, uid,
                                                  filter(lambda e: e[2] == False,
                                                         needed_account_ids),
                                                  context=context))
        res.update(self.get_account_data_trx_rate(pool, cr, uid,
                                                  filter(lambda e: e[2] == True,
                                                         needed_account_ids),
                                                  context=context))
        return res

    def reset_account_tree(self, node):
        '''Given a node of an account tree, the dr-cr-bal lists of the node and
           all of its descendants are set to zero.'''
        curr_total = node[self.IDX_TOTAL]
        for k in curr_total.iterkeys():
            curr_total[k] = self.create_total()
        for subtree in node[self.IDX_CHILDREN]:
            self.reset_account_tree(subtree)

    def create_tree_node(self, acc_id=None, children=None, level=None,
                         dr=0.0, cr=0.0, bd=0.0, bc=0.0, currency_id=None,
                         total_text=None, company_id=None, acc_type=None,
                         report_type=None, total=None, move_count=0,
                         force_multicompany=False, dont_calculate=False,
                         company_ids=None, consol_children=None):
        if children is None:
            children = []
        if consol_children is None:
            consol_children = []
        if company_ids is None:
            company_ids = []
        if total is None:
            total = dict([cid, self.create_total()] for cid in company_ids)
        return [acc_id, children, level, dr, cr, currency_id, total_text,
                company_id, acc_type, total, dont_calculate, force_multicompany,
                move_count, report_type, bd, bc, consol_children]

    def get_tree_skeleton(self, acc_pool, cr, uid, root_account_id,
                          needed_account_ids, context=None):
        '''needed_account_ids is a list of [acc_id, [currency_chain],
        True if under income/expense head account else False]
        '''
        if not root_account_id:
            return None

        root_account = acc_pool.browse(cr, uid, root_account_id, context=context)
        income_expense_head_account_ids = (root_account.company_id.income_head_account.id,
                                           root_account.company_id.expense_head_account.id)

        def _get_tree_skeleton(root_account,
                               needed_account_ids, level, company_ids,
                               currency_chain,
                               under_income_expense_head_account,
                               parent_account_company):
            '''Get the complete tree using depth-first search.'''
            under_income_expense_head_account |= (root_account.id
                                                  in income_expense_head_account_ids)
            com_pool = pooler.get_pool(cr.dbname).get('res.company')
            com = com_pool.browse(cr, uid, root_account.company_id.id,
                                  context=context)
            parent_com = com_pool.browse(cr, uid, parent_account_company.id,
                                         context=context)
            if parent_account_company.id != root_account.company_id.id:
                currency_chain_entry = [com.currency_id]
                if under_income_expense_head_account:
                    if (com.consolidation_exchange_rate_pl
                        or com.consolidation_exchange_rate):
                        currency_chain_entry.append(com.consolidation_exchange_rate_pl
                                                    or com.consolidation_exchange_rate)
                    else:
                        # As discussed with DS, when not specified use company's
                        # currency to make the user aware of the config error
                        # because no currency conversion takes place
                        currency_chain_entry.append(com.currency_id)
                else:
                    if (com.consolidation_exchange_rate_bs
                        or com.consolidation_exchange_rate):
                        currency_chain_entry.append(com.consolidation_exchange_rate_bs
                                                    or com.consolidation_exchange_rate)
                    else:
                        # As discussed with DS, when not specified use company's
                        # currency to make the user aware of the config error
                        # because no currency conversion takes place
                        currency_chain_entry.append(com.currency_id)
                currency_chain.insert(0, currency_chain_entry)

            if (root_account.user_type.conversion_method not in ('rpt_rate', 'trx_rate')
                and root_account.type != 'view'):
                    raise osv.except_osv(_('Error !'),
                                         _('Account type "%s" of account "%s %s"'
                                           ' has no conversion  method !'
                                           % (root_account.user_type.name,
                                              root_account.code,
                                              root_account.name)))

            needed_account_ids.append([root_account.id, list(currency_chain),
                                       (root_account.user_type.conversion_method
                                        == 'trx_rate')])

            children = []
            for acc in root_account.child_id:
                children.append(_get_tree_skeleton(acc,
                                                   needed_account_ids,
                                                   level + 1, company_ids,
                                                   currency_chain,
                                                   under_income_expense_head_account,
                                                   root_account.company_id))

            if parent_account_company.id != root_account.company_id.id:
                del currency_chain[0]

            # Check that the company structure is correct
            if root_account.company_id.id not in company_ids:
                raise CompanyHierarchyError(root_account)
            # This is the tree node
            return self.create_tree_node(acc_id=root_account.id,
                                         children=children,
                                         level=level,
                                         currency_id=com.currency_id.id,
                                         company_id=root_account.company_id.id,
                                         acc_type=root_account.type,
                                         report_type=root_account.user_type.report_type,
                                         company_ids=company_ids,
                                         consol_children=root_account.child_consol_ids)

        company_ids = get_company_ids(root_account.company_id)

        return _get_tree_skeleton(root_account,
                                  needed_account_ids, 0, company_ids,
                                  [],
                                  False,
                                  root_account.company_id)

    def update_idx_total(self, total, dr, cr, bd, bc, lm):
        '''Add the given dr, cr, bd, and bc into total.'''
        new_dr = self.read_total(total, 'dr') + dr
        new_cr = self.read_total(total, 'cr') + cr
        new_mv = new_dr - new_cr
        new_bd = self.read_total(total, 'bd') + bd
        new_bc = self.read_total(total, 'bc') + bc
        new_bb = new_bd - new_bc
        new_eb = new_bb + new_mv
        self.update_total(total,
                          new_dr=new_dr, new_cr=new_cr, new_mv=new_mv,
                          new_bd=new_bd, new_bc=new_bc, new_bb=new_bb,
                          new_eb=new_eb, new_lm=lm)

    def sub_idx_totals(self, com_total_1, com_total_2):
        '''Subtract total com_total_2 from total com_total_1.'''
        for (k, v) in com_total_2.iteritems():
            self.update_idx_total(com_total_1[k],
                                  -self.read_total(v, 'dr'),
                                  -self.read_total(v, 'cr'),
                                  -self.read_total(v, 'bd'),
                                  -self.read_total(v, 'bc'),
                                  self.read_total(v, 'lm'))

    def calculate_account_tree(self, node, parent_total=None, context=None):
        '''Sum up the debit and credit of all accounts in the tree.'''
        if context is None:
            context = {}

        curr_total = node[self.IDX_TOTAL]

        dont_calculate = node[self.IDX_DONT_CALCULATE]
        if not dont_calculate:

            # Start with this account's own debit and credit
            curr_com = node[self.IDX_COMPANY]
            curr_com_total = curr_total[curr_com]
            self.reset_total(curr_com_total)
            self.update_idx_total(curr_com_total,
                                  node[self.IDX_DEBIT],
                                  node[self.IDX_CREDIT],
                                  node[self.IDX_BB_DEBIT],
                                  node[self.IDX_BB_CREDIT],
                                  True)

            # Iterate the children first
            for subtree in node[self.IDX_CHILDREN]:
                self.calculate_account_tree(subtree, curr_total, context)

            # A consolidation account has its debit and credit taken from its
            # cons-children as well.
            cons_account = (node[self.IDX_TYPE] == self.CONS_ACC)
            if cons_account and not context.get('via_financial_reports.calculating_retained_earnings', False):
                cons_children_com_ids = set(n.company_id.id
                                            for n in node[self.IDX_CONSOL_CHILDREN])
                # cons_children_com_ids is needed because what needs to be summed
                # to the consolidation account total is only from the companies
                # of the cons-children as illustrated below:
                #                                   +-----------+-----------+-----------+-----------+
                #                                   | Company_A | Company_B | Company_C | Company_D |
                #                                   +-----------+-----------+-----------+-----------+
                # Consolidated_Account_Company_A    | Y1 + Y2   | Y1        | Y1        | Y2        |
                # |                                 |           |           |           |           |
                # |                                 +-----------+-----------+-----------+-----------+
                # +- Consolidated_Account_Company_B |           | Y1        | Y1        |           |
                # |  |                              |           |           |           |           |
                # |  |                              +-----------+-----------+-----------+-----------+
                # |  +- Account_Company_C           |           |           | Y1        |           |
                # |                                 |           |           |           |           |
                # |                                 +-----------+-----------+-----------+-----------+
                # +- Account_Company_D              |           |           |           | Y2        |
                #                                   |           |           |           |           |
                #                                   +-----------+-----------+-----------+-----------+
                # Without cons_children_com_ids, column Company_A would be Y1 + Y1 + Y2 instead of
                # the correct one Y1 + Y2.
                # This is also the reason why function linearize_tree needs cons_children_com_ids
                # to decide which cell in the crosstab needs to have value.
                for (k, v) in curr_total.iteritems():
                    if k in cons_children_com_ids:
                        self.update_idx_total(curr_com_total,
                                              self.read_total(v, 'dr'),
                                              self.read_total(v, 'cr'),
                                              self.read_total(v, 'bd'),
                                              self.read_total(v, 'bc'),
                                              self.read_total(v, 'lm'))

        if context.get('via_financial_reports.gl_new', False):
            move_lines = context['via_financial_reports.gl_new_move_lines']
            l = move_lines.setdefault(node[self.IDX_ACCOUNT], [])
            com_id = node[self.IDX_COMPANY]
            com_total = node[self.IDX_TOTAL][com_id]
            if (context.get('via_financial_reports.form', False)
                and context['via_financial_reports.form'].display_move):
                move_count = node[self.IDX_MOVE_COUNT]
            else:
                move_count = 0
            l.append({
                'move_line_id': 0,
                'move_line_com_id': com_id,
                'move_line_debit': self.read_total(com_total, 'dr'),
                'move_line_credit': self.read_total(com_total, 'cr'),
                'move_line_currency': node[self.IDX_CURRENCY],
                'acc_level': node[self.IDX_LEVEL],
                'line_type': None,
                'acc_move_count': move_count,
            })
            if move_count == 0:
                l.append({
                    'move_line_id': -2,
                    'move_line_com_id': com_id,
                    'move_line_debit': self.read_total(com_total, 'eb'),
                    'move_line_credit': 0.0,
                    'move_line_currency': node[self.IDX_CURRENCY],
                    'acc_level': node[self.IDX_LEVEL],
                    'line_type': None,
                    'acc_move_count': move_count,
                })

        # Update the parent's total
        if parent_total is not None:
            for (k, v) in curr_total.iteritems():
                self.update_idx_total(parent_total[k],
                                      self.read_total(v, 'dr'),
                                      self.read_total(v, 'cr'),
                                      self.read_total(v, 'bd'),
                                      self.read_total(v, 'bc'),
                                      self.read_total(v, 'lm'))

    def flesh_out_skeleton(self, node, data):
        account_id = node[self.IDX_ACCOUNT]
        node[self.IDX_DEBIT] = data[account_id]['debit']
        node[self.IDX_CREDIT] = data[account_id]['credit']
        node[self.IDX_MOVE_COUNT] = data[account_id]['move_count']
        node[self.IDX_BB_DEBIT] = data[account_id]['bb_debit']
        node[self.IDX_BB_CREDIT] = data[account_id]['bb_credit']
        data[account_id]['tree_node'] = node

        for subtree in node[self.IDX_CHILDREN]:
            self.flesh_out_skeleton(subtree, data)

    # The in-out argument nth reflects the nth of the last processed node.
    # That is, if the whole tree has only one node, nth will stay the same
    # because the current value of nth is assigned to the one node. If the
    # whole tree has two nodes with parent-child relationship, the nth will
    # be the value of the original nth plus one because the original nth
    # value is assigned to the parent and nth+1 is assigned to the child.
    def linearize_tree(self, node, nth, res, move_lines=None,
                       do_not_display=None, context=None):
        if context is None:
            context = {}

        def fill_element(element, this_nth, curr_com, curr_com_total, node,
                         active_com):
            element.extend([this_nth,
                            node[self.IDX_ACCOUNT],
                            node[self.IDX_LEVEL],
                            self.read_total(curr_com_total, 'dr'),
                            self.read_total(curr_com_total, 'cr'),
                            self.read_total(curr_com_total, 'mv'),
                            self.read_total(curr_com_total, 'bb'),
                            self.read_total(curr_com_total, 'eb'),
                            node[self.IDX_TOTAL_TEXT],
                            curr_com,
                            str(node[self.IDX_REPORT_TYPE])])
            if context.get('via_financial_reports.gl_new', False):
                element.append(active_com)
            if (context.get('via_jasper_report_utils.rpt_name', False)
                in ('Balance Sheet', 'Profit/Loss', 'General Ledger/Trial Balance')):  # Using reporting tree
                element.extend([self.read_total(curr_com_total, 'bd'),
                                self.read_total(curr_com_total, 'bc')])

        display_me = True
        if do_not_display is not None and id(node) in do_not_display:
            display_me = False

        if display_me:
            curr_total = node[self.IDX_TOTAL]

            total_node = (node[self.IDX_TYPE] in (self.VIEW_ACC, self.CONS_ACC)
                          or node[self.IDX_FORCE_MULTICOMPANY])
            if total_node:
                if node[self.IDX_FORCE_MULTICOMPANY]:
                    len_curr_total = len(curr_total)
                else:
                    len_curr_total = len(filter(lambda e: self.read_total(e,
                                                                          'lm'),
                                                curr_total.itervalues()))
                l = [[] for i in range(len_curr_total)]
            else:
                l = [[]]
            res.extend(l)

            this_nth = nth[0]

            if move_lines is not None:
                if context.get('via_financial_reports.gl_new', False):
                    if node[self.IDX_ACCOUNT] in move_lines:
                        lines = move_lines[node[self.IDX_ACCOUNT]]
                        last_move_line_id = None
                        total_lines = []
                        ending_balance_lines = []
                        for line in lines:
                            if last_move_line_id != line['move_line_id']:
                                if line['move_line_id'] not in (0, -2):
                                    nth[0] += 1
                                last_move_line_id = line['move_line_id']
                            if line['move_line_id'] == 0:
                                total_lines.append(line)
                            elif line['move_line_id'] == -2:
                                ending_balance_lines.append(line)
                            else:
                                line['line_type'] = None
                                line['acc_move_count'] = None
                            line['tree_order'] = nth[0]
                            line['acc_level'] = node[self.IDX_LEVEL]
                        line['line_type'] = 'last'
                        nth[0] += 1
                        for line in total_lines:
                            line['tree_order'] = nth[0]
                        nth[0] += 1
                        for line in ending_balance_lines:
                            line['tree_order'] = nth[0]
                else:
                    lines = move_lines[node[self.IDX_ACCOUNT]]
                    for line in lines:
                        nth[0] += 1
                        line['tree_order'] = nth[0]

        for subtree in node[self.IDX_CHILDREN]:
            nth[0] += 1
            self.linearize_tree(subtree, nth, res, move_lines=move_lines,
                                do_not_display=do_not_display, context=context)

        if display_me:
            curr_com = node[self.IDX_COMPANY]
            if total_node:
                i = 0
                for (k, v) in curr_total.iteritems():
                    if (not node[self.IDX_FORCE_MULTICOMPANY]
                        and not self.read_total(v, 'lm')):
                            continue
                    fill_element(l[i], this_nth, k, v, node, curr_com)
                    i += 1
            else:
                curr_com_total = curr_total[curr_com]
                fill_element(l[0], this_nth, curr_com, curr_com_total, node, curr_com)

    def stringify_tree(self, linearized_tree, context=None):
        if context is None:
            context = {}
        type_cast = [('tree_order', 'INTEGER'), ('account_id', 'INTEGER'),
                     ('level', 'INTEGER'), ('debit', 'NUMERIC'),
                     ('credit', 'NUMERIC'), ('movement', 'NUMERIC'),
                     ('beginning_balance', 'NUMERIC'),
                     ('ending_balance', 'NUMERIC'),
                     ('total_name', 'TEXT'), ('company_id', 'INTEGER'),
                     ('acc_type', 'TEXT')]
        if context.get('via_financial_reports.gl_new', False):
            type_cast.append(('active_com_id', 'INTEGER'))

        if (context.get('via_jasper_report_utils.rpt_name', False)
            in ('Balance Sheet', 'Profit/Loss', 'General Ledger/Trial Balance')):  # Using reporting tree
            if context['via_jasper_report_utils.rpt_name'] == 'General Ledger/Trial Balance':
                acc_data = map(lambda e: [e[1], e[9], [e[12], e[13], e[3], e[4]]],
                               filter(lambda e: e[2] != -1, linearized_tree))
            else:
                acc_data = map(lambda e: [e[1], e[9], [e[11], e[12], e[3], e[4]]],
                               filter(lambda e: e[2] != -1, linearized_tree))
            acc_dict = {}
            for acc_datum in acc_data:
                com_data = acc_dict.setdefault(acc_datum[0], {})
                com_data[acc_datum[1]] = acc_datum[2]

            normalizer = context['via_financial_reports.normalizer']
            rounder = context['via_financial_reports.rounder']
            is_zero = context['via_financial_reports.is_zero']

            def update_com_data(target, multiplier, *com_data_dicts):
                for com_data_dict in com_data_dicts:
                    for (com_id, com_data) in com_data_dict.iteritems():
                        data = target.setdefault(com_id, [0.0, 0.0, 0.0, 0.0])
                        for i in range(4):
                            data[i] = (data[i]
                                       + rounder(multiplier
                                                 * com_data[i]))

            form = context.get('via_financial_reports.form', False)

            node_data = {}
            rt_move_lines = {}
            rt_move_lines_bb = {}
            context['via_financial_reports.reporting_tree_move_lines'] = rt_move_lines
            context['via_financial_reports.reporting_tree_move_lines_bb'] = rt_move_lines_bb
            for node in form.tree_id.node_ids:
                com_data = node_data.setdefault(node.id, {})
                move_lines = []

                # Combining info from the accounts
                for acc in node.account_tree_node_ids:
                    acc_com_data = acc_dict.get(acc.account_id.id, False)
                    if acc_com_data is not False:
                        update_com_data(com_data, acc.multiplier, acc_com_data)
                    if context['via_jasper_report_utils.rpt_name'] == 'General Ledger/Trial Balance':
                        acc_move_lines = context['via_financial_reports.gl_new_move_lines'].get(acc.account_id.id, [])
                        for ml in filter(lambda ml: ml['move_line_id'] > 0, acc_move_lines):
                            ml['move_line_debit'] = rounder(acc.multiplier * ml['move_line_debit'])
                            ml['move_line_credit'] = rounder(acc.multiplier * ml['move_line_credit'])
                            ml['acc_level'] = node.level
                            ml['line_type'] = None
                            move_lines.append(ml)

                total_bb_dr = 0.0
                total_bb_cr = 0.0
                total_dr = 0.0
                total_cr = 0.0
                for cid, cdata in com_data.iteritems():
                    total_bb_dr += cdata[0]
                    total_bb_cr += cdata[1]
                    total_dr += cdata[2]
                    total_cr += cdata[3]

                rt_move_lines_bb[node.id] = total_bb_dr - total_bb_cr
                rt_move_lines[node.id] = sorted(move_lines, key=lambda x: (x['move_line_com_id'],
                                                                           x['move_line_date'],
                                                                           x['move_line_name']))
                if len(move_lines):
                    rt_move_lines[node.id][-1]['line_type'] = 'last'
                if form.display_drcr:
                    rt_move_lines[node.id].append({
                        'move_line_id': 0,
                        'move_line_com_id': node.company_id.id,
                        'move_line_debit': total_dr,
                        'move_line_credit': total_cr,
                        'move_line_currency': None,
                        'acc_level': node.level,
                        'line_type': None,
                        'acc_move_count': len(move_lines),
                    })
                rt_move_lines[node.id].append({
                    'move_line_id': -2,
                    'move_line_com_id': node.company_id.id,
                    'move_line_debit': ((total_bb_dr - total_bb_cr)
                                        + (total_dr - total_cr)),
                    'move_line_credit': 0.0,
                    'move_line_currency': None,
                    'acc_level': node.level,
                    'line_type': None,
                    'acc_move_count': 0,
                })

            cats = NestedDictCat('node', [n.id for n in form.tree_id.node_ids],
                                 NestedDictCat('company', get_company_ids(form.tree_id.company_id)))
            datasource = NestedDict(cats,
                                    lambda: AccountTreeNodeValue(normalizer,
                                                                 rounder,
                                                                 is_zero))

            def attacher(keys):
                com_data = node_data[keys[0]].get(keys[1], None)
                if com_data is None:
                    return

                v = datasource.get_value(*keys)
                v.linearize_me = True
                v.add(None,
                      com_data[0], com_data[1], com_data[2], com_data[3])

            datasource.traverse(attacher)

            from via_reporting_tree.via_reporting_tree import tree
            tree.calculate(form.tree_id.root_node_id, datasource)

            nth = [0]
            type_cast = [('tree_order', 'INTEGER'), ('rtype', 'TEXT'),
                         ('node_id', 'INTEGER'),
                         ('cmp', 'TEXT'), ('com_id', 'INTEGER'),
                         ('beginning_balance', 'NUMERIC'), ('debit', 'NUMERIC'),
                         ('credit', 'NUMERIC'),
                         ('movement', 'NUMERIC'), ('ending_balance', 'NUMERIC')]
            if context.get('via_financial_reports.gl_new', False):
                type_cast.append(('active_com_id', 'INTEGER'))
            if context.get('via_financial_reports.cmp1_phase', False):
                cmp_text = '2' + (form.cmp1_label or '')
            else:
                cmp_text = '1' + (form.label or '')

            def linearize_node(node):
                nth[0] = nth[0] + 1
                linearized_node_common = [nth[0], node.get_rtype(context=context),
                                          node.id]
                if context['via_jasper_report_utils.rpt_name'] == 'General Ledger/Trial Balance':
                    for ml in rt_move_lines[node.id]:
                        nth[0] = nth[0] + 1
                        ml['tree_order'] = nth[0]
                        ml['cmp'] = cmp_text

                com_data = datasource.get_view(node.id)

                linearized_node = []

                beginning_balance_entry = [None]
                def process_leaf(keys):
                    value = com_data.get_value(*keys)
                    if not value.linearize_me and not value.node.title_line:
                        return
                    linearized_com = linearized_node_common[:]
                    com_id = keys[0]
                    if context['via_jasper_report_utils.rpt_name'] == 'General Ledger/Trial Balance':
                        if beginning_balance_entry[0] is None:
                            linearized_com.extend([cmp_text, node.company_id.id,
                                                   value.bb,
                                                   value.dr, value.cr, value.mv,
                                                   value.eb,
                                                   node.company_id.id])
                            linearized_node.append(linearized_com)
                            beginning_balance_entry[0] = linearized_com
                        else:
                            beginning_balance_entry[0][5] += value.bb
                            beginning_balance_entry[0][6] += value.dr
                            beginning_balance_entry[0][7] += value.cr
                            beginning_balance_entry[0][8] += value.mv
                            beginning_balance_entry[0][9] += value.eb
                    else:
                        linearized_com.extend([cmp_text, com_id,
                                               value.bb,
                                               value.dr, value.cr, value.mv,
                                               value.eb])
                        linearized_node.append(linearized_com)
                com_data.traverse(process_leaf)
                return linearized_node

            linearized_tree = tree.linearize(form.tree_id.root_node_id, linearize_node)

            rounder = context.get('via_financial_reports.rounder', False)
            if rounder:
                def round_element(element):
                    for idx in (5, 6, 7, 8, 9):
                        element[idx] = rounder(element[idx])
                    return element
                linearized_tree = map(round_element, linearized_tree)

            return (type_cast, linearized_tree)
        else:
            rounder = context.get('via_financial_reports.rounder', False)
            if rounder:
                def round_element(element):
                    for idx in (3, 4, 5, 6, 7):
                        element[idx] = rounder(element[idx])
                    return element
                linearized_tree = map(round_element, linearized_tree)
            return list_to_pgTable(linearized_tree, 't', type_cast)

    def filter_accounts(self, node, display_account, is_zero,
                        whitelist=None, immune_accs=None):
        def _filter_accounts(node, display_account, is_zero,
                             whitelist, immune_accs, ancestors, do_not_display):
            children = node[self.IDX_CHILDREN][:]  # Will be mangled by subcall
            filtered_children = []
            node[self.IDX_CHILDREN] = filtered_children
            removed_children = []

            ancestors.append(node)
            remove_me = True
            for subtree in children:
                if _filter_accounts(subtree, display_account, is_zero,
                                    whitelist, immune_accs, ancestors,
                                    do_not_display):
                    filtered_children.append(subtree)
                    remove_me = False
                else:
                    removed_children.append(subtree)

            # Adjust ancestors' total
            for child in removed_children:
                for ancestor in ancestors:
                    self.sub_idx_totals(ancestor[self.IDX_TOTAL],
                                        child[self.IDX_TOTAL])
            del ancestors[-1]

            # The return value is True to cancel node removal
            def check_removal(display_account, node, is_zero, whitelist, immune_accs):
                if immune_accs is not None and node[self.IDX_ACCOUNT] in immune_accs:
                    return True

                if display_account == 'bal_movement':
                    res1 = (node[self.IDX_MOVE_COUNT] != 0)
                elif display_account == 'bal_solde':
                    res1 = not is_zero(self.read_total(node[self.IDX_TOTAL][node[self.IDX_COMPANY]], 'mv'))
                else:
                    res1 = True

                if whitelist is not None:
                    res2 = node[self.IDX_ACCOUNT] in whitelist
                else:
                    res2 = True

                return res1 and res2
            if remove_me:
                return check_removal(display_account, node, is_zero, whitelist, immune_accs)
            else:
                if not check_removal(display_account, node, is_zero, whitelist, immune_accs):
                    do_not_display.add(id(node))
                return True
        do_not_display = set()
        if _filter_accounts(node, display_account, is_zero,
                            whitelist, immune_accs, [], do_not_display):
            return (node, do_not_display)
        else:
            return (None, do_not_display)

    def reset_report_type_total(self, report_type_total):
        for (cid, v) in report_type_total.iteritems():
            for k in v.iterkeys():
                report_type_total[cid][k] = self.create_total()

    def get_account_tree(self, pool, cr, uid, root_account_id, context=None):
        needed_account_ids = []
        acc_pool = pool.get('account.account')
        skeleton = self.get_tree_skeleton(acc_pool, cr, uid, root_account_id,
                                          needed_account_ids, context)
        data = self.get_account_data(pool, cr, uid, needed_account_ids, context)

        self.flesh_out_skeleton(skeleton, data)

        self.calculate_account_tree(skeleton, context=context)

        return (skeleton, data, needed_account_ids)

    def find_account(self, nodes, pl_account_ids, order_found=None):
        def _find_account(res, node, pl_account_ids):
            node_account = node[self.IDX_ACCOUNT]
            if node_account in pl_account_ids:
                res[node_account] = node
                if order_found is not None:
                    order_found.append((node_account, node[self.IDX_COMPANY]))
                pl_account_ids.remove(node[self.IDX_ACCOUNT])
            if len(pl_account_ids) == 0:
                return
            for acc in node[self.IDX_CHILDREN]:
                _find_account(res, acc, pl_account_ids)
        res = dict.fromkeys(pl_account_ids, None)
        accounts_to_search = set(pl_account_ids)
        for node in nodes:
            _find_account(res, node, accounts_to_search)
        return res

    def get_com_head_accs(self, pool, cr, uid, company_ids, context=None):
        com_head_accs = {}
        coms = pool.get('res.company').browse(cr, uid, company_ids,
                                              context=context)
        for com in coms:
            com_head_accs[com.id] = {
                self.ASSET_ACC: com.asset_head_account or None,
                self.LIABILITY_ACC: com.liability_head_account or None,
                self.INCOME_ACC: com.income_head_account or None,
                self.EXPENSE_ACC: com.expense_head_account or None,
            }
        return com_head_accs

    def get_account_trees(self, pool, cr, uid, ids, context=None):
        skels = []
        needed_account_ids = []
        acc_pool = pool.get('account.account')

        # Get skeletons
        for acc_id in ids:
            skel = self.get_tree_skeleton(acc_pool, cr, uid, acc_id,
                                          needed_account_ids, context)
            skels.append(skel)

        # Get all data at once
        data = self.get_account_data(pool, cr, uid, needed_account_ids, context)

        # Flesh out & calculate all skeletons
        for skel in skels:
            self.flesh_out_skeleton(skel, data)
            self.calculate_account_tree(skel, context=context)
        return (skels, data, needed_account_ids)

    def get_profit_loss_tree(self, pool, cr, uid, root_account_id,
                             income_head_acc_id, expense_head_acc_id,
                             context=None):
        '''Only consider the head accounts whose type is either "income"
           or "expense"'''
        (trees, data, unused) = self.get_account_trees(pool, cr, uid,
                                                       [income_head_acc_id,
                                                        expense_head_acc_id],
                                                       context)

        profit_loss = {}
        for cid in trees[0][self.IDX_TOTAL].iterkeys():
            profit_loss[cid] = self.create_total()
            total_income = trees[0][self.IDX_TOTAL][cid]
            total_expense = trees[1][self.IDX_TOTAL][cid]
            income_abs_bal = abs(self.read_total(total_income, 'mv'))
            expense_abs_bal = abs(self.read_total(total_expense, 'mv'))
            income_abs_bb = abs(self.read_total(total_income, 'bb'))
            expense_abs_bb = abs(self.read_total(total_expense, 'bb'))
            self.update_idx_total(profit_loss[cid],
                                  expense_abs_bal, income_abs_bal,
                                  expense_abs_bb, income_abs_bb, True)

        mv_profit_loss_type = {}
        for cid in trees[0][self.IDX_TOTAL].iterkeys():
            if self.read_total(profit_loss[cid], 'mv') <= 0.0:
                mv_profit_loss_type[cid] = 'profit'
            else:
                mv_profit_loss_type[cid] = 'loss'

        eb_profit_loss_type = {}
        for cid in trees[0][self.IDX_TOTAL].iterkeys():
            if self.read_total(profit_loss[cid], 'eb') <= 0.0:
                eb_profit_loss_type[cid] = 'profit'
            else:
                eb_profit_loss_type[cid] = 'loss'

        return ((mv_profit_loss_type, eb_profit_loss_type),
                profit_loss, trees, data)

    @staticmethod
    def get_root_account_ids(pool, cr, uid, company_ids, context=None):
        root_account_ids = dict.fromkeys(company_ids, None)
        acc_pool = pool.get('account.account')
        for cid in company_ids:
            acc_ids = acc_pool.search(cr, uid, [('parent_id', '=', False),
                                                ('company_id', '=', cid)],
                                      context=context)
            if len(acc_ids) == 1:
                acc_id = acc_ids[0]
            else:
                import logging
                logger = logging.getLogger('via.financial.reports')
                com = pool.get('res.company').browse(cr, uid, cid,
                                                     context=context)
                if len(acc_ids) == 0:
                    logger.warning("Company '%s' has no root account"
                                   % com.name)
                    continue
                else:
                    acc_id = acc_ids[0]
                    acc = acc_pool.browse(cr, uid, acc_id, context=context)
                    logger.warning("Company '%s' has multiple root accounts,"
                                   " account '%s' is regarded as the root"
                                   " account" % (com.name, acc.name))
            root_account_ids[cid] = acc_id
        return root_account_ids

    def check_com_head_accs_completeness(self, com_head_accs):
        missing_head_accs = {}
        for (cid, head_accs) in com_head_accs.iteritems():
            for (acc_type, acc) in head_accs.iteritems():
                if acc is None:
                    missing_head_accs.setdefault(cid, []).append(acc_type)
        return missing_head_accs

    def create_crosstab_line_node(self, line_text, acc_id, cid, acc_type, total, report_type):
        return self.create_tree_node(acc_id=acc_id,
                                     level=-1,
                                     total_text=line_text,
                                     company_id=cid,
                                     acc_type=acc_type,
                                     report_type=report_type,
                                     total=total,
                                     force_multicompany=True)

    def report_profit_loss(self, pool, cr, uid, root_account_id, context=None):
        if context is None:
            context = {}

        # Ensure all companies have their income and expense head accounts set
        acc_pool = pool.get('account.account')
        root_account = acc_pool.browse(cr, uid, root_account_id, context=context)
        company_ids = get_company_ids(root_account.company_id)
        com_head_accs = self.get_com_head_accs(pool, cr, uid, company_ids,
                                               context)
        missing_head_accs = self.check_com_head_accs_completeness(com_head_accs)
        if len(missing_head_accs) != 0:
            return (None, missing_head_accs, None)

        (normalizer,
         rounder,
         is_zero) = get_currency_toolkit(cr, uid,
                                         root_account.company_id.currency_id,
                                         context)
        context['via_financial_reports.normalizer'] = normalizer
        context['via_financial_reports.rounder'] = rounder
        context['via_financial_reports.is_zero'] = is_zero

        try:
            ((mv_pl_type, eb_pl_type),
             pl,
             trees,
             unused) = self.get_profit_loss_tree(pool, cr, uid,
                                                 root_account_id,
                                                 com_head_accs[root_account.company_id.id][self.INCOME_ACC].id,
                                                 com_head_accs[root_account.company_id.id][self.EXPENSE_ACC].id,
                                                 context)
        except CompanyHierarchyError as che:
            return (None, None, che.account)

        linearized_tree = []

        # Filter out accounts
        do_not_display = []
        if ('via_financial_reports.form' in context
            and context['via_financial_reports.form'].display_account):
            display_account = context['via_financial_reports.form'].display_account
            for (i, tree) in enumerate(trees):
                (trees[i],
                 dont_display) = self.filter_accounts(tree, display_account, is_zero)
                do_not_display.append(dont_display)

        # Incomes
        tree_nr = [0]
        if trees[0] is not None:
            self.linearize_tree(trees[0], tree_nr, linearized_tree,
                                do_not_display=do_not_display[0],
                                context=context)
            tree_nr[0] += 1
        else:
            trees[0] = self.create_tree_node(company_ids=company_ids)
        # Total income line
        line_node = self.create_crosstab_line_node('Total Incomes',
                                                   root_account_id,
                                                   root_account.company_id.id,
                                                   root_account.type,
                                                   trees[0][self.IDX_TOTAL],
                                                   self.INCOME_ACC)
        self.linearize_tree(line_node, tree_nr, linearized_tree, context=context)

        # Total income checksum line
        if self.display_checksum:
            tree_nr[0] += 1
            gl_report_type_total = self.get_gl_report_type_total(pool, cr, uid,
                                                                 root_account.company_id.id,
                                                                 context)
            total_income_gl = self.report_type_total_to_idx_total(gl_report_type_total,
                                                                  [self.INCOME_ACC])
            line_node = self.create_crosstab_line_node('Checksumming Total Incomes',
                                                       root_account_id,
                                                       root_account.company_id.id,
                                                       root_account.type,
                                                       total_income_gl,
                                                       self.INCOME_ACC)
            self.linearize_tree(line_node, tree_nr, linearized_tree, context=context)

        separator_nr = tree_nr[0]

        # Expenses
        tree_nr[0] += 1
        if trees[1] is not None:
            self.linearize_tree(trees[1], tree_nr, linearized_tree,
                                do_not_display=do_not_display[1],
                                context=context)
            tree_nr[0] += 1
        else:
            trees[1] = self.create_tree_node(company_ids=company_ids)
        # Total expense line
        line_node = self.create_crosstab_line_node('Total Expenses',
                                                   root_account_id,
                                                   root_account.company_id.id,
                                                   root_account.type,
                                                   trees[1][self.IDX_TOTAL],
                                                   self.EXPENSE_ACC)
        self.linearize_tree(line_node, tree_nr, linearized_tree, context=context)
        # Total expense checksum line
        if self.display_checksum:
            tree_nr[0] += 1
            total_expense_gl = self.report_type_total_to_idx_total(gl_report_type_total,
                                                                   [self.EXPENSE_ACC])
            line_node = self.create_crosstab_line_node('Checksumming Total Expenses',
                                                       root_account_id,
                                                       root_account.company_id.id,
                                                       root_account.type,
                                                       total_expense_gl,
                                                       self.EXPENSE_ACC)
            self.linearize_tree(line_node, tree_nr, linearized_tree,
                                context=context)

        # Profit/Loss
        profit_loss = []
        for cid in pl.iterkeys():
            profit_loss.append([1, 'Profit / Loss',
                                mv_pl_type[cid], eb_pl_type[cid],
                                self.read_total(pl[cid], 'mv'),
                                self.read_total(pl[cid], 'eb'), cid])

        # Checksumming profit/loss
        if self.display_checksum:
            gl_profit_loss = self.get_gl_profit_loss(gl_report_type_total)
            for (cid,
                 ((csum_mv_pl_type,
                   csum_eb_pl_type), csum_pl)) in gl_profit_loss.iteritems():
                profit_loss.append([2, 'Checksumming Profit / Loss',
                                    csum_mv_pl_type, csum_eb_pl_type,
                                    self.read_total(csum_pl, 'mv'),
                                    self.read_total(csum_pl, 'eb'), cid])

        rounder = context.get('via_financial_reports.rounder', False)
        if rounder:
            def round_element(element):
                for idx in (4, 5):
                    element[idx] = rounder(element[idx])
                return element
            profit_loss = map(round_element, profit_loss)
        profit_loss_line = list_to_pgTable(profit_loss, 't',
                                           [('pl_order', 'INTEGER'),
                                            ('pl_text', 'TEXT'),
                                            ('mv_pl_type', 'TEXT'),
                                            ('eb_pl_type', 'TEXT'),
                                            ('mv_pl_amount', 'NUMERIC'),
                                            ('eb_pl_amount', 'NUMERIC'),
                                            ('company_id', 'INTEGER')])

        return (profit_loss_line, self.stringify_tree(linearized_tree, context),
                separator_nr)

    def report_type_total_to_idx_total(self, report_type_total, report_types):
        '''Return a dictionary whose key is company_id found in report_type_total
           and whose value is a dr-cr-bal list. The value of the dr-cr-bal list
           is obtained by summing the dr-cr-bal lists found in report_type_total
           belonging to the corresponding company. The specified report_types
           governs which dr-cr-bal lists found in report_type_total should be
           summed.'''
        total = dict((cid, self.create_total())
                     for cid in report_type_total.iterkeys())
        for (cid, v) in report_type_total.iteritems():
            for (k, t) in v.iteritems():
                if k in report_types:
                    self.update_idx_total(total[cid],
                                          self.read_total(t, 'dr'),
                                          self.read_total(t, 'cr'),
                                          self.read_total(t, 'bd'),
                                          self.read_total(t, 'bc'),
                                          self.read_total(t, 'lm'))
        return total

    def report_general_ledger(self, pool, cr, uid, root_account_id, context=None):
        if context is None:
            context = {}

        root_account = pool.get('account.account').browse(cr, uid,
                                                          root_account_id,
                                                          context=context)

        (normalizer,
         rounder,
         is_zero) = get_currency_toolkit(cr, uid,
                                         root_account.company_id.currency_id,
                                         context)
        context['via_financial_reports.normalizer'] = normalizer
        context['via_financial_reports.rounder'] = rounder
        context['via_financial_reports.is_zero'] = is_zero

        try:
            (tree,
             data,
             unused) = self.get_account_tree(pool, cr, uid, root_account_id,
                                             context)
        except CompanyHierarchyError as che:
            return (None, None, che.account)

        # Filter accounts
        new_tree = tree
        if ('via_financial_reports.form' in context
            and context['via_financial_reports.form'].display_account):
            display_account = context['via_financial_reports.form'].display_account
            whitelist = set(acc.id for acc in context['via_financial_reports.form'].account_ids)
            whitelist = None if len(whitelist) == 0 else whitelist
            (new_tree,
             do_not_display) = self.filter_accounts(tree, display_account, is_zero,
                                                    whitelist=whitelist)

        tree_nr = [0]
        linearized_tree = []
        if new_tree is not None:
            self.linearize_tree(new_tree, tree_nr, linearized_tree,
                                do_not_display=do_not_display, context=context)
            tree_nr[0] += 1
        else:
            company_ids = get_company_ids(root_account.company_id)
            new_tree = self.create_tree_node(company_ids=company_ids)
        # Total line
        line_node = self.create_crosstab_line_node('Total',
                                                   root_account_id,
                                                   root_account.company_id.id,
                                                   root_account.type,
                                                   new_tree[self.IDX_TOTAL],
                                                   root_account.user_type.report_type)
        self.linearize_tree(line_node, tree_nr, linearized_tree, context=context)
        # Checksum line
        if self.display_checksum:
            tree_nr[0] += 1
            root_account = pool.get('account.account').browse(cr, uid,
                                                              root_account_id,
                                                              context=context)
            gl_report_type_total = self.get_gl_report_type_total(pool, cr, uid,
                                                                 root_account.company_id.id,
                                                                 context)
            total = self.report_type_total_to_idx_total(gl_report_type_total,
                                                        [self.ASSET_ACC,
                                                         self.LIABILITY_ACC,
                                                         self.INCOME_ACC,
                                                         self.EXPENSE_ACC])
            line_node = self.create_crosstab_line_node('Checksumming Total',
                                                       root_account_id,
                                                       root_account.company_id.id,
                                                       root_account.type,
                                                       total,
                                                       root_account.user_type.report_type)
            self.linearize_tree(line_node, tree_nr, linearized_tree, context=context)

        return (None, self.stringify_tree(linearized_tree, context), None)

    def report_general_ledger_with_move(self, pool, cr, uid, root_account_id,
                                        context=None):

        if context is None:
            context = {}

        root_account = pool.get('account.account').browse(cr, uid,
                                                          root_account_id,
                                                          context=context)

        (normalizer,
         rounder,
         is_zero) = get_currency_toolkit(cr, uid,
                                         root_account.company_id.currency_id,
                                         context)
        context['via_financial_reports.normalizer'] = normalizer
        context['via_financial_reports.rounder'] = rounder
        context['via_financial_reports.is_zero'] = is_zero

        try:
            (tree,
             data,
             needed_account_ids) = self.get_account_tree(pool, cr, uid,
                                                         root_account_id,
                                                         context)
        except CompanyHierarchyError as che:
            return (None, None, che.account)

        move_lines = self.get_account_move_lines(pool, cr, uid, data.keys(),
                                                 needed_account_ids, context)

        # Filter accounts
        new_tree = tree
        if ('via_financial_reports.form' in context
            and context['via_financial_reports.form'].display_account):
            display_account = context['via_financial_reports.form'].display_account
            whitelist = set(acc.id for acc in context['via_financial_reports.form'].account_ids)
            whitelist = None if len(whitelist) == 0 else whitelist
            (new_tree,
             do_not_display) = self.filter_accounts(tree, display_account, is_zero,
                                                    whitelist=whitelist)

        tree_nr = [0]
        linearized_tree = []
        if new_tree is not None:
            self.linearize_tree(new_tree, tree_nr, linearized_tree,
                                move_lines=move_lines,
                                do_not_display=do_not_display,
                                context=context)
            tree_nr[0] += 1
        else:
            company_ids = get_company_ids(root_account.company_id)
            new_tree = self.create_tree_node(company_ids=company_ids)
        # Total line
        line_node = self.create_crosstab_line_node('Total',
                                                   root_account_id,
                                                   root_account.company_id.id,
                                                   root_account.type,
                                                   new_tree[self.IDX_TOTAL],
                                                   root_account.user_type.report_type)
        self.linearize_tree(line_node, tree_nr, linearized_tree, context=context)
        # Checksum line
        if self.display_checksum:
            tree_nr[0] += 1
            root_account = pool.get('account.account').browse(cr, uid,
                                                              root_account_id,
                                                              context=context)
            gl_report_type_total = self.get_gl_report_type_total(pool, cr, uid,
                                                                 root_account.company_id.id,
                                                                 context)
            total = self.report_type_total_to_idx_total(gl_report_type_total,
                                                        [self.ASSET_ACC,
                                                         self.LIABILITY_ACC,
                                                         self.INCOME_ACC,
                                                         self.EXPENSE_ACC])
            line_node = self.create_crosstab_line_node('Checksumming Total',
                                                       root_account_id,
                                                       root_account.company_id.id,
                                                       root_account.type,
                                                       total,
                                                       root_account.user_type.report_type)
            self.linearize_tree(line_node, tree_nr, linearized_tree, context=context)

        typer = [('tree_order', 'INTEGER'), ('move_line_id', 'INTEGER'),
                 ('debit', 'NUMERIC'), ('credit', 'NUMERIC'),
                 ('movement', 'NUMERIC')]
        if context.get('via_financial_reports.gl_new', False):
            typer.insert(2, ('move_line_com_id', 'INTEGER'))
            typer.append(('acc_level', 'INTEGER'))
            typer.append(('line_type', 'TEXT'))
            typer.append(('acc_move_count', 'INTEGER'))
            if context['via_jasper_report_utils.rpt_name'] == 'General Ledger/Trial Balance':
                typer.append(('cmp', 'TEXT'))

        # Move lines
        if (context.get('via_jasper_report_utils.rpt_name', False)
            == 'General Ledger/Trial Balance'):
                tree_table = self.stringify_tree(linearized_tree, context=context)
                rt_move_lines_bb = context['via_financial_reports.reporting_tree_move_lines_bb']
                rt_move_lines = context['via_financial_reports.reporting_tree_move_lines']
                def get_bb(k):
                    return rt_move_lines_bb[k]
                linearized_move_lines = self.linearize_move_lines(rt_move_lines, get_bb, context)
                move_line_table = list_to_pgTable(linearized_move_lines, 'm', typer)
        else:
                def get_bb(k):
                    if 'tree_node' in data[k]:
                        n = data[k]['tree_node']
                        com_id = n[self.IDX_COMPANY]
                        return self.read_total(n[self.IDX_TOTAL][com_id],
                                               'bb')
                    else:
                        return 0.0
                linearized_move_lines = self.linearize_move_lines(move_lines, get_bb, context)
                move_line_table = list_to_pgTable(linearized_move_lines, 'm', typer)
                tree_table = self.stringify_tree(linearized_tree, context=context)

        return (move_line_table,
                tree_table,
                None)

    def linearize_move_lines(self, move_lines, get_bb, context):
        linearized_move_lines = []
        for (k, v) in move_lines.iteritems():

            cummulative_bal = get_bb(k)

            for e in v:
                if 'tree_order' not in e:
                    continue
                bal = e['move_line_debit'] - e['move_line_credit']
                element = [e['tree_order'],
                           e['move_line_id'],
                           e['move_line_debit'],
                           e['move_line_credit'],
                           bal]
                if context.get('via_financial_reports.gl_new', False):
                    element.insert(2, e['move_line_com_id'])
                    if e['move_line_id'] > 0:
                        cummulative_bal = cummulative_bal + bal
                        element[-1] = cummulative_bal
                    element.append(e['acc_level'])
                    element.append(e['line_type'])
                    element.append(e['acc_move_count'])
                    if context['via_jasper_report_utils.rpt_name'] == 'General Ledger/Trial Balance':
                        element.append(e['cmp'])

                linearized_move_lines.append(element)

        rounder = context.get('via_financial_reports.rounder', False)
        _gl_new = context.get('via_financial_reports.gl_new', False)
        if rounder:
            if _gl_new:
                def round_element(element):
                    for idx in (3, 4, 5):
                        element[idx] = rounder(element[idx])
                    return element
            else:
                def round_element(element):
                    for idx in (2, 3, 4):
                        element[idx] = rounder(element[idx])
                    return element
            linearized_move_lines = map(round_element, linearized_move_lines)

        return linearized_move_lines

    def get_profit_loss_accounts(self, pool, cr, uid, company_ids, context=None):
        com_pl_accounts = dict.fromkeys(company_ids, None)
        for com in pool.get('res.company').browse(cr, uid, company_ids,
                                                  context=context):
            if com.reserve_and_surplus_account:
                com_pl_accounts[com.id] = com.reserve_and_surplus_account.id
        return com_pl_accounts

    def get_currency_gain_loss_accounts(self, pool, cr, uid, company_ids, context=None):
        com_xgl_accounts = dict.fromkeys(company_ids, None)
        for com in pool.get('res.company').browse(cr, uid, company_ids,
                                                  context=context):
            if com.exchange_gain_loss_account:
                com_xgl_accounts[com.id] = com.exchange_gain_loss_account.id
        return com_xgl_accounts

    def update_account_node(self, root_node, node, update,
                            update_ancestors_only=False):
        def _find_account_node(root_node, node, nodes_to_update):
            nodes_to_update.append(root_node)
            if root_node is node:
                return True
            for subtree in root_node[self.IDX_CHILDREN]:
                if _find_account_node(subtree, node, nodes_to_update):
                    return True
            del nodes_to_update[-1]
            return False

        nodes_to_update = []
        res = _find_account_node(root_node, node, nodes_to_update)
        if res is False:
            return False

        # We calculate from the bottom
        nodes_to_update.reverse()

        # We need to modify update for convenience
        update_mod = dict([cid, self.create_total()] for cid in update.iterkeys())
        for (cid, (dr, cr, bd, bc)) in update.iteritems():
            self.update_idx_total(update_mod[cid], dr, cr, bd, bc, None)

        def propagate_update(target_node, update, do_update=True):
            if target_node[self.IDX_TYPE] == self.CONS_ACC:
                cons_children_com_ids = set(n.company_id.id
                                            for n in target_node[self.IDX_CONSOL_CHILDREN])
                cons_delta = self.create_total()
                for cid in cons_children_com_ids:
                    if cid not in update:
                        continue
                    self.update_idx_total(cons_delta,
                                          self.read_total(update[cid], 'dr'),
                                          self.read_total(update[cid], 'cr'),
                                          self.read_total(update[cid], 'bd'),
                                          self.read_total(update[cid], 'bc'),
                                          None)

                cons_com_id = target_node[self.IDX_COMPANY]
                cons_total = update.setdefault(cons_com_id, self.create_total())
                self.update_idx_total(cons_total,
                                      self.read_total(cons_delta, 'dr'),
                                      self.read_total(cons_delta, 'cr'),
                                      self.read_total(cons_delta, 'bd'),
                                      self.read_total(cons_delta, 'bc'),
                                      None)

            if do_update:
                for (cid, cid_total) in update.iteritems():
                    self.update_idx_total(target_node[self.IDX_TOTAL][cid],
                                          self.read_total(cid_total, 'dr'),
                                          self.read_total(cid_total, 'cr'),
                                          self.read_total(cid_total, 'bd'),
                                          self.read_total(cid_total, 'bc'),
                                          None)

        target_node = nodes_to_update.pop(0)
        propagate_update(target_node, update_mod, not update_ancestors_only)
        for n in nodes_to_update:
            propagate_update(n, update_mod)

        return res

    def report_balance_sheet(self, pool, cr, uid, root_account_id, context=None):
        if context is None:
            context = {}

        # Ensure all companies have their income and expense head accounts set
        acc_pool = pool.get('account.account')
        root_account = acc_pool.browse(cr, uid, root_account_id, context=context)
        company_ids = get_company_ids(root_account.company_id)
        com_head_accs = self.get_com_head_accs(pool, cr, uid, company_ids,
                                               context)
        missing_head_accs = self.check_com_head_accs_completeness(com_head_accs)
        if len(missing_head_accs) != 0:
            return ((None, 3, None, None), missing_head_accs, None)

        (normalizer,
         rounder,
         is_zero) = get_currency_toolkit(cr, uid,
                                         root_account.company_id.currency_id,
                                         context)
        context['via_financial_reports.normalizer'] = normalizer
        context['via_financial_reports.rounder'] = rounder
        context['via_financial_reports.is_zero'] = is_zero

        try:
            (trees,
             data,
             unused) = self.get_account_trees(pool, cr, uid,
                                              [com_head_accs[root_account.company_id.id][self.ASSET_ACC].id,
                                               com_head_accs[root_account.company_id.id][self.LIABILITY_ACC].id],
                                              context)
        except CompanyHierarchyError as che:
            return ((None, 4, None, None), che.account, None)

        # Get each company profit/loss accounts
        com_pl_accounts = self.get_profit_loss_accounts(pool, cr, uid,
                                                        company_ids, context)
        com_missing_pl_accounts = map(lambda (k, v): k,
                                      filter(lambda (k, v): v is None,
                                             com_pl_accounts.iteritems()))
        if len(com_missing_pl_accounts) != 0:
            return ((None, 1, None, None), com_missing_pl_accounts, None)

        # Find each company profit/loss account in the asset/liability trees
        pl_account_nodes = self.find_account(trees,
                                             list(com_pl_accounts.itervalues()))
        com_missing_pl_nodes = map(lambda (a, v): a,
                                   filter(lambda (a, v): v is None,
                                          pl_account_nodes.iteritems()))
        if len(com_missing_pl_nodes) != 0:
            return ((None, 2, None, None), com_missing_pl_nodes, None)

        # Calculate the profit/loss of each company and record it in
        # the company's profit/loss account
        root_com_pl_node = None
        csum_pl_node_tree = {}

        context['via_financial_reports.calculating_retained_earnings'] = True
        try:
            (unused,
             _pl,
             unused,
             unused) = self.get_profit_loss_tree(pool, cr, uid, root_account.id,
                                                 com_head_accs[root_account.company_id.id][self.INCOME_ACC].id,
                                                 com_head_accs[root_account.company_id.id][self.EXPENSE_ACC].id,
                                                 context)
        except CompanyHierarchyError as che:
            return ((None, 4, None, None), che.account, None)
        finally:
            del context['via_financial_reports.calculating_retained_earnings']

        for cid in company_ids:
            com_profit_loss_bal = self.read_total(_pl[cid], 'mv')
            com_profit_loss_bb = self.read_total(_pl[cid], 'bb')
            if com_profit_loss_bal <= 0.0:
                # Make profit
                profit = abs(com_profit_loss_bal)
                update_data_arg = {'new_cr': profit}
                if com_profit_loss_bb <= 0.0:
                    profit_bb = abs(com_profit_loss_bb)
                    update_data = (0.0, profit, 0.0, profit_bb)
                    update_data_arg['new_bc'] = profit_bb
                else:
                    loss_bb = abs(com_profit_loss_bb)
                    update_data = (0.0, profit, loss_bb, 0.0)
                    update_data_arg['new_bd'] = loss_bb
                pl_account_node = pl_account_nodes[com_pl_accounts[cid]]

                if cid == root_account.company_id.id:
                    root_account_pl_type = 'profit'
                    root_com_pl_node = pl_account_node

                for (i, tree) in enumerate(trees):
                    if self.update_account_node(tree, pl_account_node,
                                                {cid: update_data}):
                        csum_pl_node_tree[pl_account_node[self.IDX_COMPANY]] = i
                        break
            else:
                # Make loss
                loss = com_profit_loss_bal
                update_data_arg = {'new_dr': loss}
                if com_profit_loss_bb <= 0.0:
                    profit_bb = abs(com_profit_loss_bb)
                    update_data = (loss, 0.0, 0.0, profit_bb)
                    update_data_arg['new_bc'] = profit_bb
                else:
                    loss_bb = abs(com_profit_loss_bb)
                    update_data = (loss, 0.0, loss_bb, 0.0)
                    update_data_arg['new_bd'] = loss_bb
                pl_account_node = pl_account_nodes[com_pl_accounts[cid]]

                if cid == root_account.company_id.id:
                    root_account_pl_type = 'loss'
                    root_com_pl_node = pl_account_node

                for (i, tree) in enumerate(trees):
                    if self.update_account_node(tree, pl_account_node,
                                                {cid: update_data}):
                        csum_pl_node_tree[pl_account_node[self.IDX_COMPANY]] = i
                        break

        # Currency gain/loss
        if len(company_ids) > 1:
            # When there are more than one company, there is no guaranteed way to
            # see whether all companies have the same currency. Therefore, when
            # there are more than one company, assume multi-currency and demand
            # currency gain/loss account to be specified.
            com_xgl_accounts = self.get_currency_gain_loss_accounts(pool, cr, uid,
                                                                    company_ids,
                                                                    context)
            com_missing_xgl_accounts = map(lambda (k, v): k,
                                           filter(lambda (k, v): v is None,
                                                  com_xgl_accounts.iteritems()))
            if len(com_missing_xgl_accounts) != 0:
                return ((None, 5, None, None), com_missing_xgl_accounts, None)

            # Find each company currency gain/loss account in the asset/liability trees
            order_found = []
            xgl_account_nodes = self.find_account(trees,
                                                  list(com_xgl_accounts.itervalues()),
                                                  order_found=order_found)
            com_missing_xgl_nodes = map(lambda (a, v): a,
                                        filter(lambda (a, v): v is None,
                                               xgl_account_nodes.iteritems()))
            if len(com_missing_xgl_nodes) != 0:
                return ((None, 6, None, None), com_missing_xgl_nodes, None)

            order_found.reverse()
            for (acc_id, cid) in order_found:
                # Calculate currency gain/loss of this company
                currency_gain_loss = (0.0, 0.0, 0.0, 0.0)
                total_asset = trees[0][self.IDX_TOTAL]
                total_liability = trees[1][self.IDX_TOTAL]
                gain_loss = (self.read_total(total_asset[cid], 'eb')
                             + self.read_total(total_liability[cid], 'eb'))
                if gain_loss < 0.0:
                    loss = abs(gain_loss)
                    currency_gain_loss = (loss, 0.0, 0.0, 0.0)
                elif gain_loss > 0.0:
                    gain = abs(gain_loss)
                    currency_gain_loss = (0.0, gain, 0.0, 0.0)
                else:
                    continue

                # Update the currency gain/loss accounts
                xgl_account_node = xgl_account_nodes[acc_id]
                for (i, tree) in enumerate(trees):
                    if self.update_account_node(tree, xgl_account_node,
                                                {cid: currency_gain_loss}):
                        break

        # Filter accounts
        do_not_display = []
        if ('via_financial_reports.form' in context
            and context['via_financial_reports.form'].display_account):
            display_account = context['via_financial_reports.form'].display_account
            for (i, tree) in enumerate(trees):
                # Retained earnings account shall never be filtered out
                immune_accs = set([root_com_pl_node[self.IDX_ACCOUNT]])
                (trees[i],
                 dont_display) = self.filter_accounts(tree, display_account, is_zero,
                                                      immune_accs=immune_accs)
                do_not_display.append(dont_display)

        # Calculate GL checksums
        if self.display_checksum:
            gl_report_type_total = self.get_gl_report_type_total(pool, cr, uid,
                                                                 root_account.company_id.id,
                                                                 context)
            gl_profit_loss = self.get_gl_profit_loss(gl_report_type_total)
            gl_asset_total = self.report_type_total_to_idx_total(gl_report_type_total,
                                                                 [self.ASSET_ACC])
            gl_liability_total = self.report_type_total_to_idx_total(gl_report_type_total,
                                                                     [self.LIABILITY_ACC])
            for (cid, tree_idx) in csum_pl_node_tree.iteritems():
                if tree_idx == 0:
                    gl_total = gl_asset_total[cid]
                else:
                    gl_total = gl_liability_total[cid]

                mv = self.read_total(gl_profit_loss[cid][1], 'mv')
                bb = self.read_total(gl_profit_loss[cid][1], 'bb')
                dr = cr = bd = bc = 0.0
                if mv <= 0.0:
                    cr = abs(mv)
                else:
                    dr = abs(mv)
                if bb <= 0.0:
                    bc = abs(bb)
                else:
                    bd = abs(bb)
                self.update_idx_total(gl_total, dr, cr, bd, bc, None)

        # Linearize the trees
        linearized_tree = []

        ## Assets
        tree_nr = [0]
        if trees[0] is not None:
            self.linearize_tree(trees[0], tree_nr, linearized_tree,
                                do_not_display=do_not_display[0],
                                context=context)
            tree_nr[0] += 1
        else:
            trees[0] = self.create_tree_node(company_ids=company_ids)
        total_asset_tree_nr = tree_nr[0]

        ## Liabilities
        tree_nr[0] = 0
        if trees[1] is not None:
            self.linearize_tree(trees[1], tree_nr, linearized_tree,
                                do_not_display=do_not_display[1],
                                context=context)
            tree_nr[0] += 1
        else:
            trees[1] = self.create_tree_node(company_ids=company_ids)
        total_liability_tree_nr = tree_nr[0]

        ## Total lines
        tree_nr[0] = total_asset_tree_nr
        line_node = self.create_crosstab_line_node('Total Assets',
                                                   root_account_id,
                                                   root_account.company_id.id,
                                                   root_account.type,
                                                   trees[0][self.IDX_TOTAL],
                                                   self.ASSET_ACC)
        self.linearize_tree(line_node, tree_nr, linearized_tree, context=context)
        tree_nr[0] = total_liability_tree_nr
        line_node = self.create_crosstab_line_node('Total Liabilities',
                                                   root_account_id,
                                                   root_account.company_id.id,
                                                   root_account.type,
                                                   trees[1][self.IDX_TOTAL],
                                                   self.LIABILITY_ACC)
        self.linearize_tree(line_node, tree_nr, linearized_tree, context=context)

        ## Checksumming total lines
        if self.display_checksum:
            total_asset_tree_nr += 1
            tree_nr[0] = total_asset_tree_nr
            line_node = self.create_crosstab_line_node('Checksumming Total Assets',
                                                       root_account_id,
                                                       root_account.company_id.id,
                                                       root_account.type,
                                                       gl_asset_total,
                                                       self.ASSET_ACC)
            self.linearize_tree(line_node, tree_nr, linearized_tree,
                                context=context)

            total_liability_tree_nr += 1
            tree_nr[0] = total_liability_tree_nr
            line_node = self.create_crosstab_line_node('Checksumming Total Liabilities',
                                                       root_account_id,
                                                       root_account.company_id.id,
                                                       root_account.type,
                                                       gl_liability_total,
                                                       self.LIABILITY_ACC)
            self.linearize_tree(line_node, tree_nr, linearized_tree,
                                context=context)

        return ((root_account_pl_type,
                 com_pl_accounts[root_account.company_id.id],
                 'asset' if total_liability_tree_nr > total_asset_tree_nr else 'liability',
                 total_asset_tree_nr if total_liability_tree_nr > total_asset_tree_nr else total_liability_tree_nr),
                self.stringify_tree(linearized_tree, context),
                None)
