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
from copy import deepcopy
from _cjr_generator_pageless import gen_jrxml_pageless

_SPREADSHEET_FORMATS = ('xls', 'csv')

def gen_jrxml_spreadsheets_cmd_opts(parser):
    parser.add_option('', '--spreadsheets', dest='spreadsheets', action='store',
                      help='generate the spreadsheet formats of the JRXML files (e.g., --spreadsheets=xls,csv)')

    def options_parser(options):
        parsed_spreadsheet_formats = []
        if options.spreadsheets is not None:
            for format in map(lambda fmt: fmt.lower(), options.spreadsheets.split(',')):
                if format not in _SPREADSHEET_FORMATS:
                    raise Exception('Unrecognized spreadsheet format %s, please develop cjr.py further' % format)
                parsed_spreadsheet_formats.append(format)
        options.spreadsheets = parsed_spreadsheet_formats
    return options_parser

def gen_jrxml_spreadsheets_rpt_names_to_opts(rpt_names, options):
    opt_args = []
    for rpt_name in rpt_names:
        match_obj = re.match('.+_(%s)$' % ('|'.join(_SPREADSHEET_FORMATS)),
                             rpt_name)
        if match_obj:
            opt_args.append(match_obj.group(1))
    options.spreadsheets = opt_args

def gen_jrxml_spreadsheets(jrxml_ref, jrxml_opts):
    jrxml = None

    if 'xls' in jrxml_opts.spreadsheets:
        jrxml = gen_jrxml_pageless('xls', deepcopy(jrxml_ref))
        root = jrxml.getroot()
        # Further modifications if necessary
        yield jrxml

    if 'csv' in jrxml_opts.spreadsheets:
        jrxml = gen_jrxml_pageless('csv', deepcopy(jrxml_ref))
        root = jrxml.getroot()
        # Further modifications if necessary
        yield jrxml
