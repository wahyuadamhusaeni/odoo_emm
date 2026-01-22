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
    get_style_up_chain_names, insert_element

_SIDE_EFFECT_VAR_NAME = 'CJR_TRANSFORMER_DONT_UNDERLINE_LEADING_SPACE_VAR'

def transform_jrxml_dont_underline_leading_space_cmd_opts(parser):
    parser.add_option('', '--no-dont-underline-leading-space', dest='dont_underline_leading_space', action='store_false',
                      default=True, help='Preprocess by installing Java expression to prevent leading whitespaces from being underlined')

    def options_parser(options):
        pass
    return options_parser

def get_effective_markup_dict(jrxml, parent_name=None, parent_dict=None):
    if parent_dict is None:
        parent_dict = {}
    root = jrxml.getroot()

    result = {}

    for style in root.xpath("./jr:style[%s]"
                            % (parent_name is None and 'not (@style)'
                               or ("@style='%s'" % parent_name)),
                            namespaces=JRXML_NS):
        cond_dict = {}
        cond_dict.update(parent_dict)

        style_markup = style.get('markup', None)
        if style_markup is not None:
            cond_dict[None] = style_markup

        for conditional_markup in style.xpath("./jr:conditionalStyle/jr:style[@markup]",
                                              namespaces=JRXML_NS):
            conditional_expr = conditional_markup.getprevious().text

            cond_dict.setdefault(conditional_markup.get('markup'),
                                 []).append(conditional_expr)

        result[style.get('name')] = cond_dict

        result.update(get_effective_markup_dict(jrxml, style.get('name'),
                                                cond_dict))

    return result

PROCESSING_STRATEGIES = dict(map(lambda (idx, name): (name, idx),
                                 enumerate([
    'N/A',
    'REPLACE',
    'DUPLICATE_AND_REPLACE',
])))

def get_processing_strategy(candidate_element, effective_markup_dict):
    if len(candidate_element.xpath('./jr:textElement', namespaces=JRXML_NS)) == 0:
        return (PROCESSING_STRATEGIES['N/A'], None)

    text_element_markup = candidate_element.xpath('./jr:textElement[@markup]',
                                                  namespaces=JRXML_NS)
    if len(text_element_markup) != 0:
        markup = text_element_markup[0].get('markup')
        if markup != 'none':
            return (PROCESSING_STRATEGIES['N/A'], None)
        return (PROCESSING_STRATEGIES['REPLACE'], None)

    report_element_style = candidate_element.xpath('./jr:reportElement[@style]',
                                                   namespaces=JRXML_NS)
    if len(report_element_style) == 0:
        return (PROCESSING_STRATEGIES['REPLACE'], None)

    style_name = report_element_style[0].get('style')
    if len(effective_markup_dict[style_name]) == 0:
        return (PROCESSING_STRATEGIES['REPLACE'], None)
    elif (len(effective_markup_dict[style_name]) == 1
          and effective_markup_dict[style_name].keys()[0] is None):
        markup = effective_markup_dict[style_name][None]
        if markup != 'none':
            return (PROCESSING_STRATEGIES['N/A'], None)
        return (PROCESSING_STRATEGIES['REPLACE'], None)

    html_conds = effective_markup_dict[style_name].get('html', None)
    styled_conds = effective_markup_dict[style_name].get('styled', None)
    rtf_conds = effective_markup_dict[style_name].get('rtf', None)
    none_conds = effective_markup_dict[style_name].get('none', None)
    other = effective_markup_dict[style_name].get(None, None)

    if html_conds is None and styled_conds is None and rtf_conds is None:
        return (PROCESSING_STRATEGIES['REPLACE'], style_name)

    if none_conds is None and other is None:
        return (PROCESSING_STRATEGIES['N/A'], None)

    return (PROCESSING_STRATEGIES['DUPLICATE_AND_REPLACE'], style_name)

def set_print_when_expr(text_field, cond_str):
    report_element = text_field.xpath('./jr:reportElement',
                                      namespaces=JRXML_NS)[0]

    print_when_expr = report_element.xpath('./jr:printWhenExpression',
                                           namespaces=JRXML_NS)

    new_expr = cond_str
    if len(print_when_expr) == 0:
        print_when_expr = etree.SubElement(report_element,
                                           JR + 'printWhenExpression')
    else:
        print_when_expr = print_when_expr[0]
        new_expr += ' && (' + print_when_expr.text + ')'

    print_when_expr.text = etree.CDATA(new_expr)

def make_conditioned_duplicate(text_field, conditions_dict):
    text_field_dup = deepcopy(text_field)
    text_field.getparent().append(text_field_dup)

    cond_str = ''
    for k in ('html', 'styled', 'rtf'):
        if conditions_dict.has_key(k):
            if len(cond_str) != 0:
                cond_str += ' || '
            cond_str += ' || '.join('(' + cond + ')'
                                    for cond in conditions_dict[k])

    if conditions_dict.has_key(None):
        if conditions_dict[None] != 'none':
            cond_str = 'true || ' + cond_str

    if conditions_dict.has_key('none'):
        cond_str = ('(' + cond_str + ') && !('
                    + ' || '.join('(' + cond + ')'
                                  for cond in conditions_dict['none'])
                    + ')')

    set_print_when_expr(text_field_dup, cond_str)

    return (text_field_dup, cond_str)

