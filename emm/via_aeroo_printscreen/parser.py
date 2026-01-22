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

from report_aeroo_printscreen import parser


class Parser(parser.Parser):
    def __init__(self, cr, uid, name, context):
        # The 2 lines added mimicing the approach done by/in ps_list.py (OpenERP Server)
        self.context = {}
        self.groupby = []
        super(Parser, self).__init__(cr, uid, name, context)

    def _parse_node(self, root_node):
        result = []
        for node in root_node:
            field_name = node.get('name')

            # Check if the tag has invisible attribute 'turned on'
            if not eval(str(node.attrib.get('invisible', False)), {'context': self.context}):
                if node.tag == 'field':
                    # Check if the tag is accessible to the user (i.e. the user belonging to the group given access to the column/field)
                    if field_name in self.groupby:
                        continue
                    # Add (append) the field name as to be 'print screen-ed'
                    result.append(field_name)
                else:
                    # Recursively process the (non-field) node and concatenate the resulting list of field name(s)
                    result.extend(self._parse_node(node))
        return result
