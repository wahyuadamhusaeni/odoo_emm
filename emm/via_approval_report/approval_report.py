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

from openerp.osv import fields, orm


class report_xml(orm.Model):
    _inherit = 'ir.actions.report.xml'

    def _report_sxw(self, cursor, user, ids, name, arg, context=None):
        for report in self.browse(cursor, user, ids, context=context):
            report_name = report.report_name
        self.pool.get('approval.list').hook_validation(cursor, user, context.get('active_ids', []), report_name, context=context)
        return super(report_xml, self)._report_sxw(cursor, user, ids, name, arg, context=context)

    _columns = {
        'report_sxw': fields.function(_report_sxw, type='char', string='SXW Path'),
    }

report_xml()
