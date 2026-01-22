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

sql_for_sales_report = lambda: """
SELECT
  rp_user.name AS salesman,
  COALESCE(rp2.name, cust.name) AS customer,
  so.date_order AS so_date,
  so.name AS so_no,
  prod.default_code AS product_code,
  prod.name_template AS product,
  COALESCE(sol.product_uom_qty, 0)
    / COALESCE(sale_uom.factor, 1)
    * COALESCE(prod_uom.factor, 1) AS so_qty,
  prod_uom.name AS uom,
  (sol.product_uom_qty)
    * (sol.price_unit)
    * ((100-sol.discount)/100) AS so_amt,
  co_curr.name AS currency_comp,
  so_curr.name AS currency_ori,
  (sol.product_uom_qty)
    * (sol.price_unit)
    * ((100-sol.discount)/100)
    / (SELECT COALESCE(curr_rate.rate, 1)
       FROM res_currency_rate curr_rate
       WHERE curr_rate.currency_id = so_curr.id AND curr_rate.name <= so.date_order
       ORDER BY name DESC
       LIMIT 1)
    * (SELECT COALESCE(curr_rate.rate, 1)
       FROM res_currency_rate curr_rate
       WHERE curr_rate.currency_id = company.currency_id AND curr_rate.name <= so.date_order
       ORDER BY name DESC
       LIMIT 1) AS ori_amt
FROM
  sale_order so
  JOIN sale_order_line sol
       ON (sol.order_id = so.id)
  JOIN res_partner cust
       ON (cust.id = so.partner_id)
  JOIN product_product prod
       ON (prod.id = sol.product_id)
  JOIN product_template tmpl
       ON (tmpl.id = prod.product_tmpl_id)
  JOIN res_company company
       ON (company.id = so.company_id)
  JOIN res_currency co_curr
       ON (co_curr.id = company.currency_id)
  LEFT JOIN product_pricelist so_price
       ON (so_price.id = so.pricelist_id)
  LEFT JOIN res_currency so_curr
       ON (so_curr.id = so_price.currency_id)
  LEFT JOIN res_users users
       ON (users.id = so.user_id)
  LEFT JOIN res_partner rp_user
       ON (rp_user.id = users.partner_id)
  LEFT JOIN product_uom prod_uom
       ON (prod_uom.id = tmpl.uom_id)
  LEFT JOIN product_uom sale_uom
       ON (sale_uom.id = sol.product_uom)
  LEFT JOIN res_partner rp2
       ON (cust.parent_id = rp2.id)
WHERE
  so.state NOT IN ('draft', 'sent', 'cancel')
  AND so.date_order BETWEEN '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}'
  AND '$P!{TO_DATE_2_YR}-$P!{TO_DATE_2_MO}-$P!{TO_DATE_2_DY}'
  AND so.company_id IN ($P!{COMPANY_IDS})
  $P!{WHERE_CLAUSE}
ORDER BY
  $P!{ORDER_CLAUSE}
"""

sql_for_sales_report_without_prod_group_level = lambda: """
SELECT
  rp_user.name AS salesman,
  COALESCE(rp2.name, cust.name) AS customer,
  so.date_order AS so_date,
  so.name AS so_no,
  prod.default_code AS product_code,
  prod.name_template AS product,
  COALESCE(sol.product_uom_qty, 0)
    / COALESCE(sale_uom.factor, 1)
    * COALESCE(prod_uom.factor, 1) AS so_qty,
  prod_uom.name AS uom,
  (sol.product_uom_qty)
    * (sol.price_unit)
    * ((100-sol.discount)/100) AS so_amt,
  co_curr.name AS currency_comp,
  so_curr.name AS currency_ori,
  (sol.product_uom_qty)
    * (sol.price_unit)
    * ((100-sol.discount)/100)
    / (SELECT COALESCE(curr_rate.rate, 1)
       FROM res_currency_rate curr_rate
       WHERE curr_rate.currency_id = so_curr.id AND curr_rate.name <= so.date_order
       ORDER BY name DESC
       LIMIT 1)
    * (SELECT COALESCE(curr_rate.rate, 1)
       FROM res_currency_rate curr_rate
       WHERE curr_rate.currency_id = company.currency_id AND curr_rate.name <= so.date_order
       ORDER BY name DESC
       LIMIT 1) AS ori_amt,
    sol.th_weight as total_weight,
    pt.weight as gross_weight,
  (CASE WHEN sol.th_weight = 0
            THEN 0
        ELSE (sol.product_uom_qty) * (sol.price_unit) * ((100-sol.discount)/100/sol.th_weight)END) AS price_perkg
FROM
  sale_order so
  JOIN sale_order_line sol
       ON (sol.order_id = so.id)
  JOIN res_partner cust
       ON (cust.id = so.partner_id)
  JOIN product_product prod
       ON (prod.id = sol.product_id)
  JOIN product_template pt
       ON (pt.id = prod.product_tmpl_id)
  JOIN res_company company
       ON (company.id = so.company_id)
  JOIN res_currency co_curr
       ON (co_curr.id = company.currency_id)
  LEFT JOIN product_pricelist so_price
       ON (so_price.id = so.pricelist_id)
  LEFT JOIN res_currency so_curr
       ON (so_curr.id = so_price.currency_id)
  LEFT JOIN res_users users
       ON (users.id = so.user_id)
  LEFT JOIN res_partner rp_user
       ON (rp_user.id = users.partner_id)
  LEFT JOIN product_uom prod_uom
       ON (prod_uom.id = pt.uom_id)
  LEFT JOIN product_uom sale_uom
       ON (sale_uom.id = sol.product_uom)
  LEFT JOIN res_partner rp2
       ON (cust.parent_id = rp2.id)

WHERE
  so.state NOT IN ('draft', 'sent', 'cancel')
  AND so.date_order BETWEEN '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}'
  AND '$P!{TO_DATE_2_YR}-$P!{TO_DATE_2_MO}-$P!{TO_DATE_2_DY}'
  AND so.company_id IN ($P!{COMPANY_IDS})
  $P!{WHERE_CLAUSE}
ORDER BY
  $P!{ORDER_CLAUSE}
"""
