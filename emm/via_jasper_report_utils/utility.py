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
    from osv import osv
    from tools.translate import _
except ImportError:
    import openerp
    from openerp import release
    from openerp import pooler
    from openerp.osv import osv
    from openerp.tools.translate import _

_SERVICE_NAME_FIELD = 'report_name'
_REPORT_NAME_FIELD = 'name'
_REPORT_OUTPUT_FIELD = 'jasper_output'
_JASPER_REPORT_INDICATOR_FIELD = 'jasper_report'


def _get_jasper_report_criteria():
    return [(_JASPER_REPORT_INDICATOR_FIELD, '=', True)]


def _get_oerp_report_pool(cr):
    return pooler.get_pool(cr.dbname).get('ir.actions.report.xml')


def get_available_outputs(cr, uid, rpt_name, context=None):
    if not rpt_name:
        return []

    crit = _get_jasper_report_criteria()
    crit.append((_REPORT_NAME_FIELD, '=', rpt_name))

    pool = _get_oerp_report_pool(cr)
    ids = pool.search(cr, uid, crit, order=_REPORT_OUTPUT_FIELD, context=context)
    if len(ids) == 0:
        raise osv.except_osv(_('Error !'),
                             _('Report "%s" does not exist') % rpt_name)

    recs = pool.read(cr, uid, ids, [_REPORT_OUTPUT_FIELD], context=context)

    available_outputs = set()
    for rec in recs:
        available_outputs.add(rec[_REPORT_OUTPUT_FIELD])

    return list(available_outputs)


def get_outputs_selection(object_, cr, uid, context=None):
    if context is None:
        context = {}
    rpt_name = context.get('via_jasper_report_utils.rpt_name', False)
    return [(output, output.upper())
            for output in get_available_outputs(cr, uid, rpt_name, context)]


def get_service_name(cr, uid, rpt_name, rpt_output,
                     service_name_filter=lambda service_names, ctx: service_names,
                     context=None):
    crit = _get_jasper_report_criteria()
    crit.extend([(_REPORT_NAME_FIELD, '=', rpt_name),
                 (_REPORT_OUTPUT_FIELD, '=', rpt_output)])

    pool = _get_oerp_report_pool(cr)
    ids = pool.search(cr, uid, crit, context=context)
    service_names = []
    for rec in pool.read(cr, uid, ids, [_SERVICE_NAME_FIELD], context=context):
        service_names.append(rec[_SERVICE_NAME_FIELD])

    filtered_service_names = service_name_filter(service_names, context)

    filtered_service_names_count = len(filtered_service_names)
    if filtered_service_names_count == 0:
        raise osv.except_osv(_('Error !'),
                             _('Report "%s" with output "%s" has no service name !')
                             % (rpt_name, rpt_output))
    elif filtered_service_names_count > 1:
        raise osv.except_osv(_('Error !'),
                             _('Report "%s" with output "%s" has multiple service names !')
                             % (rpt_name, rpt_output))
    else:
        return filtered_service_names[0]
