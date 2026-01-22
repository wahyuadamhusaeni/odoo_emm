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
    _description = 'Standard VIA wizard for generating Jasper Reports HR'

    _columns = {
        'dept_ids': fields.many2many('hr.department',
                                     'via_report_dept_rel',
                                     'via_report_id',
                                     'dept_id',
                                     string='Departments'),
    }

    _defaults = {
    }

    # Related to dept_ids
    def get_dept_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.dept_ids) == 0:
            _default_domain = form.get_current_domain('dept_ids')
            crit = _default_domain or [('company_id', 'in', [com_id.id for com_id in form.company_ids])]
            return self.pool.get('hr.department').search(cr, uid,
                                                         crit,
                                                         context=context)
        else:
            return [dept_id.id for dept_id in form.dept_ids]

    def get_dept_names(self, cr, uid, ids, when_empty='All', context=None):
        form = self.get_form(cr, uid, ids, context=context)

        return ([dept_id.name for dept_id in form.dept_ids]
                or [when_empty])
    # Related to dept_ids [END]

    def print_report(self, cr, uid, ids, context=None, data=None):
        o = self.browse(cr, uid, ids[0], context=context)
        # Related to dept_ids
        o.add_marshalled_data('DEPT_IDS', ','.join('%d' % dept_id
                                        for dept_id in o.get_dept_ids(context=context)))
        o.add_marshalled_data('DEPT_IDS_INCLUDE_NULL', len(o.dept_ids) == 0 and True or False)
        o.add_marshalled_data('DEPT_NAMES', ', '.join(o.get_dept_names(context=context)))

        return super(via_jasper_report, self).print_report(cr, uid, ids, context=context, data=data)

via_jasper_report()


class wizard(wizard):
    _onchange = {}
    _visibility = []
    _required = []
    _readonly = []
    _attrs = {}
    _domain = {
        'dept_ids': "[('company_id','=',False)]",
    }

    _label = {}

    _defaults = {}

    _selections = {}

    _tree_columns = {
    }
