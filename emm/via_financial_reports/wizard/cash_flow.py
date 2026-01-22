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
    from via_reporting_tree.specialization_link_account import register_node_tags
    from via_reporting_tree.specialization_link_account import register_tags
    import pooler
    from via_reporting_utility.pgsql import create_composite_type
    from via_reporting_utility.pgsql import create_aggregator
    from via_reporting_utility.pgsql import create_plpgsql_proc
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import osv, fields
    from openerp.tools.translate import _
    from openerp.addons.via_jasper_report_utils_account.framework import register_report_wizard  # wizard
    from openerp.addons.via_reporting_tree.specialization_link_account import register_node_tags
    from openerp.addons.via_reporting_tree.specialization_link_account import register_tags
    from openerp import pooler
    from openerp.addons.via_reporting_utility.pgsql import create_composite_type
    from openerp.addons.via_reporting_utility.pgsql import create_aggregator
    from openerp.addons.via_reporting_utility.pgsql import create_plpgsql_proc

import _financial_reports
from copy import deepcopy


RPT_NAME = 'Cash Flow'

register_node_tags('Cash Flow', [
    ('beginning', 'Beginning Balance'),
    ('ending', 'Ending Balance'),
])


register_tags('Cash Flow', [
    ('beginning', 'Beginning Balance'),
    ('ending', 'Ending Balance'),
    ('income', 'Income'),
    ('expense', 'Expense'),
])


