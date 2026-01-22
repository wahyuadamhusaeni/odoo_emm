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
from util_jrxml import JRXML_NS, set_x, get_width, set_width, get_height, \
    component_set_str, set_y, get_y, JR, set_height, BOX_ORDER, STYLE_ORDER, \
    reorder_elements, parse_exp_file, get_resource_dir, write_jrxml
from glob import glob
from os import path
import os
import numbers
import subprocess
import shutil
from optparse import OptionParser

_CMD_OPTIONS = None

def parse_cmd():
    parser = OptionParser(usage='Usage: %prog [options] IREPORT_LIBS_DIR_PATH [JAVA_FILE ...]')
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error('incorrect number of arguments')
    elif len(args) == 1:
        exit(0)

    global _CMD_OPTIONS
    _CMD_OPTIONS = options

    ireport_libs_dir_path = path.abspath(args[0])

    java_file_paths = map(lambda e: path.abspath(e), args[1:])

    return (ireport_libs_dir_path, java_file_paths)

def get_ireport_cp(ireport_libs_dir_path):
    return path.join(ireport_libs_dir_path, r'*')

if __name__ == '__main__':
    (ireport_libs_dir_path, java_file_paths) = parse_cmd()

    classpath = ':'.join([get_ireport_cp(ireport_libs_dir_path),
                          get_resource_dir()])

    for java_file_path in java_file_paths:
        subprocess.check_call(['javac',
                               '-cp', classpath,
                               path.basename(java_file_path)],
                              cwd=path.dirname(java_file_path))
