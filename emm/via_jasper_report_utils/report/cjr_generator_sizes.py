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

import re
from util_jrxml import JRXML_NS, JR, get_x, get_width, SIZE_REGISTRY, \
    PAPER_ORIENTATION, set_x, set_width

def gen_jrxml_sizes_cmd_opts(parser):
    parser.add_option('', '--page-sizes', dest='page_sizes', action='store',
                      help='generate derivate(s) by scaling the widths of the JRXML files (e.g., --page-sizes=A3_landscape,A2_portrait)')

    def options_parser(options):
        parsed_page_sizes = []
        if options.page_sizes is not None:
            for page_size in options.page_sizes.split(','):
                (size, orientation) = page_size.split('_')
                size = size.upper()
                orientation = orientation.lower()
                if size not in SIZE_REGISTRY:
                    raise Exception('Unrecognized page size %s, please develop util_jrxml.py further' % size)
                if orientation not in PAPER_ORIENTATION:
                    raise Exception('Page orientation %s is invalid (choice: "landscape", "portrait")' % orientation)
                parsed_page_sizes.append((size, orientation))
        options.page_sizes = parsed_page_sizes
    return options_parser

def gen_jrxml_sizes_rpt_names_to_opts(rpt_names, options):
    opt_args = []
    for rpt_name in rpt_names:
        match_obj = re.match('.+_(%s)_(%s)$' % ('|'.join(entry.lower() for entry in SIZE_REGISTRY),
                                                '|'.join(entry.lower() for entry in PAPER_ORIENTATION)),
                             rpt_name)
        if match_obj:
            opt_args.append((match_obj.group(1).upper(), match_obj.group(2)))
    options.page_sizes = opt_args

def gen_jrxml_sizes(jrxml, jrxml_opts):
    root = jrxml.getroot()

    for (size, orientation) in jrxml_opts.page_sizes:
        root.set('name', ('_'.join([root.get('name'), size, orientation])).lower())
        margin = int(root.get('leftMargin')) + int(root.get('rightMargin'))

        curr_width = int(root.get('pageWidth'))
        width_idx, height_idx = (int(orientation == 'landscape'),
                                 int(orientation != 'landscape'))
        (target_width,
         target_height) = (SIZE_REGISTRY[size][width_idx],
                           SIZE_REGISTRY[size][height_idx])

        root.set('pageWidth', '%d' % target_width)
        root.set('columnWidth', '%d' % (target_width - margin))
        root.set('pageHeight', '%d' % target_height)

        scaling_factor = float(target_width - margin) / float(curr_width - margin)
        scale = lambda x: round(x * scaling_factor)

        for component in root.xpath("//jr:reportElement/..", namespaces=JRXML_NS):
            set_x(component, scale(get_x(component)))
            set_width(component, scale(get_width(component)))

        for width_attr in root.xpath("//jr:*[@width and name() != 'reportElement']", namespaces=JRXML_NS):
            width_attr.set('width', '%d' % scale(int(width_attr.get('width'))))

        yield jrxml
