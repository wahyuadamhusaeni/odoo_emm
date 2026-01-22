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

{
    "name": "Generic Form Templates",
    "version": "1.3",
    "author": "Vikasa Infinity Anugrah, PT",
    "category": "Generic Modules/Reporting",
    "description": """
    This module provides a means to produce a configurable forms with simple rendering,
    in which only the functions provided by via_form_template_mako_parser in via_report_webkit
    module is available.

    It is meant to be expandable using various Rendering engines, but currently only
    supports Mako by way of report_webkit module.
    """,
    "website": "http://www.infi-nity.com",
    "license": "GPL-3",
    "depends": [
        "via_report_webkit",
    ],
    "init_xml": [],
    'update_xml': [
        "security/ir.model.access.csv",
        "via_form_templates_view.xml"
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
