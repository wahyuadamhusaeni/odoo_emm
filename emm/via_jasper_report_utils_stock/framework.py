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
    import pooler
    from osv import osv, fields, orm
    if release.major_version == '6.1':
        import openerp.modules as addons
    else:
        import addons
    from via_jasper_report_utils import utility
    from tools.translate import _
    from tools import DEFAULT_SERVER_DATE_FORMAT
except ImportError:
    import openerp
    from openerp import release
    from openerp import pooler
    from openerp.osv import osv, fields, orm
    import openerp.modules as addons
    from openerp.addons.via_jasper_report_utils import utility
    from openerp.tools.translate import _
    from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

import calendar
from lxml import etree
import re
import os
import glob
from datetime import date
from datetime import datetime
from copy import deepcopy
from via_reporting_utility.pgsql import list_to_pgTable
from via_jasper_report_utils.framework import register_report_wizard, wizard


class via_jasper_report(osv.osv_memory):
    _inherit = 'via.jasper.report'
    _description = 'Standard VIA wizard for generating Jasper Reports Stock'

    _columns = {
        'location_ids': fields.many2many('stock.location',
                                         'via_report_location_rel',
                                         'via_report_id',
                                         'location_id',
                                         string='Locations'),
        'prod_lot_ids': fields.many2many('stock.production.lot',
                                         'via_report_production_lot_rel',
                                         'via_report_id',
                                         'lot_id',
                                         string='Product Lots'),
        'prod_lot_ids_empty_is_none': fields.boolean('Product Lots When Empty Means None'),
        'prod_lot_ids_2': fields.many2many('stock.production.lot',
                                           'via_report_production_lot_rel_2',
                                           'via_report_id',
                                           'lot_id',
                                           string='Product Lots'),
        'prod_lot_ids_2_empty_is_none': fields.boolean('Product Lots When Empty Means None'),
    }

    _defaults = {
    }

    # Related to location_ids
    def get_location_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.location_ids) == 0:
            _default_domain = form.get_current_domain('location_ids')
            crit = _default_domain or ['|', ('company_id', '=', False), ('company_id', 'in', [com_id.id for com_id in form.company_ids])]
            return self.pool.get('stock.location').search(cr, uid,
                                                          crit,
                                                          context=context)
        else:
            return [location_id.id for location_id in form.location_ids]
    # Related to location_ids [END]

    # Related to prod_lot_ids
    def get_prod_lot_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.prod_lot_ids) == 0:
            if form.prod_lot_ids_empty_is_none:
                return []
            _default_domain = form.get_current_domain('prod_lot_ids')
            crit = _default_domain or [('product_id.company_id', 'in', [com_id.id for com_id in form.company_ids])]
            return self.pool.get('stock.production.lot').search(cr, uid,
                                                                crit,
                                                                context=context)
        else:
            return [prod_lot_id.id for prod_lot_id in form.prod_lot_ids]
    # Related to prod_lot_ids [END]

    # Related to prod_lot_ids_2
    def get_prod_lot_ids_2(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.prod_lot_ids_2) == 0:
            if form.prod_lot_ids_2_empty_is_none:
                return []
            _default_domain = form.get_current_domain('prod_lot_ids_2')
            crit = _default_domain or [('product_id.company_id', 'in', [com_id.id for com_id in form.company_ids])]
            return self.pool.get('stock.production.lot').search(cr, uid,
                                                                crit,
                                                                context=context)
        else:
            return [prod_lot_id_2.id for prod_lot_id_2 in form.prod_lot_ids_2]
    # Related to prod_lot_ids_2 [END]

    def print_report(self, cr, uid, ids, context=None, data=None):
        o = self.browse(cr, uid, ids[0], context=context)
        o.add_marshalled_data('LOCATION_IDS', ', '.join('%d' % location_id
                                     for location_id in o.get_location_ids(context=context) + [0]))

        # Related to prod_lot_ids
        o.add_marshalled_data('PROD_LOT_IDS', ', '.join('%d' % prod_lot_id
                                     for prod_lot_id in o.get_prod_lot_ids(context=context)))
        o.add_marshalled_data('PROD_LOT_IDS_INCLUDE_NULL', len(o.prod_lot_ids) == 0 and True or False)
        o.add_marshalled_data('PROD_LOT_IDS_EMPTY_IS_NONE', o.prod_lot_ids_empty_is_none)

        # Related to prod_lot_ids_2
        o.add_marshalled_data('PROD_LOT_IDS_2', ', '.join('%d' % prod_lot_id_2
                                       for prod_lot_id_2 in o.get_prod_lot_ids_2(context=context)))
        o.add_marshalled_data('PROD_LOT_IDS_2_INCLUDE_NULL', len(o.prod_lot_ids_2) == 0 and True or False)
        o.add_marshalled_data('PROD_LOT_IDS_2_EMPTY_IS_NONE', o.prod_lot_ids_2_empty_is_none)

        return super(via_jasper_report, self).print_report(cr, uid, ids, context=context, data=data)

via_jasper_report()


class wizard(wizard):
    _onchange = {}
    _visibility = []
    _required = []
    _readonly = []
    _attrs = {}
    _domain = {
        'location_ids': "[('company_id', '=', False), ('usage', '=', 'internal')]",
        'prod_lot_ids': "[('product_id.product_tmpl_id.company_id', '=', False)]",
        'prod_lot_ids_2': "[('product_id.product_tmpl_id.company_id', '=', False)]",
    }

    _label = {}

    _defaults = {}

    _selections = {}

    _tree_columns = {
        'location_ids': ['name'],
        'prod_lot_ids': ['name'],
        'prod_lot_ids_2': ['name'],
    }
