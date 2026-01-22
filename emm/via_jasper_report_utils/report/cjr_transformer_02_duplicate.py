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
from util_jrxml import JRXML_NS, JR, tag_name, import_plugins, \
    DUPLICABLE_ELEMENTS

PROPERTY_KEY = 'via.duplicate.'

def _import_property_setters():
    return dict(import_plugins('_cjr_transformer_duplicate_prop_setter_',
                               r'_cjr_transformer_duplicate_prop_setter_(.+)',
                               "('%(trunk)s', %(mod_name)s._set_prop_%(trunk)s)"))

_available_property_setters = _import_property_setters()

def _remove_dup_properties(element, prop_lists):
    for prop_list in prop_lists:
        for prop in prop_list:
            if prop.origin is None:
                continue

            element.remove(prop.origin)
            prop.origin = None

def transform_jrxml_duplicate_cmd_opts(parser):
    parser.add_option('', '--no-duplicate', dest='preprocess_duplicate', action='store_false',
                      default=True, help='Preprocess by duplicating components tagged with "via.duplicate.*" setting the specified properties')

    def options_parser(options):
        pass
    return options_parser

class PropertySpecification(object):
    def __init__(self, name, value, origin):
        self.name = name
        self.value = value
        self.origin = origin

    def __repr__(self):
        return repr({
            'name': self.name,
            'value': self.value,
            'origin': self.origin,
        })

def _duplicate(element, dup_specs):
    duplicates = []
    for dup_id, prop_list in dup_specs.iteritems():
        dup = deepcopy(element)
        duplicates.append((element.getparent(), dup))

        for prop in prop_list:
            if prop.name in _available_property_setters:
                _available_property_setters[prop.name](dup, prop.value)
            else:
                raise Exception("Don't know how to set property '%s' on %s"
                                " (please develop _cjr_transformer_duplicate_prop_setter_%s.py)"
                                % (prop.name, tag_name(element.tag), prop.name))
    return duplicates

def _transform_jrxml_duplicate(dups, element, level):
    result = {}
    if (tag_name(element.tag) == 'property'
        and element.get('name').find(PROPERTY_KEY) == 0):
            dup_spec = element.get('name')[len(PROPERTY_KEY):]
            dup_id, prop_name = dup_spec.split('.')
            result.setdefault(dup_id, []).append(PropertySpecification(
                name=prop_name,
                value=element.get('value'),
                origin=element
            ))

    for child_element in element.iterchildren():
        sub_result = _transform_jrxml_duplicate(dups, child_element, level + 1)
        for dup_id, prop_list in sub_result.iteritems():
            parent_prop_list = result.setdefault(dup_id, [])
            for prop in prop_list:
                parent_prop_list.append(prop)

    if result and tag_name(element.tag) != 'property':
        _remove_dup_properties(element, result.itervalues())

        if tag_name(element.tag) in DUPLICABLE_ELEMENTS:
            dups.extend(_duplicate(element, result))
            result = {}

    return result

def transform_jrxml_duplicate(jrxml, jrxml_opts):
    if not jrxml_opts.preprocess_duplicate:
        return

    root = jrxml.getroot()

    dups = []
    _transform_jrxml_duplicate(dups, root, 0)

    for (dup_parent, dup) in dups:
        dup_parent.append(dup)
