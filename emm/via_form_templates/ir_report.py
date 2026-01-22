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

from via_report_webkit.ir_report import via_form_template_mako_parser, via_form_template_webkit_parser, register_report
from report import report_sxw
from osv import osv


class ir_actions_report_xml(osv.osv):
    _inherit = 'ir.actions.report.xml'

    def register_all(self, cursor):
        value = super(ir_actions_report_xml, self).register_all(cursor)

        cursor.execute("SELECT * FROM via_form_templates WHERE active = True")
        records = cursor.dictfetchall()

        for record in records:
            _rpt = self.browse(cursor, record.get('create_uid', False), record.get('act_report_id', False))
            register_report(_rpt.report_name, _rpt.model, _rpt.report_rml, parser=via_form_template_mako_parser, force_parser=True)
        return value

ir_actions_report_xml()
