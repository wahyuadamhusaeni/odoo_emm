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
    "name" : "VIA module partner enhancement",
    "version" : "1.1",
    "author" : "Vikasa Infinity Anugrah, PT",
    "description" : """
	Module for adding partner's information
	""",
    "website" : "",
    "license" : "GPL-3",
    "category" : "Generic Modules/Accounting",
    "depends" : ["base","via_code_decode"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    "partner_enhancement_data.xml",
                    "partner_view.xml",
                    "security/ir.model.access.csv",
                   ],
    "active":False,
    "installable":True,
}
