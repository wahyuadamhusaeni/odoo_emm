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

inventory_sql = lambda: """
SELECT prod_data.prod AS prod,
       prod_data.uom AS prod_uom,
       prod_data.weight AS prod_weight,
       stock_rule.min AS prod_stock_min,
       location_data.complete_name AS prod_location,
       SUM(COALESCE(prod_data.weight, 1) * COALESCE(t.prod_stock_bb, 0.0)) AS prod_stock_bb,
       SUM(COALESCE(prod_data.weight, 1) * COALESCE(t.prod_stock_in, 0.0)) AS prod_stock_in,
       SUM(COALESCE(prod_data.weight, 1) * COALESCE(t.prod_stock_out_ext, 0.0)) AS prod_stock_out_ext,
       SUM(COALESCE(prod_data.weight, 1) * COALESCE(t.prod_stock_out_int, 0.0)) AS prod_stock_out_int,
       SUM(COALESCE(prod_data.weight, 1) * (COALESCE(t.prod_stock_bb, 0.0) + COALESCE(t.prod_stock_in, 0.0) - COALESCE(t.prod_stock_out_ext, 0.0) - COALESCE(t.prod_stock_out_int, 0.0))) AS prod_stock_eb,
       prod_data.prod_cat AS prod_cat
FROM (-- Combining BB, PUT-IN, PUT-OUT-EXT, and PUT-OUT-INT
      SELECT COALESCE(t.prod_id, put_out_int.prod_id) AS prod_id,
             COALESCE(t.location_id, put_out_int.location_id) AS location_id,
             t.prod_stock_bb AS prod_stock_bb,
             t.prod_stock_in AS prod_stock_in,
             t.prod_stock_out_ext AS prod_stock_out_ext,
             COALESCE(put_out_int.qty, 0.0) AS prod_stock_out_int
      FROM (-- Combining BB, PUT-IN, and PUT-OUT-EXT
            SELECT COALESCE(t.prod_id, put_out_ext.prod_id) AS prod_id,
                   COALESCE(t.location_id, put_out_ext.location_id) AS location_id,
                   t.prod_stock_bb AS prod_stock_bb,
                   t.prod_stock_in AS prod_stock_in,
                   COALESCE(put_out_ext.qty, 0.0) AS prod_stock_out_ext
            FROM (-- Combining BB and PUT-IN
                  SELECT COALESCE(bb.prod_id, put_in.prod_id) AS prod_id,
                         COALESCE(bb.location_id, put_in.location_id) AS location_id,
                         COALESCE(bb.qty, 0.0) AS prod_stock_bb,
                         COALESCE(put_in.qty, 0.0) AS prod_stock_in
                  FROM (-- BB
                        SELECT COALESCE(bb_put_in.prod_id, bb_put_out.prod_id) AS prod_id,
                               COALESCE(bb_put_in.location_id, bb_put_out.location_id) AS location_id,
                               COALESCE(bb_put_in.qty, 0.0) - COALESCE(bb_put_out.qty, 0.0) AS qty
                        FROM (-- BB PUT-IN
                              SELECT p.id AS prod_id,
                                     sld.id AS location_id,
                                     SUM(sm.product_qty) AS qty
                              FROM stock_move sm
                              INNER JOIN product_product p ON sm.product_id = p.id
                              INNER JOIN stock_location sls ON sm.location_id = sls.id
                              INNER JOIN stock_location sld ON sm.location_dest_id = sld.id
                              WHERE sm.state = 'done'
                                AND sld.id IN ($P!{LOCATION_IDS})
                                AND sm.company_id IN ($P!{COMPANY_IDS})
                                AND sm.product_id IN ($P!{PROD_IDS})
                                AND DATE_TRUNC('day', sm.date) < '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}'
                              GROUP BY p.id,
                                       sld.id) bb_put_in
                        FULL JOIN (-- BB PUT-OUT
                                   SELECT p.id AS prod_id,
                                          sls.id AS location_id,
                                          SUM(sm.product_qty) AS qty
                                   FROM stock_move sm
                                   INNER JOIN product_product p ON sm.product_id = p.id
                                   INNER JOIN stock_location sls ON sm.location_id = sls.id
                                   INNER JOIN stock_location sld ON sm.location_dest_id = sld.id
                                   WHERE sm.state = 'done'
                                     AND sls.id IN ($P!{LOCATION_IDS})
                                     AND sm.company_id IN ($P!{COMPANY_IDS})
                                     AND sm.product_id IN ($P!{PROD_IDS})
                                     AND DATE_TRUNC('day', sm.date) < '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}'
                                   GROUP BY p.id,
                                            sls.id) bb_put_out ON (bb_put_in.prod_id,
                                                                   bb_put_in.location_id) = (bb_put_out.prod_id,
                                                                                             bb_put_out.location_id)) bb
                  FULL JOIN (-- PUT-IN
                             SELECT p.id AS prod_id,
                                    sld.id AS location_id,
                                    SUM(sm.product_qty) AS qty
                             FROM stock_move sm
                             INNER JOIN product_product p ON sm.product_id = p.id
                             INNER JOIN stock_location sls ON sm.location_id = sls.id
                             INNER JOIN stock_location sld ON sm.location_dest_id = sld.id
                             WHERE sm.state = 'done'
                               AND sld.id IN ($P!{LOCATION_IDS})
                               AND sm.company_id IN ($P!{COMPANY_IDS})
                               AND sm.product_id IN ($P!{PROD_IDS})
                               AND DATE_TRUNC('day', sm.date) BETWEEN '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}' AND '$P!{TO_DATE_2_YR}-$P!{TO_DATE_2_MO}-$P!{TO_DATE_2_DY}'
                             GROUP BY p.id,
                                      sld.id) put_in ON (bb.prod_id,
                                                         bb.location_id) = (put_in.prod_id,
                                                                            put_in.location_id)) t
            FULL JOIN (-- PUT-OUT-EXT
                       SELECT p.id AS prod_id,
                              sls.id AS location_id,
                              SUM(sm.product_qty) AS qty
                       FROM stock_move sm
                       INNER JOIN product_product p ON sm.product_id = p.id
                       INNER JOIN stock_location sls ON sm.location_id = sls.id
                       INNER JOIN stock_location sld ON sm.location_dest_id = sld.id
                       WHERE sm.state = 'done'
                         AND sls.id IN ($P!{LOCATION_IDS})
                         AND sld.usage IN ('supplier',
                                           'customer')
                         AND sm.company_id IN ($P!{COMPANY_IDS})
                         AND sm.product_id IN ($P!{PROD_IDS})
                         AND DATE_TRUNC('day', sm.date) BETWEEN '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}' AND '$P!{TO_DATE_2_YR}-$P!{TO_DATE_2_MO}-$P!{TO_DATE_2_DY}'
                       GROUP BY p.id,
                                sls.id) put_out_ext ON (t.prod_id,
                                                        t.location_id) = (put_out_ext.prod_id,
                                                                          put_out_ext.location_id)) t
      FULL JOIN (-- PUT-OUT-INT
                 SELECT p.id AS prod_id,
                        sls.id AS location_id,
                        SUM(sm.product_qty) AS qty
                 FROM stock_move sm
                 INNER JOIN product_product p ON sm.product_id = p.id
                 INNER JOIN stock_location sls ON sm.location_id = sls.id
                 INNER JOIN stock_location sld ON sm.location_dest_id = sld.id
                 WHERE sm.state = 'done'
                   AND sls.id IN ($P!{LOCATION_IDS})
                   AND sld.usage NOT IN ('supplier',
                                         'customer')
                   AND sm.company_id IN ($P!{COMPANY_IDS})
                   AND sm.product_id IN ($P!{PROD_IDS})
                   AND DATE_TRUNC('day', sm.date) BETWEEN '$P!{FROM_DATE_2_YR}-$P!{FROM_DATE_2_MO}-$P!{FROM_DATE_2_DY}' AND '$P!{TO_DATE_2_YR}-$P!{TO_DATE_2_MO}-$P!{TO_DATE_2_DY}'
                 GROUP BY p.id,
                          sls.id) put_out_int ON (t.prod_id,
                                                  t.location_id) = (put_out_int.prod_id,
                                                                    put_out_int.location_id)) t
INNER JOIN (-- Product row (1 row when net weight is zero, 2 rows otherwise)
 (-- Original UoM
  SELECT p.id AS prod_id,
         p.name_template AS prod,
         pu.name AS uom,
         NULL AS weight,
         pc$P!{PROD_GROUP_LEVEL}.name AS prod_cat
  FROM product_product p
  INNER JOIN product_template pt ON p.product_tmpl_id = pt.id
  INNER JOIN product_uom pu ON pt.uom_id = pu.id $P!{PROD_CAT_CLAUSE})
  UNION ALL
  (-- For kg line
   SELECT p.id AS prod_id,
          p.name_template AS prod,
          'kg' AS uom,
          pt.weight_net AS weight,
          pc$P!{PROD_GROUP_LEVEL}.name AS prod_cat
   FROM product_product p
   INNER JOIN product_template pt ON p.product_tmpl_id = pt.id $P!{PROD_CAT_CLAUSE}
   WHERE pt.weight_net IS NOT NULL
     AND pt.weight_net > 0.0)) prod_data ON t.prod_id = prod_data.prod_id
INNER JOIN stock_location location_data ON t.location_id = location_data.id
LEFT JOIN
  (SELECT p.id AS prod_id,
          sl.id AS location_id,
          MAX(swo.product_min_qty) AS min
   FROM product_product p
   INNER JOIN stock_warehouse_orderpoint swo ON p.id = swo.product_id
   INNER JOIN stock_location sl ON swo.location_id = sl.id
   GROUP BY p.id,
            sl.id) stock_rule ON (t.prod_id,
                                  t.location_id) = (stock_rule.prod_id,
                                                    stock_rule.location_id)
GROUP BY prod_data.prod,
         prod_data.uom,
         prod_data.weight,
         stock_rule.min,
         location_data.complete_name,
         prod_data.prod_cat
ORDER BY prod_cat,
         prod,
         prod_location
"""
