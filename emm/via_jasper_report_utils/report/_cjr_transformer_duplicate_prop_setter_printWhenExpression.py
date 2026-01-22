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

from lxml import etree
from util_jrxml import tag_name, ELEMENTS_HAVING_PRINT_WHEN_EXPRESSION, \
    ELEMENTS_HAVING_REPORT_ELEMENT, JRXML_NS

def _set_prop_printWhenExpression(element, value):
    if tag_name(element.tag) not in ELEMENTS_HAVING_PRINT_WHEN_EXPRESSION:
        raise Exception('printWhenExpression cannot be set on %s'
                        % tag_name(element.tag))

    xpath_expr = './jr:printWhenExpression'
    print_when_expr_parent = element
    if tag_name(element.tag) in ELEMENTS_HAVING_REPORT_ELEMENT:
        xpath_expr = xpath_expr[:2] + 'jr:reportElement/' + xpath_expr[2:]
        print_when_expr_parent = element.xpath('./jr:reportElement',
                                               namespaces=JRXML_NS)[0]

    print_when_exprs = element.xpath(xpath_expr, namespaces=JRXML_NS)
    if len(print_when_exprs) == 0:
        print_when_expr = etree.SubElement(print_when_expr_parent,
                                           JR + 'printWhenExpression')
    else:
        print_when_expr = print_when_exprs[0]

    print_when_expr.text = etree.CDATA(value)
