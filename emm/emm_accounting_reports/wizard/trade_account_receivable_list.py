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

from osv import orm, fields
from tools.translate import _
from via_jasper_report_utils.framework import register_report_wizard, wizard


RPT_NAME = 'Trade Account Receivable List'

report_sql = """
WITH receivable_accounts AS
    (SELECT id
     FROM account_account
     WHERE type = 'receivable'),
       selected_invoices AS
    (SELECT ai.id
     FROM account_invoice ai
     WHERE ai.state = 'open'
       AND ai.type IN ('out_invoice',
                       'out_refund') $P!{CUSTOMER_IDS}
       AND ai.company_id IN ($P!{COMPANY_IDS})
     UNION SELECT ai.id
     FROM account_invoice ai
     LEFT OUTER JOIN account_move_line aml ON (aml.move_id = ai.move_id
                                               AND (COALESCE(aml.reconcile_id, aml.reconcile_partial_id) IS NOT NULL)
                                               AND (aml.account_id IN
                                                      (SELECT id
                                                       FROM receivable_accounts)))
     LEFT OUTER JOIN account_move_line aml2 ON (aml.id != aml2.id
                                                AND(COALESCE(aml2.reconcile_id, aml2.reconcile_partial_id) = COALESCE(aml.reconcile_id, aml.reconcile_partial_id))
                                                AND (aml.account_id IN
                                                       (SELECT id
                                                        FROM receivable_accounts)))
     LEFT OUTER JOIN res_company rco ON (rco.id = ai.company_id)
     LEFT OUTER JOIN account_period ap ON (ap.company_id = rco.id)
     WHERE ai.state IN ('open',
                        'paid')
       AND ai.type IN ('out_invoice',
                       'out_refund')
       AND $P{TODAY} BETWEEN ap.date_start AND ap.date_stop
       AND (aml2.date BETWEEN ap.date_start AND ap.date_stop) $P!{CUSTOMER_IDS}
       AND ai.company_id IN ($P!{COMPANY_IDS}))
  SELECT area,
         cust_name,
         cust_ref,
         pers_in_charge,
         invoice_date,
         invoice_no,
         --untaxed_amount--

         CASE
             WHEN com_curr_id != inv_curr_id THEN ROUND(untaxed_amount /
                                                          (SELECT rate
                                                           FROM res_currency_rate
                                                           WHERE name <= invoice_date
                                                             AND res_currency_rate.currency_id = inv_curr_id
                                                           ORDER BY name DESC, create_date DESC LIMIT 1), 2)
             ELSE untaxed_amount
         END AS untaxed_amount,
         CASE
             WHEN com_curr_id != inv_curr_id THEN untaxed_amount
             ELSE NULL
         END AS untaxed_amount_currency,
         --tax_amount--

         CASE
             WHEN com_curr_id != inv_curr_id THEN ROUND(tax_amount /
                                                          (SELECT rate
                                                           FROM res_currency_rate
                                                           WHERE name <= invoice_date
                                                             AND res_currency_rate.currency_id = inv_curr_id
                                                           ORDER BY name DESC, create_date DESC LIMIT 1), 2)
             ELSE tax_amount
         END AS tax_amount,
         CASE
             WHEN com_curr_id != inv_curr_id THEN tax_amount
             ELSE NULL
         END AS tax_amount_currency,
         --invoice_amount--

         CASE
             WHEN (invoice_date NOT BETWEEN date_start AND date_stop) THEN invoice_amount
             ELSE 0.0
         END AS invoice_amount,
         CASE
             WHEN (invoice_date NOT BETWEEN date_start AND date_stop)
                  AND com_curr_id != inv_curr_id THEN invoice_amount_currency
             ELSE NULL
         END AS invoice_amount_currency,
         invoice_due_date,
         --amount_sales--

         CASE
             WHEN (invoice_date BETWEEN date_start AND date_stop) THEN invoice_amount
             ELSE 0.0
         END AS amount_sales,
         CASE
             WHEN (invoice_date BETWEEN date_start AND date_stop)
                  AND com_curr_id != inv_curr_id THEN invoice_amount_currency
             ELSE NULL
         END AS amount_sales_currency,
         --pay_date--

         pay_date,
         --pay_amount--

         CASE
             WHEN (1 != 0) THEN SUM(pay_amount)
             ELSE 0.0
         END AS pay_amount,
         CASE
             WHEN (pay_date BETWEEN date_start AND date_stop)
                  AND com_curr_id != pay_curr_id
                  AND SUM(pay_amount_currency) != 0.0 THEN ROUND((SUM(ABS(pay_amount_currency))/rate), 2)
             WHEN (pay_date BETWEEN date_start AND date_stop)
                  AND com_curr_id != pay_curr_id
                  AND SUM(pay_amount_currency) = 0.0 THEN ROUND(SUM(pay_amount) *
                                                                  (SELECT rate
                                                                   FROM res_currency_rate
                                                                   WHERE name <= pay_date
                                                                     AND res_currency_rate.currency_id = pay_curr_id
                                                                   ORDER BY name DESC, create_date DESC LIMIT 1), 2)
             ELSE NULL
         END AS pay_amount_currency,
         --balance--

         balance,
         CASE
             WHEN com_curr_id != inv_curr_id
                  AND balance_currency != 0 THEN balance_currency
             ELSE NULL
         END AS balance_currency,
         pass_due,
         --due_in_30--

         CASE
             WHEN (pass_due BETWEEN 1 AND 30) THEN balance
             ELSE 0.0
         END AS due_in_30,
         CASE
             WHEN (pass_due BETWEEN 1 AND 30)
                  AND com_curr_id != inv_curr_id
                  AND balance_currency != 0 THEN balance_currency
             ELSE NULL
         END AS due_in_30_currency,
         --due_in_60--

         CASE
             WHEN (pass_due BETWEEN 31 AND 60) THEN balance
             ELSE 0.0
         END AS due_in_60,
         CASE
             WHEN (pass_due BETWEEN 31 AND 60)
                  AND com_curr_id != inv_curr_id
                  AND balance_currency != 0 THEN balance_currency
             ELSE NULL
         END AS due_in_60_currency,
         --due_in_90--

         CASE
             WHEN (pass_due BETWEEN 61 AND 90) THEN balance
             ELSE 0.0
         END AS due_in_90,
         CASE
             WHEN (pass_due BETWEEN 61 AND 90)
                  AND com_curr_id != inv_curr_id
                  AND balance_currency != 0 THEN balance_currency
             ELSE NULL
         END AS due_in_90_currency,
         --less_1_month--

         CASE
             WHEN (pass_due BETWEEN -31 AND 0) THEN balance
             ELSE 0.0
         END AS less_1_month,
         CASE
             WHEN (pass_due BETWEEN -31 AND 0)
                  AND com_curr_id != inv_curr_id
                  AND balance_currency != 0 THEN balance_currency
             ELSE NULL
         END AS less_1_month_currency,
         --more_1_month--

         CASE
             WHEN (pass_due < -30) THEN balance
             ELSE 0.0
         END AS more_1_month,
         CASE
             WHEN (pass_due < -30)
                  AND com_curr_id != inv_curr_id
                  AND balance_currency != 0 THEN balance_currency
             ELSE NULL
         END AS more_1_month_currency,
         com_curr_symbol AS com_currency,
         inv_curr_symbol AS inv_currency,
         CASE
             WHEN pay_curr_symbol IS NULL THEN com_curr_symbol
             ELSE pay_curr_symbol
         END AS pay_currency,
         CASE
             WHEN type IS NOT NULL
                  AND type = 'sale_refund' THEN ' - Refund'
             ELSE ' '
         END AS sale_refund,
         date_start,
         date_stop
  FROM
    (SELECT COALESCE(rcs.name, 'Without Area') AS area,
            COALESCE(rp.name, rp2.name, '') AS cust_name,
            rp.ref AS cust_ref,
            rpu.name AS pers_in_charge,
            ai.date_invoice AS invoice_date,
            ai.number AS invoice_no,
            (CASE WHEN ai.type = 'out_invoice'
                  THEN ai.amount_untaxed
                  ELSE ai.amount_untaxed * -1
                  END) AS untaxed_amount,
            (CASE WHEN ai.type = 'out_invoice'
                  THEN ai.amount_tax
                  ELSE ai.amount_tax * -1
                  END) AS tax_amount,
            CASE
                WHEN rc_com.id != rc_inv.id AND ai.type = 'out_invoice'
                     THEN ROUND(ai.amount_total /
                                (SELECT rate
                                 FROM res_currency_rate
                                 WHERE name <= ai.date_invoice
                                       AND res_currency_rate.currency_id = rc_inv.id
                                 ORDER BY name DESC, create_date DESC LIMIT 1), 2)
                WHEN rc_com.id != rc_inv.id AND ai.type != 'out_invoice'
                     THEN -1 * ROUND(ai.amount_total /
                                (SELECT rate
                                 FROM res_currency_rate
                                 WHERE name <= ai.date_invoice
                                       AND res_currency_rate.currency_id = rc_inv.id
                                 ORDER BY name DESC, create_date DESC LIMIT 1), 2)
                WHEN rc_com.id = rc_inv.id AND ai.type = 'out_invoice'
                     THEN ai.amount_total
                ELSE ai.amount_total * -1
            END AS invoice_amount,
            (CASE WHEN ai.type = 'out_invoice'
                  THEN ai.amount_total
                  ELSE ai.amount_total * -1
                  END) AS invoice_amount_currency,
            ai.date_due AS invoice_due_date,
            aml2.date AS pay_date,
            (CASE WHEN ai.type = 'out_invoice'
                  THEN COALESCE(aml2.credit, 0.0)
                  ELSE COALESCE(aml2.debit, 0.0) * -1
                  END) AS pay_amount,
            (CASE WHEN ai.type = 'out_invoice'
                  THEN aml2.amount_currency
                  ELSE aml2.amount_currency * -1
                  END) AS pay_amount_currency,
            CASE
                WHEN rc_com.id != rc_inv.id AND ai.type = 'out_invoice'
                     THEN ROUND((ai.residual /
                                 (SELECT rate
                                  FROM res_currency_rate
                                  WHERE name <= ai.date_invoice
                                        AND res_currency_rate.currency_id = rc_inv.id
                                  ORDER BY name DESC, create_date DESC LIMIT 1)), 2)
                WHEN rc_com.id != rc_inv.id AND ai.type != 'out_invoice'
                     THEN -1 * ROUND((ai.residual /
                                 (SELECT rate
                                  FROM res_currency_rate
                                  WHERE name <= ai.date_invoice
                                        AND res_currency_rate.currency_id = rc_inv.id
                                  ORDER BY name DESC, create_date DESC LIMIT 1)), 2)
                WHEN rc_com.id = rc_inv.id AND ai.type = 'out_invoice'
                     THEN ai.residual
                ELSE ai.residual * -1
            END AS balance,
            CASE WHEN ai.type = 'out invoice'
                 THEN ai.residual
                 ELSE ai.residual * -1
                 END AS balance_currency,
            ai.date_due - $P{TODAY} AS pass_due,
                                  rc_com.id AS com_curr_id,
                                  rc_com.symbol AS com_curr_symbol,
                                  rc_com.rounding AS com_curr_rounding,
                                  rc_inv.id AS inv_curr_id,
                                  rc_inv.symbol AS inv_curr_symbol,
                                  rc_pay.id AS pay_curr_id,
                                  rc_pay.symbol AS pay_curr_symbol,
                                  aj.type AS type,
                                  ap.date_start AS date_start,
                                  ap.date_stop AS date_stop,
                                  CASE WHEN ai.type = 'out_invoice'
                                       THEN av.payment_rate
                                       ELSE av.payment_rate * -1
                                       END AS rate,
                                  aml2.move_id AS MOVE,
                                  COALESCE(aml2.reconcile_id, aml2.reconcile_partial_id) AS reconcile
     FROM account_invoice ai
     LEFT OUTER JOIN res_partner rp ON (rp.id = ai.partner_id)
     LEFT OUTER JOIN res_country_state rcs ON (rcs.id = rp.state_id)
     LEFT OUTER JOIN res_partner rp2 ON (rp2.id = ai.partner_id)
     LEFT OUTER JOIN res_users ru ON (ru.id = ai.user_id)
     LEFT OUTER JOIN res_partner rpu ON (rpu.id = ru.partner_id)
     LEFT OUTER JOIN res_company rco ON (rco.id = ai.company_id)
     LEFT OUTER JOIN account_move_line aml ON (aml.move_id = ai.move_id
                                               AND (COALESCE(aml.reconcile_id, aml.reconcile_partial_id) IS NOT NULL)
                                               AND (aml.account_id IN
                                                      (SELECT id
                                                        FROM receivable_accounts)))
     LEFT OUTER JOIN account_move_line aml2 ON (aml.id != aml2.id
                                                AND COALESCE(aml2.reconcile_id, aml2.reconcile_partial_id) = COALESCE(aml.reconcile_id, aml.reconcile_partial_id)
                                                AND (aml2.account_id IN
                                                       (SELECT id
                                                        FROM receivable_accounts)))
     LEFT OUTER JOIN account_journal aj ON (aj.id = aml2.journal_id)
     LEFT OUTER JOIN res_currency rc_com ON (rc_com.id = rco.currency_id)
     LEFT OUTER JOIN res_currency rc_inv ON (rc_inv.id = ai.currency_id)
     LEFT OUTER JOIN res_currency rc_pay ON (rc_pay.id = aj.currency)
     LEFT OUTER JOIN account_period ap ON (ap.company_id = rco.id)
     LEFT OUTER JOIN account_voucher av ON (av.move_id = aml2.move_id)
     WHERE ai.id IN
         (SELECT id
          FROM selected_invoices)
       AND ($P{TODAY} BETWEEN ap.date_start AND ap.date_stop)) AS raw_table
  GROUP BY area,
           cust_name,
           cust_ref,
           pers_in_charge,
           invoice_date,
           invoice_no,
           com_curr_id,
           inv_curr_id,
           pay_curr_id,
           untaxed_amount,
           tax_amount,
           date_start,
           date_stop,
           invoice_amount,
           invoice_amount_currency,
           invoice_due_date,
           pay_date,
           rate,
           balance,
           balance_currency,
           pass_due,
           com_curr_symbol,
           inv_curr_symbol,
           pay_curr_symbol,
           type,
           move,
           reconcile
  ORDER BY area,
           cust_name,
           invoice_no,
           invoice_date
"""


