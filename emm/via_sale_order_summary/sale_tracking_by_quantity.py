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

# from openerp import tools
from osv import orm, fields
import openerp.addons.decimal_precision as dp
from openerp import tools


class sale_tracking_by_quantity(orm.Model):
    _name = "sale.tracking.by.quantity"
    _description = "Sale Tracking by Quantity"
    _auto = False

    _columns = {
        'order_id': fields.many2one('sale.order', 'SO ID'),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'uom_id': fields.many2one('product.uom', 'UoM', readonly=True),
        'so_qty': fields.float('Requested (Qty)', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'delivery_qty': fields.float('Delivered (Qty)', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'cancel_qty': fields.float('Cancelled (Qty)', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'outstand_done': fields.float('Requested - Delivered', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'outstand_done_cancel': fields.float('Requested - Delivered - Cancelled', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_tracking_by_quantity')
        cr.execute("""CREATE OR REPLACE VIEW sale_tracking_by_quantity AS (
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
           SUM(COALESCE(sm_cancel.product_qty, 0.0) * (CASE
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
   LEFT JOIN stock_move sm_cancel ON (sol.id = sm_cancel.sale_line_id
                               AND sm_cancel.state IN ('cancel'))
   LEFT JOIN stock_picking sp ON (sp.id = sm_cancel.picking_id)
   LEFT JOIN product_uom do_uom ON (do_uom.id = sm_cancel.product_uom)
   LEFT JOIN product_uom_categ do_uom_cat ON (do_uom_cat.id = do_uom.category_id)
   LEFT JOIN product_uom so_uom ON (so_uom.id = sol.product_uom)
   LEFT JOIN product_uom_categ so_uom_cat ON (so_uom_cat.id = so_uom.category_id)
   GROUP BY so.id,
            sol.product_id,
            prod_uom.id
)
SELECT CAST(row_number() OVER () AS INT) AS id,
       so.so_id AS order_id,
       so.sol_prd_id AS product_id,
       so.prd_uom_id AS uom_id,
       so.so_qty AS so_qty,
       sm.do_qty AS delivery_qty,
       csm.cancel_qty AS cancel_qty,
       so.so_qty - sm.do_qty AS outstand_done,
       so.so_qty - sm.do_qty - csm.cancel_qty AS outstand_done_cancel
FROM so_dataset so
LEFT JOIN sm_dataset sm ON (so.so_id = sm.so_id
                         AND COALESCE(so.sol_prd_id, -1) = COALESCE(sm.sol_prd_id, -1)
                         AND COALESCE(so.prd_uom_id, -1) = COALESCE(sm.prd_uom_id, -1))
LEFT JOIN cancel_sm_dataset csm ON (so.so_id = csm.so_id
                         AND COALESCE(so.sol_prd_id, -1) = COALESCE(csm.sol_prd_id, -1)
                         AND COALESCE(so.prd_uom_id, -1) = COALESCE(csm.prd_uom_id, -1))
            )""")

sale_tracking_by_quantity()