_CASH_FLOW_ITEMS_DEF = '''
DECLARE
    acc_id RECORD;

    to_be_processed_entries VCF_TUPLE[];

    next_to_be_processed_entries VCF_TUPLE[];

    already_traversed_items INTEGER[];

    result_items VCF_TUPLE[];

    cash_in_out_items NO SCROLL CURSOR(date_start_ DATE,
                                       date_end_ DATE,
                                       company_ids_ INTEGER[],
                                       account_ids_ INTEGER[])
        FOR
         SELECT
          aml.id,
          aml.move_id,
          CASE WHEN aml.debit > aml.credit
           THEN 1::INTEGER
           ELSE 2::INTEGER
          END AS type,
          aml.date AS date,
          aml.account_id AS bank_acc_id
         FROM account_move_line aml
          INNER JOIN account_move am
           ON am.id = aml.move_id
          INNER JOIN account_account a
           ON aml.account_id = a.id
          INNER JOIN UNNEST(company_ids_) selected_company_id
           ON a.company_id = selected_company_id
          INNER JOIN UNNEST(account_ids_) selected_account_id
           ON a.id = selected_account_id
         WHERE
          aml.state = 'valid'
          AND am.state = 'posted'
          AND NOT ((aml.debit IS NULL AND aml.credit IS NULL)
                   OR (aml.debit = 0 AND aml.credit = 0))
          AND aml.date BETWEEN date_start_ AND date_end_;

    border_items NO SCROLL CURSOR(date_end_ DATE,
                                  company_ids_ INTEGER[],
                                  to_be_processed_entries_ VCF_TUPLE[],
                                  already_traversed_items_ INTEGER[])
        FOR
         SELECT
          other_items.date AS date,
          other_items.move_id AS curr_move_id,
          other_items.id AS curr_id,
          reconciled_items.move_id AS next_move_id,
          reconciled_items.id AS next_id,
          other_items.type AS type,
          other_items.bank_acc_id AS bank_acc_id
         FROM
          (
           SELECT
            aml.id, aml.move_id, entries.date, entries.type, entries.bank_acc_id,
            aml.reconcile_id, aml.reconcile_partial_id
           FROM account_move_line aml
            INNER JOIN UNNEST(to_be_processed_entries_) entries
             ON entries.id = aml.move_id
           WHERE
            NOT ((aml.debit IS NULL AND aml.credit IS NULL)
                 OR (aml.debit = 0 AND aml.credit = 0))
            AND NOT EXISTS (SELECT *
                            FROM UNNEST(already_traversed_items_) item_id
                            WHERE item_id = aml.id)
          ) other_items
          LEFT JOIN (
           SELECT aml.*
           FROM account_move_line aml
            INNER JOIN account_move am
             ON am.id = aml.move_id
            INNER JOIN UNNEST(company_ids_) selected_company_ids
             ON aml.company_id = selected_company_ids
           WHERE
            aml.state = 'valid'
            AND am.state = 'posted'
            AND NOT ((aml.debit IS NULL AND aml.credit IS NULL)
                      OR (aml.debit = 0 AND aml.credit = 0))
            AND aml.date <= date_end_
            AND NOT EXISTS (SELECT *
                            FROM UNNEST(to_be_processed_entries_) entries
                            WHERE entries.id = aml.move_id)
          ) reconciled_items
           ON (COALESCE(reconciled_items.reconcile_id,
                       reconciled_items.reconcile_partial_id)
               = COALESCE(other_items.reconcile_id,
                          other_items.reconcile_partial_id));
BEGIN
    --- Function for Cash Flow Realisation report
    result_items := ARRAY[]::VCF_TUPLE[];

    FOR acc_id IN (SELECT id FROM UNNEST(account_ids) id) LOOP
        to_be_processed_entries := ARRAY[]::VCF_TUPLE[];

        already_traversed_items := ARRAY[]::INTEGER[];

        FOR rec IN cash_in_out_items(date_start, date_end,
                                     company_ids, ARRAY[acc_id.id]) LOOP
            already_traversed_items := ARRAY_APPEND(already_traversed_items,
                                                    rec.id);
            to_be_processed_entries := ARRAY_APPEND(to_be_processed_entries,
                                                    (rec.move_id, rec.date, rec.type, rec.bank_acc_id)::VCF_TUPLE);
        END LOOP;

        WHILE ARRAY_LENGTH(to_be_processed_entries, 1) IS NOT NULL LOOP

            next_to_be_processed_entries := ARRAY[]::VCF_TUPLE[];

            FOR rec IN border_items(date_end, company_ids,
                                    to_be_processed_entries,
                                    already_traversed_items) LOOP
                already_traversed_items := ARRAY_APPEND(already_traversed_items,
                                                        rec.curr_id);
                result_items := ARRAY_APPEND(result_items,
                                             (rec.curr_id, rec.date, rec.type, rec.bank_acc_id)::VCF_TUPLE);

                IF rec.next_id IS NOT NULL THEN
                    already_traversed_items := ARRAY_APPEND(already_traversed_items,
                                                        rec.next_id);
                    result_items := ARRAY_APPEND(result_items,
                                                        (rec.next_id, rec.date, rec.type, rec.bank_acc_id)::VCF_TUPLE);
                    next_to_be_processed_entries := ARRAY_APPEND(
                        next_to_be_processed_entries,
                        (rec.next_move_id, rec.date, rec.type, rec.bank_acc_id)::VCF_TUPLE
                    );
                END IF;
            END LOOP;

            to_be_processed_entries := next_to_be_processed_entries;

        END LOOP;

    END LOOP; -- For each liquidity account_id

    RETURN QUERY (SELECT DISTINCT
                   (CASE
                     WHEN type = 1
                      THEN 'income'
                     ELSE 'expense'
                    END)::VARCHAR AS type,
                   id,
                   date,
                   bank_acc_id
                  FROM UNNEST(result_items) result_item
                  ORDER BY type, date, id);
END
'''


