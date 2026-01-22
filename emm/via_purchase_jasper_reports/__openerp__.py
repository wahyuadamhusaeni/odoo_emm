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

{
    'name': 'VIA Purchase Jasper Reports',
    'version': '1.0',
    'category': 'VIA/Purchase Reports',
    'description': """
    This module contains standar Jasper reports for Purchase functions
    """,
    'author': 'PT. Vikasa Infinity Anugrah',
    'website': 'http://www.infi-nity.com/',
    'depends': [
        'purchase_requisition', # quotation_report
        'via_purchase_enhancements', # quotation_report
        'via_jasper_report_utils',
    ],
    'init_xml': [],
    'update_xml': [
        # Report registration first
        'report/quotation_report/quotation_report_registration.xml',

        # Wizard view, wizard action and menu item last
        'wizard/quotation_report_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
#    'certificate': '0063495605613',
}
