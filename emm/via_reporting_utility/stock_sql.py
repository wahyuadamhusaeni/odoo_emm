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

_VIA_STOCK_NORMALIZE_UOM_DEF = '''
BEGIN
    RETURN QUERY SELECT
                  (datum.quantity
                   / (CASE
                      WHEN puc.id = normal_uom_cat.id
                       THEN (pu.factor
                             * (CASE
                                WHEN normal_uom.id IS NULL
                                 THEN 1
                                ELSE normal_uom.factor
                                END))
                      ELSE 1
                      END))::NUMERIC AS qty,
                  normal_uom.id::BIGINT AS uom_id,
                  p.id::BIGINT AS product_id,
                  datum.ids AS ids
                 FROM UNNEST(data) datum
                  INNER JOIN product_uom pu
                   ON pu.id = datum.uom_id
                  INNER JOIN product_uom_categ puc
                   ON puc.id = pu.category_id
                  INNER JOIN product_product p
                   ON datum.product_id = p.id
                  INNER JOIN product_template pt
                   ON p.product_tmpl_id = pt.id
                  LEFT JOIN product_uom normal_uom
                   ON normal_uom.id = pt.uom_id
                  LEFT JOIN product_uom_categ normal_uom_cat
                   ON normal_uom_cat.id = normal_uom.category_id;
END
'''