class via_jasper_report(osv.osv_memory):
    def _auto_init(self, cr, context=None):
        super(via_jasper_report, self)._auto_init(cr, context=context)
        create_composite_type(cr, 'vcf_tuple',
                              [('id', 'BIGINT'),
                               ('date', 'DATE'),
                               ('type', 'INT'),
                               ('bank_acc_id', 'BIGINT')])
        create_plpgsql_proc(cr, 'cash_flow_items',
                            [('IN', 'date_start', 'DATE'),
                             ('IN', 'date_end', 'DATE'),
                             ('IN', 'company_ids', 'INTEGER[]'),
                             ('IN', 'account_ids', 'INTEGER[]')],
                            'TABLE(type_ CHARACTER VARYING, id_ BIGINT, date_ DATE, bank_acc_id_ BIGINT)',
                            _CASH_FLOW_ITEMS_DEF)

    _inherit = 'via.jasper.report'
    _description = 'Cash Flow'

    _columns = {
    }

    # DO NOT use the following default dictionary. Use the one in class wizard.
    # The following is presented for your information regarding the system-
    # wide defaults.
    _defaults = {
    }

via_jasper_report()


class wizard(_financial_reports.wizard):

    @staticmethod
    def default_fiscalyear_id(cr, uid, context=None):
        user_pool = pooler.get_pool(cr.dbname).get('res.users')
        com_id = user_pool.browse(cr, uid, uid, context=context).company_id.id

        form_pool = pooler.get_pool(cr.dbname).get('via.jasper.report')
        return form_pool.default_fiscalyear_id(cr, uid,
                                               company_id=com_id,
                                               context=context)

    @staticmethod
    def default_from_dt(cr, uid, context=None):
        fiscalyear_id = wizard.default_fiscalyear_id(cr, uid, context=context)
        return _financial_reports.wizard.default_from_dt(cr, uid, [],
                                                         fiscalyear_id,
                                                         context=context)

    @staticmethod
    def default_to_dt(cr, uid, context=None):
        fiscalyear_id = wizard.default_fiscalyear_id(cr, uid, context=context)
        return _financial_reports.wizard.default_to_dt(cr, uid, [],
                                                       fiscalyear_id,
                                                       context=context)

    def onchange_company_id(cr, uid, ids, com_id, context=None):
        return {
            'value': {
                'from_dt': wizard.default_from_dt(cr, uid, context=context),
                'to_dt': wizard.default_to_dt(cr, uid, context=context),

                'reporting_tree_id': False,
            },
        }

    _onchange = {
        'company_id': (onchange_company_id, 'company_id', 'context'),
    }

    _visibility = [
        'company_id',
        'reporting_tree_id',
        'use_indentation',
        'no_zero',
        ['from_dt', 'to_dt'],
    ]

    # The values in the dictionary below must be callables with signature:
    #     lambda self, cr, uid, context
    _defaults = deepcopy(_financial_reports.wizard._defaults)
    _defaults.update({
        'use_indentation': lambda self, cr, uid, context: True,
        'from_dt': lambda self, cr, uid, context: wizard.default_from_dt(cr, uid, context),
        'to_dt': lambda self, cr, uid, context: wizard.default_to_dt(cr, uid, context),
    })

    _label = deepcopy(_financial_reports.wizard._label)
    _label.update({
        'no_zero': 'Exclude node with 0 balance',
    })

    _attrs = deepcopy(_financial_reports.wizard._attrs)
    del _attrs['from_dt']
    del _attrs['to_dt']

    _required = deepcopy(_financial_reports.wizard._required)
    _required.extend([
        'from_dt',
        'to_dt',
    ])

    _domain = deepcopy(_financial_reports.wizard._domain)
    _domain.update({
        'reporting_tree_id': "[('company_id','=',company_id),('tree_type_name','=','Cash Flow')]",
    })

    def _populate_form_acc_ids(self, cr, uid, form, context=None):
        acc_pool = self.pool.get('account.account')
        acc_ids = acc_pool.search(cr, uid, [('type', '=', 'liquidity')], context=context)
        form.write({
            'acc_ids': [(6, 0, acc_ids)],
        }, context=context)
        return form.get_form(context=context)

    def print_report(self, cr, uid, form, context=None):
        form = self._populate_form_company_ids(cr, uid, form, context=context)
        form = self._populate_form_acc_ids(cr, uid, form, context=context)

register_report_wizard(RPT_NAME, wizard)
