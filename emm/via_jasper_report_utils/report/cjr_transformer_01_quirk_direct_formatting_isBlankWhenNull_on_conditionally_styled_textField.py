###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
#
###############################################################################

from copy import deepcopy
from lxml import etree
import re
from util_jrxml import JRXML_NS, JR, get_style_down_chain_names, tag_name, \
    get_style_up_chain_names

def transform_jrxml_quirk_direct_formatting_isBlankWhenNull_on_conditionally_styled_textField_cmd_opts(parser):
    parser.add_option('', '--no-direct-formatting-isBlankWhenNull', dest='direct_formatting_isBlankWhenNull', action='store_false',
                      default=True, help='Preprocess by setting isBlankWhenNull on conditionally styled textFields')

    def options_parser(options):
        pass
    return options_parser

def transform_jrxml_quirk_direct_formatting_isBlankWhenNull_on_conditionally_styled_textField(jrxml, jrxml_opts):
    if not jrxml_opts.direct_formatting_isBlankWhenNull:
        return

    root = jrxml.getroot()

    conditional_style_names = set(map(lambda e: e.getparent().get('name'),
                                      root.xpath("jr:style/jr:conditionalStyle",
                                                 namespaces=JRXML_NS)))

    if len(conditional_style_names) == 0:
        return

    xpath_expr = []
    for conditional_style_name in conditional_style_names:
        xpath_expr.append("//jr:textField[not (@isBlankWhenNull='true')]/jr:reportElement[@style='%(style_name)s']/.."
                          "|//jr:textField[not (@isBlankWhenNull='true')]/jr:reportElement[starts-with(@style, '%(style_name)s.')]/.."
                          % {'style_name': conditional_style_name})
    xpath_expr = '|'.join(xpath_expr)

    for text_field in root.xpath(xpath_expr, namespaces=JRXML_NS):
        text_field.set('isBlankWhenNull', 'true')