class via_jasper_report(orm.TransientModel):
    _inherit = 'via.jasper.report'
    _description = 'Trade Account Receivable List'

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
                'domain': {
                    'customer_ids': [
                        ('company_id', '=', False),
                        '|', ('customer', '=', True),
                        ('parent_id', '=', False)
                    ]},
                'value': {'customer_ids': False},
            }
        return {
            'domain': {
                'customer_ids': [
                    ('company_id', 'in', com_ids[0][2]),
                    '|', ('customer', '=', True),
                    ('parent_id', '=', False)
                ]},
            'value': {'customer_ids': False},
        }

    _onchange = {
        'company_ids': (onchange_company_ids, 'company_ids', 'context'),
    }

    _visibility = [
        'company_ids',
        'customer_ids',
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
        'customer_ids': ['display_name'],
    }

    def validate_parameters(self, cr, uid, form, context=None):
        if len(form.company_ids) == 0:
            raise orm.except_orm(_('Caution !'), _('No page will be printed !'))

    def print_report(self, cr, uid, form, context=None):
        self.validate_parameters(cr, uid, form, context=context)

        if len(form.customer_ids) == 0:
            sql_cust_ids = ''
        else:
            cust_list = form.get_customer_ids(context=context)
            cust_ids = ", ".join(str(n) for n in cust_list)
            sql_cust_ids = 'AND ai.partner_id IN (%s)' % cust_ids
        form.add_marshalled_data('CUSTOMER_IDS', sql_cust_ids)
        form.add_marshalled_data('REPORT_SQL', report_sql)

register_report_wizard(RPT_NAME, wizard)
