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

try:
    import release
    from osv import osv
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import osv

from pgsql import create_composite_type, create_plpgsql_proc
from stock_sql import _VIA_STOCK_NORMALIZE_UOM_DEF

class via_reporting_stock(osv.osv):
    _name = 'via.reporting.stock'
    _auto = False
    _description = 'VIA Reporting Utility For Stock'

    def _auto_init(self, cr, context=None):
        super(via_reporting_stock, self)._auto_init(cr, context=context)
        create_composite_type(cr, 'via_stock_normalized_uom',
                              [('quantity', 'NUMERIC'),
                               ('uom_id', 'BIGINT'),
                               ('product_id', 'BIGINT'),
                               ('ids', 'BIGINT[]')])
        create_plpgsql_proc(cr, 'via_stock_normalize_uom',
                            [('IN', 'data', 'VIA_STOCK_NORMALIZED_UOM[]')],
                            'SETOF VIA_STOCK_NORMALIZED_UOM',
                            _VIA_STOCK_NORMALIZE_UOM_DEF)
via_reporting_stock()
