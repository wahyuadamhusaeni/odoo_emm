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

ar_cust_sql = lambda: """
WITH receivable_accounts AS
  (SELECT id
   FROM account_account
   WHERE TYPE = 'receivable'),
     invoice_data AS
  (SELECT ai.id AS inv_id,
          ai.move_id,
          ai.type AS inv_type,
          ai.number AS inv_number,
          ai.company_id AS company,
          ai.date_invoice AS date_invoice,
          ai.partner_id AS partner,
          (CASE WHEN ai.currency_id != rc.currency_id THEN CONCAT ('(',rcy.symbol, ' ', ai.amount_untaxed,')') ELSE NULL END) AS note_untaxed,
          (CASE WHEN ai.currency_id != rc.currency_id THEN CONCAT ('(',rcy.symbol, ' ', ai.amount_tax,')') ELSE NULL END) AS note_tax,
          (CASE WHEN ai.currency_id != rc.currency_id THEN CONCAT ('(',rcy.symbol, ' ', ai.amount_total,')') ELSE NULL END) AS note_total,
          (CASE WHEN ai.currency_id != rc.currency_id THEN ai.amount_untaxed /
             (SELECT rate
              FROM res_currency_rate
              WHERE currency_id = ai.currency_id
                AND name <= ai.date_invoice
              ORDER BY name DESC LIMIT 1) ELSE ai.amount_untaxed END) AS amount_untaxed,
          (CASE WHEN ai.currency_id != rc.currency_id THEN ai.amount_tax /
             (SELECT rate
              FROM res_currency_rate
              WHERE currency_id = ai.currency_id
                AND name <= ai.date_invoice
              ORDER BY name DESC LIMIT 1) ELSE ai.amount_tax END) AS amount_tax,
          (CASE WHEN ai.currency_id != rc.currency_id THEN ROUND(ai.residual /
                                                                   (SELECT rate
                                                                    FROM res_currency_rate
                                                                    WHERE currency_id = ai.currency_id
                                                                      AND name <= ai.date_invoice
                                                                    ORDER BY name DESC LIMIT 1),2) ELSE ai.residual END) AS inv_residual,
          (CASE WHEN ai.currency_id != rc.currency_id THEN CONCAT('(',rcy.symbol,' ', ai.residual, ')') ELSE NULL END) AS note_inv_residual,
          -- Add CASE WHEN invoice type = refund then multiply with -1
          (CASE WHEN ai.TYPE = 'out_invoice' THEN SUM(aml.debit) ELSE SUM(aml.debit) * -1 END) AS amount_total,
          ai.state AS state,
          am.state AS am_state,
          ai.currency_id AS currency_inv,
          rc.currency_id AS currency_comp,
          COALESCE(rp2.name, rp.name) AS cust_name,
          COALESCE(rcs.name,'Without Area') AS area,
          SUM(aml.amount_currency) AS amount_currency
   FROM
    --FETCH cust invoice data
     ((SELECT ai1.id,
             ai1.move_id,
             ai1.type,
             ai1.number,
             ai1.company_id,
             ai1.date_invoice,
             ai1.partner_id,
             ai1.currency_id,
             ai1.amount_untaxed,
             ai1.amount_tax,
             ai1.amount_total,
             ai1.residual,
             ai1.state
      FROM account_invoice ai1
      --[DS]: replace LEFT JOIN with JOIN
      JOIN account_move_line aml1
           ON ai1.move_id = aml1.move_id
          AND COALESCE(aml1.debit, 0.0) != 0.0
          AND aml1.account_id IN (SELECT id FROM receivable_accounts))
   UNION
    -- FETCH cust refund data which paid using cust payment (bank/cash)
      (SELECT ai2.id,
              ai2.move_id,
              ai2.type,
              ai2.number,
              ai2.company_id,
              ai2.date_invoice,
              ai2.partner_id,
              ai2.currency_id,
              -1 * ai2.amount_untaxed AS amount_untaxed,
              -1 * ai2.amount_tax AS amount_tax,
              -1 * ai2.amount_total AS amount_total,
              -1 * ai2.residual AS residual,
              ai2.state
      FROM account_invoice ai2
      JOIN account_move_line aml2
           ON ai2.move_id = aml2.move_id
          AND COALESCE(aml2.credit, 0.0) != 0.0
          AND aml2.account_id IN (SELECT id FROM receivable_accounts)
      JOIN account_move am2 ON am2.id = ai2.move_id
      JOIN account_journal acj2_1
           ON acj2_1.id = am2.journal_id
          AND acj2_1.TYPE = 'sale_refund'
      JOIN account_move_line aml_rc
           ON aml2.id != aml_rc.id
          AND COALESCE(aml_rc.reconcile_id, aml_rc.reconcile_partial_id)
            = COALESCE(aml2.reconcile_id, aml2.reconcile_partial_id)
          AND aml2.account_id IN (SELECT id FROM receivable_accounts)
      JOIN account_journal acj2_2
           ON acj2_2.id = aml_rc.journal_id
          AND acj2_2.TYPE != 'sale')
   UNION
    --FETCH cust refund data that have not been paid
      (SELECT ai3.id,
             ai3.move_id,
             ai3.type,
             ai3.number,
             ai3.company_id,
             ai3.date_invoice,
             ai3.partner_id,
             ai3.currency_id,
             -1 * ai3.amount_untaxed AS amount_untaxed,
             -1 * ai3.amount_tax AS amount_tax,
             -1 * ai3.amount_total AS amount_total,
             -1 * ai3.residual AS residual,
             ai3.state
      FROM account_invoice ai3
      JOIN account_move_line aml3
           ON ai3.move_id = aml3.move_id
          AND COALESCE(aml3.credit, 0.0) != 0.0
          AND aml3.reconcile_id IS NULL
          AND aml3.reconcile_partial_id IS NULL
          AND aml3.account_id IN (SELECT id FROM receivable_accounts)
      JOIN account_move am3 ON am3.id = ai3.move_id
      JOIN account_journal acj3_1
           ON acj3_1.id = am3.journal_id
          AND acj3_1.type = 'sale_refund')) ai
   LEFT JOIN account_move_line aml ON ai.move_id = aml.move_id
   JOIN account_move am ON am.id = ai.move_id
   LEFT JOIN res_partner rp ON rp.id = ai.partner_id
   LEFT JOIN res_partner rp2 ON rp2.id = rp.parent_id
   LEFT JOIN res_country_state rcs ON rcs.id = COALESCE(rp2.state_id, rp.state_id)
   JOIN res_company rc ON ai.company_id = rc.id
   JOIN res_currency rcy ON ai.currency_id = rcy.id
   GROUP BY ai.id,
            ai.move_id,
            ai.type,
            ai.number,
            ai.company_id,
            ai.date_invoice,
            ai.residual,
            ai.currency_id,
            ai.partner_id,
            rc.currency_id,
            ai.amount_untaxed,
            rcy.symbol,
            ai.amount_tax,
            ai.amount_total,
            ai.state,
            am.state,
            rp.name,
            rp2.name,
            rcs.name
   ORDER BY inv_id),
     payment_data AS
  (SELECT ai.id AS inv_id,
          (CASE WHEN aj2.type = 'sale_refund' THEN CONCAT(am.name,'-Refund') ELSE am.name END) AS payment_number,
          COALESCE(payment.date, payment.date_created) AS payment_date,
          -- Add payment.debit to include refund data
          SUM(COALESCE(payment.credit,0)-COALESCE(payment.debit,0)) AS payment_total,
          (CASE WHEN (aj2.currency != rc.currency_id) THEN CONCAT('(',rcy.symbol, ' ' , ROUND(ABS(SUM(payment.amount_currency) / COALESCE(av.payment_rate, 1)),2),')') ELSE NULL END) AS note_payment_total
   FROM account_invoice ai
   LEFT JOIN account_move_line br
        ON ai.move_id = br.move_id
        -- Remove validation so it includes refund data
        --AND br.debit != 0
       AND br.account_id IN (SELECT id FROM receivable_accounts)
   LEFT JOIN account_move_line payment
        ON payment.id != br.id
       AND COALESCE(br.reconcile_id, br.reconcile_partial_id)
         = COALESCE(payment.reconcile_id, payment.reconcile_partial_id)
       -- Remove validation so it includes refund data
       --AND payment.credit != 0 AND payment.credit IS NOT NULL
       AND payment.account_id IN (SELECT id FROM receivable_accounts)
   LEFT JOIN account_move am ON payment.move_id = am.id
   JOIN account_journal aj ON aj.id = ai.journal_id
   JOIN account_journal aj2 ON aj2.id = am.journal_id
   LEFT JOIN account_voucher av ON am.id = av.move_id
   LEFT JOIN res_currency rcy ON aj2.currency = rcy.id
   JOIN res_company rc ON ai.company_id = rc.id
   WHERE (br.reconcile_id IS NOT NULL
          OR br.reconcile_partial_id IS NOT NULL)
   GROUP BY ai.id,
            aj2.type,
            am.name,
            payment.date,
            payment.date_created,
            aj2.currency,
            rc.currency_id,
            rcy.symbol,
            av.payment_rate
   ORDER BY inv_id),
     payable_data AS
  (SELECT *
   FROM $P!{PAYABLE_TABLE}),
     receivable_data AS
  (SELECT *
   FROM $P!{RECEIVABLE_TABLE})
SELECT id.inv_id,
       id.move_id,
       id.inv_number,
       id.date_invoice,
       id.inv_residual,
       id.note_untaxed,
       id.note_tax,
       id.note_total,
       id.amount_untaxed,
       id.amount_tax,
       id.amount_total,
       id.cust_name,
       id.area,
       pd.inv_id,
       pd.payment_number,
       pd.payment_date,
       pd.payment_total,
       pd.note_payment_total,
       id.inv_residual AS payment_balance,
       id.note_inv_residual AS note_payment_balance,
       ABS(rd.receivable) AS receivable,
       ABS(pdt.payable) AS payable
FROM invoice_data id
LEFT JOIN payment_data pd ON (id.inv_id = pd.inv_id)
LEFT JOIN receivable_data rd ON rd.partner_id = id.partner
LEFT JOIN payable_data pdt ON pdt.partner_id = id.partner
WHERE id.STATE IN ('open',
                   'paid')
  AND id.date_invoice::DATE BETWEEN '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}' AND '$P!{TO_DATE_2_YR}-$P!{TO_DATE_2_MO}-$P!{TO_DATE_2_DY}'
  AND id.inv_type IN ('out_invoice',
                      'out_refund')
  AND id.company IN ($P!{COMPANY_IDS}) $P!{CUSTOMER_IDS}
ORDER BY id.cust_name,
         id.area,
         id.inv_number,
         id.date_invoice,
         pd.payment_number,
         pd.payment_date
"""