def set_text_field_markup(text_field, markup):
    text_field.xpath('./jr:textElement',
                     namespaces=JRXML_NS)[0].set('markup', markup)

def get_text_field_expr(text_field):
    text_field_expr = text_field.xpath('./jr:textFieldExpression',
                                       namespaces=JRXML_NS)
    if len(text_field_expr):
        return text_field_expr[0].text
    else:
        return ''

def stringify_expr(expr):
    return ('($P{%(_SIDE_EFFECT_VAR_NAME)s}.add(%(expr)s)'
            ' && $P{%(_SIDE_EFFECT_VAR_NAME)s}.get(0) == null)'
            ' ? $P{%(_SIDE_EFFECT_VAR_NAME)s}.remove(0)'
            ' : ("" + ($P{%(_SIDE_EFFECT_VAR_NAME)s}.remove(0)))'
            % {'_SIDE_EFFECT_VAR_NAME': _SIDE_EFFECT_VAR_NAME,
               'expr': expr})

def dont_underline_leading_space_expr(expr):
    new_expr = stringify_expr(expr)

    escape_chars = [('&', '&amp;'), ('<', '&lt;'), ('>', '&gt;')]
    for char_to_escape, escaped_char in escape_chars:
        new_expr += '.replace("%s", "%s")' % (char_to_escape, escaped_char)

    new_expr += (r'.replaceAll("^(\\s\\s*)(\\S.*)\$",'
                 r' "<style isUnderline=\"false\">\$1</style>\$2")')

    return new_expr

def set_text_field_expr(text_field, new_expr):
    text_field.xpath('./jr:textFieldExpression',
                     namespaces=JRXML_NS)[0].text = etree.CDATA(new_expr)

def process_text_field(processing_strategy, text_field, conditions_dict):
    if processing_strategy not in (PROCESSING_STRATEGIES['DUPLICATE_AND_REPLACE'],
                                   PROCESSING_STRATEGIES['REPLACE']):
        return

    if processing_strategy == PROCESSING_STRATEGIES['DUPLICATE_AND_REPLACE']:
        (dup, dup_cond_str) = make_conditioned_duplicate(text_field,
                                                         conditions_dict)

        cond_str = '!(' + dup_cond_str + ')'
        set_print_when_expr(text_field, cond_str)

    set_text_field_markup(text_field, 'styled')

    expr = get_text_field_expr(text_field)
    if len(expr):
        new_expr = dont_underline_leading_space_expr(expr)
        set_text_field_expr(text_field, new_expr)

def staticText_to_textFieldExpression(static_text):
    static_text_text = static_text.xpath('./jr:text',
                                         namespaces=JRXML_NS)[0]
    static_text_text.text = etree.CDATA('"%s"' % static_text_text.text)
    static_text_text.tag = JR + 'textFieldExpression'
    static_text.tag = JR + 'textField'
    return static_text

def install_side_effect_var(root):
    side_effect_var = etree.Element(JR + 'parameter',
                                    name=_SIDE_EFFECT_VAR_NAME,
                                    isForPrompting='false')
    side_effect_var.set('class', 'java.util.List')
    var_expr = etree.SubElement(side_effect_var, JR + 'defaultValueExpression')
    var_expr.text = etree.CDATA('[]')
    insert_element(root, side_effect_var)

    crosstab_propagator = etree.Element(JR + 'crosstabParameter',
                                        name=_SIDE_EFFECT_VAR_NAME)
    crosstab_propagator.set('class', 'java.util.List')
    expr = etree.SubElement(crosstab_propagator, JR + 'parameterValueExpression')
    expr.text = etree.CDATA('$P{%s}' % _SIDE_EFFECT_VAR_NAME)

    for crosstab in root.xpath("//jr:crosstab", namespaces=JRXML_NS):
        insert_element(crosstab, deepcopy(crosstab_propagator))

def transform_jrxml_dont_underline_leading_space(jrxml, jrxml_opts):
    if not jrxml_opts.dont_underline_leading_space:
        return

    effective_markup_dict = get_effective_markup_dict(jrxml)

    root = jrxml.getroot()

    install_side_effect_var(root)

    for candidate_element in root.xpath('//jr:textField|//jr:staticText',
                                        namespaces=JRXML_NS):
        (processing_strategy,
         style_name) = get_processing_strategy(candidate_element,
                                               effective_markup_dict)

        if processing_strategy is PROCESSING_STRATEGIES['N/A']:
            continue

        if tag_name(candidate_element.tag) == 'staticText':
            candidate_element = staticText_to_textFieldExpression(candidate_element)

        text_field = candidate_element

        process_text_field(processing_strategy,
                           text_field,
                           style_name and effective_markup_dict[style_name]
                           or None)
