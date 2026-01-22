# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
#    Copyright (c) 2011 - 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

try:
    import release
    from osv import osv, fields
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import osv, fields

import logging


class via_report_orderby(osv.osv):
    _name = "via.report.orderby"
    _description = "VIA Report Order-By Selections"
    __doc__ = ("This is used to store a report name with its corresponding column names available for sorting")
    _order = 'order_dir, column_display_name'
    logger = logging.getLogger('via.report.orderby')

    _columns = {
        'name': fields.text('Report Name', required=True),
        'column_name': fields.text('Column Name', required=True),
        'column_display_name': fields.text('Column Display Name', required=True),
        'order_pos': fields.integer('Position'),
        'order_dir': fields.selection(
            (('asc', 'Ascending'),
            ('desc', 'Descending')),
            'Direction'
        ),
        'default': fields.boolean('Default')
    }
    _defaults = {
        'default': False,
        'order_dir': 'asc',
        'order_pos': 10,
    }

    def orderby_get_ids(self, cr, uid, rpt_name, context=None):
        return self.search(cr, uid, [('name', '=', rpt_name),
                                     ('default', '=', True)],
                           order='order_pos, order_dir',
                           context=context)

via_report_orderby()
