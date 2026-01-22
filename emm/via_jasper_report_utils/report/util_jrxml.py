#!/usr/bin/env python

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
import sys
import ast
import math
from os import path
from glob import glob
import re

JRXML_NS = {
    'jr': 'http://jasperreports.sourceforge.net/jasperreports',
    'jrc': 'http://jasperreports.sourceforge.net/jasperreports/components',
}

JR = '{http://jasperreports.sourceforge.net/jasperreports}'

ELEMENTS_HAVING_REPORT_ELEMENT = [
    'rectangle', 'ellipse', 'image', 'staticText', 'textField',
    'subReport', 'chart', 'crosstab', 'frame', 'componentElement',
    'genericElement', 'break', 'line',
]

DUPLICABLE_ELEMENTS = ELEMENTS_HAVING_REPORT_ELEMENT

ELEMENTS_HAVING_PRINT_WHEN_EXPRESSION = [
    'band'
] + ELEMENTS_HAVING_REPORT_ELEMENT

BOX_ORDER = dict((name, idx)
                 for idx, name in enumerate(['pen',
                                             'topPen',
                                             'leftPen',
                                             'bottomPen',
                                             'rightPen']))
STYLE_ORDER = dict((name, idx)
                   for idx, name in enumerate(['pen',
                                               'box']))

PAPER_ORIENTATION = ('landscape', 'portrait')

SIZE_REGISTRY = {
    # Paper size: (portraitPageWidth, portraitPageHeight)
    'A3': (842, 1190),
    'A4': (595, 842),
}

JR_SEQUENCES = {
    'jasperReport': (
        'property',
        'import',
        'template',
        'reportFont',
        'style',
        'subDataset',
        'scriptlet',
        'parameter',
        'queryString',
        'field',
        'sortField',
        'variable',
        'filterExpression',
        'group',
        'background',
        'title',
        'pageHeader',
        'columnHeader',
        'detail',
        'columnFooter',
        'pageFooter',
        'lastPageFooter',
        'summary',
        'noData',
    ),
    'crosstab': (
        'reportElement',
        'box',
        'crosstabParameter',
        'parametersMapExpression',
        'crosstabDataset',
        'crosstabHeaderCell',
        'rowGroup',
        'columnGroup',
        'measure',
        'crosstabCell',
        'whenNoDataCell',
    ),
}

def import_plugins(py_files_prefix, trunk_pattern, entry_tuple_expr):
    result = []

    _mod_dir = path.dirname(path.realpath(__file__))
    _mod_search_paths = [_mod_dir]
    for mod_name in map(lambda file_path: path.basename(file_path)[:-3],
                        glob(path.join(_mod_dir, py_files_prefix + '*.py'))):
        canonical_mod_name = (__package__ and (__package__ + '.') or '') + mod_name
        exec ('%s = __import__("%s")'
              % (canonical_mod_name.split('.')[0],
                 canonical_mod_name)) in globals(), locals()

        trunk = re.sub(trunk_pattern, r'\1', mod_name)
        result.append((mod_name, trunk))

    result.sort()

    return [eval(entry_tuple_expr % {'mod_name': mod_name, 'trunk': trunk})
            for (mod_name, trunk) in result]

def get_style_down_chain_names(jrxml, root_style_name, stopper=(lambda node: False)):
    result = set()
    if stopper(jrxml.getroot().xpath("./jr:style[@name='%s']" % root_style_name,
                                     namespaces=JRXML_NS)[0]):
        return result

    result.add(root_style_name)
    for name in map(lambda style: style.get('name'),
                    jrxml.getroot().xpath("./jr:style[@style='%s']" % root_style_name,
                                          namespaces=JRXML_NS)):
        result = result | get_style_down_chain_names(jrxml, name, stopper=stopper)
    return result

def get_style_up_chain_names(jrxml, root_style_name, stopper=(lambda node: False)):
    result = set()
    up_style = jrxml.getroot().xpath("./jr:style[@name='%s']" % root_style_name,
                                     namespaces=JRXML_NS)[0]
    if stopper(up_style):
        return result

    result.add(root_style_name)
    if up_style.get('style', None) is not None:
        result = result | get_style_up_chain_names(jrxml,
                                                   up_style.get('style'),
                                                   stopper=stopper)
    return result

def tag_name(tag):
    return tag.split('}')[1]

def insert_element(parent, element):
    sequence_name = tag_name(parent.tag)
    try:
        sequence = JR_SEQUENCES[sequence_name]
    except KeyError:
        raise Exception('Please develop JR_SEQUENCES further:'
                        ' %s is not sequenced yet' % sequence_name)

    element_name = tag_name(element.tag)
    try:
        element_idx = sequence.index(element_name)
    except ValueError:
        raise Exception('Tag %s is not in JR_SEQUENCES[%s]'
                        % (element_name, sequence_name))

    already_inserted = False
    sequence_bottom_half = sequence[element_idx + 1:]
    for tag in sequence_bottom_half:
        anchor_point = parent.xpath("./jr:%s[position()=1]" % tag, namespaces=JRXML_NS)
        if len(anchor_point):
            anchor_point[0].addprevious(element)
            already_inserted = True
            break
    if not already_inserted:
        sequence_first_half = sequence[:element_idx]
        sequence_first_half.reverse()
        for tag in sequence_first_half:
            anchor_point = parent.xpath("./jr:%s[last()]" % tag, namespaces=JRXML_NS)
            if len(anchor_point):
                anchor_point[0].addnext(detail_band)
                break

def parse_exp_file(exp_file_path):
    exp_file = open(exp_file_path)
    exp_file_str = exp_file.read()
    return ast.literal_eval(exp_file_str)

def reorder_elements(container, order):
    container[:] = sorted(container, key=lambda e: order[tag_name(e.tag)])

def component_get_str(component, attr):
    return component.xpath('jr:reportElement', namespaces=JRXML_NS)[0].get(attr)

def component_set_str(component, attr, val):
    component.xpath('jr:reportElement', namespaces=JRXML_NS)[0].set(attr, val)

def component_get_int(component, attr):
    return int(component_get_str(component, attr))

def component_set_int(component, attr, val):
    component_set_str(component, attr, '%d' % val)

def set_x(component, x):
    component_set_int(component, 'x', x)

def get_x(component):
    return component_get_int(component, 'x')

def set_y(component, y):
    component_set_int(component, 'y', y)

def get_y(component):
    return component_get_int(component, 'y')

def set_width(component, width):
    component_set_int(component, 'width', width)

def set_height(component, height):
    component_set_int(component, 'height', height)

def get_width(component):
    return component_get_int(component, 'width')

def get_height(component):
    return component_get_int(component, 'height')

def get_margin(component, which):
    which += 'Margin'
    return component_get_int(component, which)

def get_value(component):
    component_tag = tag_name(component.tag)
    if component_tag not in ('staticText', 'textField', 'frame'):
        raise Exception('get_value is not applicable to %s' % component_tag)
    value = component.xpath('jr:text|jr:textFieldExpression',
                            namespaces=JRXML_NS)
    if value:
        return value[0].text
    else:
        return ''

def get_resource_dir():
    return path.dirname(path.realpath(__file__))

def write_jrxml(jrxml, output_file_path=None, dry_run=False):
    jrxml_file_name = jrxml.getroot().get('name') + '.jrxml'
    if output_file_path is None:
        output_file_path = jrxml_file_name
    if path.isdir(output_file_path):
        output_file_path = path.join(output_file_path, jrxml_file_name)
    if not dry_run:
        jrxml.write(output_file_path, encoding='UTF-8', xml_declaration=True,
                    pretty_print=True)
    return output_file_path
