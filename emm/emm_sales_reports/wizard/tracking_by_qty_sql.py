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

tracking_by_qty_sql = lambda: """
WITH so_dataset AS
  ( SELECT so.id AS so_id,
           sol.product_id AS sol_prd_id,
           prod_uom.id AS prd_uom_id,
           SUM(sol.product_uom_qty * (CASE
               WHEN so_uom_cat.id = prod_uom_cat.id
                   THEN (so_uom.factor * (CASE
                       WHEN prod_uom.id IS NULL
                           THEN 1
                       ELSE prod_uom.factor
                       END))
               ELSE 1
               END)) AS so_qty
   FROM sale_order so
   JOIN sale_order_line sol ON (sol.order_id = so.id)
   LEFT JOIN product_product prd ON (prd.id = sol.product_id)
   LEFT JOIN product_template prd_tmpl ON (prd_tmpl.id = prd.product_tmpl_id)
   LEFT JOIN product_uom prod_uom ON (prod_uom.id = prd_tmpl.uom_id)
   LEFT JOIN product_uom_categ prod_uom_cat ON (prod_uom_cat.id = prod_uom.category_id)
   LEFT JOIN product_uom so_uom ON (so_uom.id = sol.product_uom)
   LEFT JOIN product_uom_categ so_uom_cat ON (so_uom_cat.id = so_uom.category_id)
   LEFT JOIN res_partner rp ON (rp.id = so.partner_id)
   LEFT JOIN res_partner rp2 ON (rp.parent_id = rp2.id)
   WHERE so.state NOT IN ('draft', 'sent', 'cancel')
     AND so.date_order BETWEEN '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}'
     AND '$P!{TO_DATE_2_YR}-$P!{TO_DATE_2_MO}-$P!{TO_DATE_2_DY}'
     AND (rp.id IN ($P!{CUSTOMER_IDS}) OR rp2.id IN ($P!{CUSTOMER_IDS}))
   GROUP BY so.id,
            sol.product_id,
            prod_uom.id
),
     sm_dataset AS
  ( SELECT so.id AS so_id,
           sol.product_id AS sol_prd_id,
           prod_uom.id AS prd_uom_id,
           SUM(COALESCE(sm.product_qty, 0.0) * (CASE
               WHEN do_uom_cat.id = prod_uom_cat.id
                   THEN (do_uom.factor * (CASE
                       WHEN prod_uom.id IS NULL
                           THEN 1
                       ELSE prod_uom.factor
                       END))
               ELSE 1
               END) * (CASE WHEN sp.type = 'in' THEN -1 ELSE 1 END)) AS do_qty
   FROM sale_order so
   JOIN sale_order_line sol ON (sol.order_id = so.id)
   LEFT JOIN product_product prd ON (prd.id = sol.product_id)
   LEFT JOIN product_template prd_tmpl ON (prd_tmpl.id = prd.product_tmpl_id)
   LEFT JOIN product_uom prod_uom ON (prod_uom.id = prd_tmpl.uom_id)
   LEFT JOIN product_uom_categ prod_uom_cat ON (prod_uom_cat.id = prod_uom.category_id)
   LEFT JOIN stock_move sm ON (sol.id = sm.sale_line_id
                               AND sm.state IN ('done'))
   LEFT JOIN stock_picking sp ON (sp.id = sm.picking_id)
   LEFT JOIN product_uom do_uom ON (do_uom.id = sm.product_uom)
   LEFT JOIN product_uom_categ do_uom_cat ON (do_uom_cat.id = do_uom.category_id)
   LEFT JOIN product_uom so_uom ON (so_uom.id = sol.product_uom)
   LEFT JOIN product_uom_categ so_uom_cat ON (so_uom_cat.id = so_uom.category_id)
   GROUP BY so.id,
            sol.product_id,
            prod_uom.id
),
     cancel_sm_dataset AS
  ( SELECT so.id AS so_id,
           sol.product_id AS sol_prd_id,
           prod_uom.id AS prd_uom_id,
           SUM(COALESCE(sm.product_qty, 0.0) * (CASE
               WHEN do_uom_cat.id = prod_uom_cat.id
                   THEN (do_uom.factor * (CASE
                       WHEN prod_uom.id IS NULL
                           THEN 1
                       ELSE prod_uom.factor
                       END))
               ELSE 1
               END) * (CASE WHEN sp.type = 'in' THEN -1 ELSE 1 END)) AS cancel_qty
   FROM sale_order so
   JOIN sale_order_line sol ON (sol.order_id = so.id)
   LEFT JOIN product_product prd ON (prd.id = sol.product_id)
   LEFT JOIN product_template prd_tmpl ON (prd_tmpl.id = prd.product_tmpl_id)
   LEFT JOIN product_uom prod_uom ON (prod_uom.id = prd_tmpl.uom_id)
   LEFT JOIN product_uom_categ prod_uom_cat ON (prod_uom_cat.id = prod_uom.category_id)
   LEFT JOIN stock_move sm ON (sol.id = sm.sale_line_id
                               AND sm.state IN ('cancel'))
   LEFT JOIN stock_picking sp ON (sp.id = sm.picking_id)
   LEFT JOIN product_uom do_uom ON (do_uom.id = sm.product_uom)
   LEFT JOIN product_uom_categ do_uom_cat ON (do_uom_cat.id = do_uom.category_id)
   LEFT JOIN product_uom so_uom ON (so_uom.id = sol.product_uom)
   LEFT JOIN product_uom_categ so_uom_cat ON (so_uom_cat.id = so_uom.category_id)
   GROUP BY so.id,
            sol.product_id,
            prod_uom.id
),
     sp_dataset AS
  ( SELECT so.id AS so_id,
           sol.product_id AS sol_prd_id,
           prod_uom.id AS prd_uom_id,
           sp.id AS picking_id,
           sm.state AS state,
           SUM(COALESCE(sm.product_qty, 0.0) * (CASE
               WHEN do_uom_cat.id = prod_uom_cat.id
                   THEN (do_uom.factor * (CASE
                       WHEN prod_uom.id IS NULL
                           THEN 1
                       ELSE prod_uom.factor
                       END))
               ELSE 1
               END) * (CASE WHEN sp.type = 'in' THEN -1 ELSE 1 END)) AS do_qty
   FROM sale_order so
   JOIN sale_order_line sol ON (sol.order_id = so.id)
   LEFT JOIN product_product prd ON (prd.id = sol.product_id)
   LEFT JOIN product_template prd_tmpl ON (prd_tmpl.id = prd.product_tmpl_id)
   LEFT JOIN product_uom prod_uom ON (prod_uom.id = prd_tmpl.uom_id)
   LEFT JOIN product_uom_categ prod_uom_cat ON (prod_uom_cat.id = prod_uom.category_id)
   LEFT JOIN stock_move sm ON (sol.id = sm.sale_line_id)
   LEFT JOIN stock_picking sp ON (sp.id = sm.picking_id)
   LEFT JOIN product_uom do_uom ON (do_uom.id = sm.product_uom)
   LEFT JOIN product_uom_categ do_uom_cat ON (do_uom_cat.id = do_uom.category_id)
   LEFT JOIN product_uom so_uom ON (so_uom.id = sol.product_uom)
   LEFT JOIN product_uom_categ so_uom_cat ON (so_uom_cat.id = so_uom.category_id)
   GROUP BY so.id,
            sol.product_id,
            prod_uom.id,
            sp.id,
            sm.state
)
SELECT COALESCE(rp2.name, rp.name) AS customer_name,
       sord.date_order AS so_date,
       sord.name AS so_no,
       pp.default_code AS prod_code,
       pp.name_template AS prod,
       product_uom.name AS uom,
       so.so_qty AS so_qty,
       sm.do_qty AS delivery_qty,
       csm.cancel_qty AS cancel_qty,
       so.so_qty - sm.do_qty AS outstand_done,
       so.so_qty - sm.do_qty - csm.cancel_qty AS outstand_done_cancel,
       dord.name AS do_no,
       dord.date_done AS do_date,
       sp.state AS do_state,
       (COALESCE(dord.date_done::DATE, NOW()::DATE) - sord.date_order) AS aging,
       (CASE WHEN sp.state = 'cancel'
             THEN 0
             ELSE sp.do_qty
        END) AS stock
FROM so_dataset so
LEFT JOIN sm_dataset sm ON (so.so_id = sm.so_id
                         AND COALESCE(so.sol_prd_id, -1) = COALESCE(sm.sol_prd_id, -1)
                         AND COALESCE(so.prd_uom_id, -1) = COALESCE(sm.prd_uom_id, -1))
LEFT JOIN cancel_sm_dataset csm ON (so.so_id = csm.so_id
                         AND COALESCE(so.sol_prd_id, -1) = COALESCE(csm.sol_prd_id, -1)
                         AND COALESCE(so.prd_uom_id, -1) = COALESCE(csm.prd_uom_id, -1))
LEFT JOIN sp_dataset sp ON (so.so_id = sp.so_id
                         AND COALESCE(so.sol_prd_id, -1) = COALESCE(sp.sol_prd_id, -1)
                         AND COALESCE(so.prd_uom_id, -1) = COALESCE(sp.prd_uom_id, -1))
JOIN sale_order sord ON (sord.id = so.so_id)
LEFT JOIN res_partner rp ON (rp.id = sord.partner_id)
LEFT JOIN res_partner rp2 ON (rp.parent_id = rp2.id)
LEFT JOIN product_product pp ON (pp.id = so.sol_prd_id)
LEFT JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
LEFT JOIN product_uom product_uom ON (product_uom.id = pt.uom_id)
LEFT JOIN stock_picking dord ON (dord.id = sp.picking_id)
ORDER BY COALESCE(rp2.name, rp.name),
         sord.name,
         pp.default_code,
         dord.name,
         sp.state
"""
