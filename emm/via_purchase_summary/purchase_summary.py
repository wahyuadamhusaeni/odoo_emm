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

from osv import orm, fields
import openerp.addons.decimal_precision as dp
from openerp import tools


class purchase_order_summary(orm.Model):
    _name = "purchase.order.summary"
    _description = "Purchase Order Summary"
    _auto = False

    _columns = {
        'purchase_id': fields.many2one('purchase.order', 'Purchase Order',),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'uom_id': fields.many2one('product.uom', 'UoM', readonly=True),
        'po_qty': fields.float('Ordered (Qty)', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'received_qty': fields.float('Received (Qty)', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'cancelled_qty': fields.float('Cancelled (Qty)', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'requested_received_qty': fields.float('Ordered - Received', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'requested_received_cancel_qty': fields.float('Ordered - Received - Cancelled', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'purchase_order_quantity')
        tools.sql.drop_view_if_exists(cr, 'purchase_order_summary')
        cr.execute("""
        CREATE OR REPLACE VIEW purchase_order_summary AS (
WITH po_dataset AS
  ( SELECT po.id AS po_id,
           pol.product_id AS pol_prd_id,
           prod_uom.id AS prd_uom_id,
           pol.notes AS pol_notes,
           SUM(pol.product_qty * (CASE
               WHEN po_uom_cat.id = prod_uom_cat.id
                   THEN (po_uom.factor * (CASE
                       WHEN prod_uom.id IS NULL
                           THEN 1
                       ELSE prod_uom.factor
                       END))
               ELSE 1
               END)) AS po_qty
   FROM purchase_order po
   JOIN purchase_order_line pol ON pol.order_id = po.id
   LEFT JOIN product_product prd ON prd.id = pol.product_id
   LEFT JOIN product_template prd_tmpl ON prd_tmpl.id = prd.product_tmpl_id
   LEFT JOIN product_uom prod_uom ON prod_uom.id = prd_tmpl.uom_id
   LEFT JOIN product_uom_categ prod_uom_cat ON prod_uom_cat.id = prod_uom.category_id
   LEFT JOIN product_uom po_uom ON po_uom.id = pol.product_uom
   LEFT JOIN product_uom_categ po_uom_cat ON po_uom_cat.id = po_uom.category_id
   GROUP BY po.id,
            pol.product_id,
            pol.notes,
            prod_uom.id
),
     sm_dataset AS
  ( SELECT po.id AS po_id,
           pol.product_id AS pol_prd_id,
           prod_uom.id AS prd_uom_id,
           pol.notes AS pol_notes,
           SUM(COALESCE(sm.product_qty, 0.0) * (CASE
               WHEN is_uom_cat.id = prod_uom_cat.id
                   THEN (is_uom.factor * (CASE
                       WHEN prod_uom.id IS NULL
                           THEN 1
                       ELSE prod_uom.factor
                       END))
               ELSE 1
               END) * (CASE WHEN sp.type = 'out' THEN -1 ELSE 1 END)) AS is_qty
   FROM purchase_order po
   JOIN purchase_order_line pol ON pol.order_id = po.id
   LEFT JOIN product_product prd ON prd.id = pol.product_id
   LEFT JOIN product_template prd_tmpl ON prd_tmpl.id = prd.product_tmpl_id
   LEFT JOIN product_uom prod_uom ON prod_uom.id = prd_tmpl.uom_id
   LEFT JOIN product_uom_categ prod_uom_cat ON prod_uom_cat.id = prod_uom.category_id
   LEFT JOIN stock_move sm ON (pol.id = sm.purchase_line_id
                               AND sm.state IN ('done'))
   LEFT JOIN stock_picking sp ON (sp.id = sm.picking_id)
   LEFT JOIN product_uom is_uom ON (is_uom.id = sm.product_uom)
   LEFT JOIN product_uom_categ is_uom_cat ON is_uom_cat.id = is_uom.category_id
   LEFT JOIN product_uom po_uom ON po_uom.id = pol.product_uom
   LEFT JOIN product_uom_categ po_uom_cat ON po_uom_cat.id = po_uom.category_id
   GROUP BY po.id,
            pol.product_id,
            pol.notes,
            prod_uom.id
),
     cancel_sm_dataset AS
  ( SELECT po.id AS po_id,
           pol.product_id AS pol_prd_id,
           prod_uom.id AS prd_uom_id,
           pol.notes AS pol_notes,
           SUM(COALESCE(sm.product_qty, 0.0) * (CASE
               WHEN is_uom_cat.id = prod_uom_cat.id
                   THEN (is_uom.factor * (CASE
                       WHEN prod_uom.id IS NULL
                           THEN 1
                       ELSE prod_uom.factor
                       END))
               ELSE 1
               END) * (CASE WHEN sp.type = 'out' THEN -1 ELSE 1 END)) AS cancel_qty
   FROM purchase_order po
   JOIN purchase_order_line pol ON pol.order_id = po.id
   LEFT JOIN product_product prd ON prd.id = pol.product_id
   LEFT JOIN product_template prd_tmpl ON prd_tmpl.id = prd.product_tmpl_id
   LEFT JOIN product_uom prod_uom ON prod_uom.id = prd_tmpl.uom_id
   LEFT JOIN product_uom_categ prod_uom_cat ON prod_uom_cat.id = prod_uom.category_id
   LEFT JOIN stock_move sm ON (pol.id = sm.purchase_line_id
                               AND sm.state IN ('cancel'))
   LEFT JOIN stock_picking sp ON (sp.id = sm.picking_id)
   LEFT JOIN product_uom is_uom ON (is_uom.id = sm.product_uom)
   LEFT JOIN product_uom_categ is_uom_cat ON is_uom_cat.id = is_uom.category_id
   LEFT JOIN product_uom po_uom ON po_uom.id = pol.product_uom
   LEFT JOIN product_uom_categ po_uom_cat ON po_uom_cat.id = po_uom.category_id
   GROUP BY po.id,
            pol.product_id,
            pol.notes,
            prod_uom.id
)
SELECT (row_number() OVER ())::INTEGER AS id,
       po.po_id AS purchase_id,
       po.pol_prd_id AS product_id,
       po.prd_uom_id AS uom_id,
       po.po_qty AS po_qty,
       sm.is_qty AS received_qty,
       csm.cancel_qty AS cancelled_qty,
       po.po_qty - sm.is_qty AS requested_received_qty,
       po.po_qty - sm.is_qty - csm.cancel_qty AS requested_received_cancel_qty
FROM po_dataset po
LEFT JOIN sm_dataset sm ON (po.po_id = sm.po_id
                         AND COALESCE(po.pol_prd_id, -1) = COALESCE(sm.pol_prd_id, -1)
                         AND COALESCE(po.prd_uom_id, -1) = COALESCE(sm.prd_uom_id, -1)
                         AND COALESCE(po.pol_notes, '') = COALESCE(sm.pol_notes, ''))
LEFT JOIN cancel_sm_dataset csm ON (po.po_id = csm.po_id
                         AND COALESCE(po.pol_prd_id, -1) = COALESCE(csm.pol_prd_id, -1)
                         AND COALESCE(po.prd_uom_id, -1) = COALESCE(csm.prd_uom_id, -1)
                         AND COALESCE(po.pol_notes, '') = COALESCE(csm.pol_notes, ''))
        )""")
