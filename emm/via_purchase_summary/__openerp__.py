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
    "name": "Purchase Order Summary",
    "version": "1.0",
    "author": "Vikasa Infinity Anugrah, PT",
    "category": "Purchase Management",
    "description": """
    This module provides a summary tab in the Purchase Order view depciting the current status
	of payment and deliveries.
    """,
    "website": "http://www.infi-nity.com",
    "license": "GPL-3",
    "depends": [
        "purchase",
        "via_purchase_enhancements",
    ],
    "init_xml": [
    ],
    'update_xml': [
        "purchase_order_summary_view.xml",
        "purchase_view.xml",
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
