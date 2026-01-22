
sales_tracking_sql = lambda: '''
WITH _so_inv AS
(SELECT
  partner.id AS _partner_id,
  COALESCE(rp.name, partner.name) AS cust_name,
  so.id AS _so_id,
  so.date_order AS so_date,
  so.name AS so_no,
  so.amount_total AS so_amt,
  so_curr.name AS so_ori_curr,
  so.amount_total
    / (SELECT COALESCE(curr_rate.rate, 1)
       FROM res_currency_rate curr_rate
       WHERE curr_rate.currency_id = so_curr.id AND curr_rate.name <= so.date_order
       ORDER BY name DESC
       LIMIT 1)
    * (SELECT COALESCE(curr_rate.rate, 1)
       FROM res_currency_rate curr_rate
       WHERE curr_rate.currency_id = company.currency_id AND curr_rate.name <= so.date_order
       ORDER BY name DESC
       LIMIT 1) AS base_so_amt,
  ai.id AS _inv_id,
  ai.number AS inv_no,
  ai.date_invoice AS inv_date,
  ai_curr.name AS _inv_curr,
  ai.amount_total AS _inv_amt,
  ABS(COALESCE(aml_inv.debit, 0) - COALESCE(aml_inv.credit,0)) AS base_inv_amt,
  ai.residual AS _inv_residual,
  ai.residual
    / (SELECT COALESCE(curr_rate.rate, 1)
       FROM res_currency_rate curr_rate
       WHERE curr_rate.currency_id = ai_curr.id AND curr_rate.name <= ai.date_invoice
       ORDER BY name DESC
       LIMIT 1)
    * (SELECT COALESCE(curr_rate.rate, 1)
       FROM res_currency_rate curr_rate
       WHERE curr_rate.currency_id = company.currency_id AND curr_rate.name <= ai.date_invoice
       ORDER BY name DESC
       LIMIT 1) AS _base_residual_amt
FROM
  sale_order so
  JOIN res_partner partner
       ON (partner.id = so.partner_id)
  JOIN res_company company
       ON (company.id = so.company_id)
  JOIN res_currency co_curr
       ON (co_curr.id = company.currency_id)
  LEFT JOIN product_pricelist so_price
       ON (so_price.id = so.pricelist_id)
  LEFT JOIN res_currency so_curr
       ON (so_curr.id = so_price.currency_id)
  LEFT JOIN sale_order_invoice_rel soir
       ON (soir.order_id = so.id)
  LEFT JOIN account_invoice ai
       ON (ai.id = soir.invoice_id
           AND ai.state IN ('open', 'paid'))
  LEFT JOIN res_currency ai_curr
       ON (ai_curr.id = ai.currency_id)
  LEFT JOIN account_move_line aml_inv
       ON (aml_inv.move_id = ai.move_id
           AND aml_inv.account_id = ai.account_id)
  LEFT JOIN res_partner rp
       ON (partner.parent_id = rp.id)
WHERE
  so.state NOT IN ('draft', 'sent', 'cancel')
  AND so.date_order BETWEEN '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}' 
  AND '$P!{TO_DATE_2_YR}-$P!{TO_DATE_2_MO}-$P!{TO_DATE_2_DY}'
  AND so.company_id IN ('$P!{COMPANY_IDS}')
),  
_inv_pay AS
(SELECT
  partner.id AS _partner_id,
  partner.name AS cust_name,
  so.id AS _so_id,
  so.date_order AS so_date,
  so.name AS so_no,
  so.amount_total AS so_amt,
  so_curr.name AS so_ori_curr,
  so.amount_total
    / (SELECT COALESCE(curr_rate.rate, 1)
       FROM res_currency_rate curr_rate
       WHERE curr_rate.currency_id = so_curr.id AND curr_rate.name <= so.date_order
       ORDER BY name DESC
       LIMIT 1)
    * (SELECT COALESCE(curr_rate.rate, 1)
       FROM res_currency_rate curr_rate
       WHERE curr_rate.currency_id = company.currency_id AND curr_rate.name <= so.date_order
       ORDER BY name DESC
       LIMIT 1) AS base_so_amt,
  ai.id AS _inv_id,
  ai.number AS _inv,
  ai.date_invoice AS inv_date,
  ai_curr.name AS _inv_curr,
  ai.amount_total AS _inv_amt,
  ABS(COALESCE(aml_inv.debit, 0) - COALESCE(aml_inv.credit,0)) AS base_inv_amt,
  ai.residual AS _inv_residual,
  ai.residual
    / (SELECT COALESCE(curr_rate.rate, 1)
       FROM res_currency_rate curr_rate
       WHERE curr_rate.currency_id = ai_curr.id AND curr_rate.name <= ai.date_invoice
       ORDER BY name DESC
       LIMIT 1)
    * (SELECT COALESCE(curr_rate.rate, 1)
       FROM res_currency_rate curr_rate
       WHERE curr_rate.currency_id = company.currency_id AND curr_rate.name <= ai.date_invoice
       ORDER BY name DESC
       LIMIT 1) AS _base_residual_amt,
  am_pay.name AS payment_no,
  am_pay.date AS payment_dt,
  COALESCE(pay_curr.name, co_curr.name) AS pay_amt_curr,
  CASE WHEN aml_pay.amount_currency = 0
THEN ABS(COALESCE(aml_pay.debit, 0) - COALESCE(aml_pay.credit,0))
ELSE aml_pay.amount_currency
END AS pay_amt,
  ABS(COALESCE(aml_pay.debit, 0) - COALESCE(aml_pay.credit,0)) AS base_pay_amt
FROM
  sale_order so
  JOIN res_partner partner
       ON (partner.id = so.partner_id)
  JOIN res_company company
       ON (company.id = so.company_id)
  JOIN res_currency co_curr
       ON (co_curr.id = company.currency_id)
  LEFT JOIN product_pricelist so_price
       ON (so_price.id = so.pricelist_id)
  LEFT JOIN res_currency so_curr
       ON (so_curr.id = so_price.currency_id)
  LEFT JOIN sale_order_invoice_rel soir
       ON (soir.order_id = so.id)
  LEFT JOIN account_invoice ai
       ON (ai.id = soir.invoice_id
           AND ai.state IN ('open', 'paid'))
  LEFT JOIN res_currency ai_curr
       ON (ai_curr.id = ai.currency_id)
  LEFT JOIN account_move_line aml_inv
       ON (aml_inv.move_id = ai.move_id
           AND aml_inv.account_id = ai.account_id)
  LEFT JOIN account_move_line aml_pay
       ON (COALESCE(aml_pay.reconcile_id, aml_pay.reconcile_partial_id)
             = COALESCE(aml_inv.reconcile_id, aml_inv.reconcile_partial_id)
           AND aml_pay.id != aml_inv.id)
  LEFT JOIN account_move am_pay
       ON (am_pay.id = aml_pay.move_id)
  LEFT JOIN res_currency pay_curr
       ON (pay_curr.id = aml_pay.currency_id)
WHERE
  so.state NOT IN ('draft', 'sent', 'cancel')
  AND so.date_order BETWEEN '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}'
  AND '$P!{TO_DATE_2_YR}-$P!{TO_DATE_2_MO}-$P!{TO_DATE_2_DY}'
  AND so.company_id IN ($P!{COMPANY_IDS})
  )

SELECT
  _core.cust_name,
  _core.so_date,
  _core.so_no,
  _core.base_so_amt,
  _core.so_ori_curr,
  _core.so_amt,
  ABS(COALESCE(_core.base_so_amt, 0) - COALESCE(base_inv_amt._inv_amt)) AS so_to_inv,
  ABS(COALESCE(_core.base_so_amt, 0) - COALESCE(base_pay_amt.pay_amt)) AS so_to_pay,
  _core.inv_no,
  _core.inv_date,
  COALESCE(_core._inv_amt, 0) AS inv_amt,
  _core.base_inv_amt,
  COALESCE(_core._inv_residual, 0) AS inv_to_res,
  COALESCE(_core._base_residual_amt, 0) AS _base_res_amt,
  _payment.payment_no,
  _payment.payment_dt,
  _payment.pay_amt_curr,
  _payment.pay_amt,
  _payment.base_pay_amt
FROM
  _so_inv _core
  LEFT JOIN _inv_pay _payment
       ON (_payment._partner_id = _core._partner_id
           AND _payment._so_id = _core._so_id
           AND _payment._inv_id = _core._inv_id)
  LEFT JOIN (SELECT _partner_id, _so_id, SUM(base_inv_amt) AS _inv_amt
             FROM _so_inv
             GROUP BY _partner_id, _so_id) base_inv_amt
       ON (base_inv_amt._partner_id = _core._partner_id
           AND base_inv_amt._so_id = _core._so_id)
  LEFT JOIN (SELECT _partner_id, _so_id, SUM(base_pay_amt) AS pay_amt
             FROM _inv_pay
             GROUP BY _partner_id, _so_id) base_pay_amt
       ON (base_pay_amt._partner_id = _core._partner_id
           AND base_pay_amt._so_id = _core._so_id)
WHERE _core._partner_id IN ($P!{CUSTOMER_IDS})
ORDER BY
  cust_name ASC,
  so_date ASC,
  so_no ASC,
  inv_date ASC,
  inv_no ASC,
  payment_dt ASC,
  payment_no ASC
'''