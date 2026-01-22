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

from openerp import tools
from osv import orm, fields
import openerp.addons.decimal_precision as dp


class sr_summary(orm.Model):
    _name = "sr.summary"
    _description = "Service Request Summary"
    _auto = False

    _columns = {
        'product': fields.char('Product', readonly=True),
        'origin': fields.char('Origin', readonly=True),
        'requested': fields.float('Requested', readonly=True, digits_compute=dp.get_precision('Product Unit of Measure')),
        'request_to_be_followed_up': fields.float('Request To Be Followed Up', readonly=True, digits_compute=dp.get_precision('Product Unit of Measure')),
        'reserved_on_pickup_area': fields.float('Reserved On Pickup Area', readonly=True, digits_compute=dp.get_precision('Product Unit of Measure')),
        'technician_responsibility': fields.float('Technician Responsibility', readonly=True, digits_compute=dp.get_precision('Product Unit of Measure')),
        'consumed_by_costumer': fields.float('Consume By Costumer', readonly=True, digits_compute=dp.get_precision('Product Unit of Measure')),
        'returned_to_warehouse': fields.float('Returned To Warehouse', readonly=True, digits_compute=dp.get_precision('Product Unit of Measure')),
    }

    def init(self, cr):
        cr.execute("""
            CREATE OR REPLACE view sr_summary as (
                SELECT
                  CAST(row_number() OVER () AS INT) AS id,
                  product AS product,
                  origin AS origin,
                  COALESCE(SUM(CASE WHEN picking_svc_type = 'request' AND state != 'cancel' THEN qty END),0) AS requested,
                  COALESCE(SUM(CASE WHEN picking_svc_type = 'request' AND state != 'done' AND state != 'cancel' THEN qty END),0) AS request_to_be_followed_up,
                  COALESCE(SUM(CASE WHEN picking_svc_type = 'request' AND state = 'done' THEN qty END),0)
                    + COALESCE(SUM(CASE WHEN picking_svc_type = 'return' AND state = 'done' AND to_location = 'pickup' THEN qty END),0)
                    - COALESCE(SUM(CASE WHEN picking_svc_type = 'pickup' AND state != 'cancel' THEN qty END),0)
                    - COALESCE(SUM(CASE WHEN picking_svc_type = 'return' AND state != 'cancel' AND from_location = 'pickup' THEN qty END),0) AS reserved_on_pickup_area,
                  COALESCE(SUM(CASE WHEN picking_svc_type = 'pickup' AND state != 'cancel' THEN qty END),0)
                    + COALESCE(SUM(CASE WHEN picking_svc_type = 'return' AND state = 'done' AND to_location = 'transit' THEN qty END),0)
                    - COALESCE(SUM(CASE WHEN picking_svc_type = 'consume' AND state != 'cancel' THEN qty END),0)
                    - COALESCE(SUM(CASE WHEN picking_svc_type = 'return' AND state != 'cancel' AND from_location = 'transit' THEN qty END),0) AS technician_responsibility,
                  COALESCE(SUM(CASE WHEN picking_svc_type = 'consume' AND state != 'cancel' THEN qty END),0) AS consumed_by_costumer,
                  COALESCE(SUM(CASE WHEN picking_svc_type = 'return' AND state != 'cancel' AND to_location = 'spareparts' THEN qty END),0) AS returned_to_warehouse
                FROM (
                  SELECT
                    sm.origin,
                    sm.name AS product,
                    SUM (sm.product_qty) AS qty,
                    pu.name,
                    sm.product_id,
                    sp.picking_svc_type AS picking_svc_type,
                    sm.state AS state,
                    sl.usage_type AS from_location,
                    sld.usage_type AS to_location
                  FROM stock_move sm
                  INNER JOIN stock_picking sp ON (sp.id = sm.picking_id)
                  INNER JOIN product_uom pu ON (pu.id = sm.product_uom)
                  LEFT JOIN stock_location sl ON (sm.location_id = sl.id)
                  LEFT JOIN stock_location sld ON (sm.location_dest_id = sld.id)
                  GROUP BY
                    sm.origin,
                    sm.name,
                    pu.name,
                    sp.picking_svc_type,
                    sm.state,
                    sm.product_id,
                    sl.usage_type,
                    sld.usage_type
                  ORDER BY
                    sm.name
                  ) as base
                GROUP BY
                  product_id,
                  product,
                  origin
            )
        """)
sr_summary()
