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

inventory_acc_sql = lambda: """
SELECT prod_data.prod AS prod,
       prod_data.prod_no AS prod_no,
       COALESCE(bb.qty, 0) AS bb_qty,
       COALESCE(bb.amount, 0.0) / (CASE
                                       WHEN COALESCE(bb.qty, 0) = 0 THEN 1
                                       ELSE bb.qty
                                   END) AS bb_avg_per_unit,
       COALESCE(bb.amount, 0.0) AS bb_amount,
       COALESCE(put_in.qty, 0) AS in_qty,
       COALESCE(put_in.amount, 0.0) / (CASE
                                           WHEN COALESCE(put_in.qty, 0) = 0 THEN 1
                                           ELSE put_in.qty
                                       END) AS in_avg_per_unit,
       COALESCE(put_in.amount, 0.0) AS in_amount,
       COALESCE(put_out.qty, 0) AS out_qty,
       COALESCE(put_out.amount, 0.0) / (CASE
                                            WHEN COALESCE(put_out.qty, 0) = 0 THEN 1
                                            ELSE put_out.qty
                                        END) AS out_avg_per_unit,
       COALESCE(put_out.amount, 0.0) AS out_amount,
       COALESCE(bb.qty, 0) + COALESCE(put_in.qty, 0) - COALESCE(put_out.qty, 0) AS eb_qty,
       ((COALESCE(bb.amount, 0.0) + COALESCE(put_in.amount, 0.0) - COALESCE(put_out.amount, 0.0)) / (CASE WHEN (COALESCE(bb.qty, 0) + COALESCE(put_in.qty, 0) - COALESCE(put_out.qty, 0)) = 0 THEN 1 ELSE (COALESCE(bb.qty, 0) + COALESCE(put_in.qty, 0) - COALESCE(put_out.qty, 0)) END)) AS eb_avg_per_unit,
       COALESCE(bb.amount, 0.0) + COALESCE(put_in.amount, 0.0) - COALESCE(put_out.amount, 0.0) AS eb_amount,
       prod_data.prod_cat AS prod_cat
FROM (-- BB

      SELECT COALESCE(bb_put_in.prod_id, bb_put_out.prod_id) AS prod_id,
             COALESCE(bb_put_in.qty, 0.0) - COALESCE(bb_put_out.qty, 0.0) AS qty,
             COALESCE(bb_put_in.amount, 0.0) - COALESCE(bb_put_out.amount, 0.0) AS amount
      FROM (-- BB PUT-IN

            SELECT p.id AS prod_id,
                   SUM(sm.product_qty) AS qty,
                   SUM((CASE WHEN sm.prodlot_id IS NULL THEN COALESCE(pt.standard_price, 0.0) ELSE COALESCE(spl.cost_price_per_unit, 0.0) END) * sm.product_qty) AS amount
            FROM stock_move sm
            INNER JOIN product_product p ON sm.product_id = p.id
            INNER JOIN product_template pt ON p.product_tmpl_id = pt.id
            INNER JOIN stock_location sls ON sm.location_id = sls.id
            INNER JOIN stock_location sld ON sm.location_dest_id = sld.id
            LEFT JOIN stock_production_lot spl ON sm.prodlot_id = spl.id
            WHERE sm.state = 'done'
              AND sls.usage NOT IN ('internal')
              AND sld.usage IN ('internal')
              AND sm.company_id IN ($P!{COMPANY_IDS})
              AND sm.product_id IN ($P!{PROD_IDS})
              AND DATE_TRUNC('day', sm.date) < '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}'
            GROUP BY p.id) bb_put_in
      FULL JOIN (-- BB PUT-OUT

                 SELECT p.id AS prod_id,
                        SUM(sm.product_qty) AS qty,
                        SUM((CASE WHEN sm.prodlot_id IS NULL THEN COALESCE(pt.standard_price, 0.0) ELSE COALESCE(spl.cost_price_per_unit, 0.0) END) * sm.product_qty) AS amount
                 FROM stock_move sm
                 INNER JOIN product_product p ON sm.product_id = p.id
                 INNER JOIN product_template pt ON p.product_tmpl_id = pt.id
                 INNER JOIN stock_location sls ON sm.location_id = sls.id
                 INNER JOIN stock_location sld ON sm.location_dest_id = sld.id
                 LEFT JOIN stock_production_lot spl ON sm.prodlot_id = spl.id
                 WHERE sm.state = 'done'
                   AND sls.usage = 'internal'
                   AND sld.usage NOT IN ('internal')
                   AND sm.company_id IN ($P!{COMPANY_IDS})
                   AND sm.product_id IN ($P!{PROD_IDS})
                   AND DATE_TRUNC('day', sm.date) < '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}'
                 GROUP BY p.id) bb_put_out ON bb_put_in.prod_id = bb_put_out.prod_id) bb
FULL JOIN (-- PUT-IN

           SELECT p.id AS prod_id,
                  SUM(sm.product_qty) AS qty,
                  SUM((CASE WHEN sm.prodlot_id IS NULL THEN COALESCE(pt.standard_price, 0.0) ELSE COALESCE(spl.cost_price_per_unit, 0.0) END) * sm.product_qty) AS amount
           FROM stock_move sm
           INNER JOIN product_product p ON sm.product_id = p.id
           INNER JOIN product_template pt ON p.product_tmpl_id = pt.id
           INNER JOIN stock_location sls ON sm.location_id = sls.id
           INNER JOIN stock_location sld ON sm.location_dest_id = sld.id
           LEFT JOIN stock_production_lot spl ON sm.prodlot_id = spl.id
           WHERE sm.state = 'done'
             AND sls.usage NOT IN ('internal')
             AND sld.usage = 'internal'
             AND sm.company_id IN ($P!{COMPANY_IDS})
             AND sm.product_id IN ($P!{PROD_IDS})
             AND DATE_TRUNC('day', sm.date) BETWEEN '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}' AND '$P!{TO_DATE_2_YR}-$P!{TO_DATE_2_MO}-$P!{TO_DATE_2_DY}'
           GROUP BY p.id) put_in ON bb.prod_id = put_in.prod_id
FULL JOIN (-- PUT-OUT

           SELECT p.id AS prod_id,
                  SUM(sm.product_qty) AS qty,
                  SUM((CASE WHEN sm.prodlot_id IS NULL THEN COALESCE(pt.standard_price, 0.0) ELSE COALESCE(spl.cost_price_per_unit, 0.0) END) * sm.product_qty) AS amount
           FROM stock_move sm
           INNER JOIN product_product p ON sm.product_id = p.id
           INNER JOIN product_template pt ON p.product_tmpl_id = pt.id
           INNER JOIN stock_location sls ON sm.location_id = sls.id
           INNER JOIN stock_location sld ON sm.location_dest_id = sld.id
           LEFT JOIN stock_production_lot spl ON sm.prodlot_id = spl.id
           WHERE sm.state = 'done'
             AND sls.usage = 'internal'
             AND sld.usage NOT IN ('internal')
             AND sm.company_id IN ($P!{COMPANY_IDS})
             AND sm.product_id IN ($P!{PROD_IDS})
             AND DATE_TRUNC('day', sm.date) BETWEEN '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}' AND '$P!{TO_DATE_2_YR}-$P!{TO_DATE_2_MO}-$P!{TO_DATE_2_DY}'
           GROUP BY p.id) put_out ON COALESCE(bb.prod_id, put_in.prod_id) = put_out.prod_id
INNER JOIN
  (SELECT p.id AS prod_id,
          p.name_template AS prod,
          p.default_code AS prod_no,
          pc$P!{PROD_GROUP_LEVEL}.name AS prod_cat
   FROM product_product p
   INNER JOIN product_template pt ON p.product_tmpl_id = pt.id $P!{PROD_CAT_CLAUSE} ) prod_data ON COALESCE(bb.prod_id, put_in.prod_id, put_out.prod_id) = prod_data.prod_id
ORDER BY prod_cat,
         prod_no,
         prod
"""
