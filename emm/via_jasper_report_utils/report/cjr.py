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

from ast import literal_eval
from lxml import etree
from util_jrxml import get_resource_dir, write_jrxml, import_plugins
import re
from os import path
import os
import subprocess
import shutil
from optparse import OptionParser
from copy import deepcopy
import imp

_JRXML_COMPILER_SRC_PATH = path.join(get_resource_dir(), 'JasperCompiler.java')

_jrxml_preprocessors = import_plugins('cjr_transformer_',
                                      r'cjr_transformer_[^_]+_(.+)',
                                      '(%(mod_name)s.transform_jrxml_%(trunk)s_cmd_opts,'
                                      ' %(mod_name)s.transform_jrxml_%(trunk)s)')
_jrxml_generators = import_plugins('cjr_generator_',
                                   r'cjr_generator_(.+)',
                                   '(%(mod_name)s.gen_jrxml_%(trunk)s_cmd_opts,'
                                   ' %(mod_name)s.gen_jrxml_%(trunk)s,'
                                   ' %(mod_name)s.gen_jrxml_%(trunk)s_rpt_names_to_opts)')

_CMD_OPTIONS = None

def parse_cmd():
    parser = OptionParser(usage=('Usage: %prog [options] IREPORT_LIBS_DIR_PATH [JRXML_FILE[:[OERP_REPORT_REGISTRATION_XML_FILE]] ...]'
                                 '\n'
                                 'OERP_REPORT_REGISTRATION_XML_FILE defaults to JRXML_FILE_registration.xml\n'
                                 '\n'
                                 'For each JRXML_FILE that is followed by a colon (:), the generations of its derivatives are'
                                 ' controlled completely by the report registration XML file\n'
                                 '\n'
                                 'For each JRXML_FILE that is *not* followed by a colon (:), the generations of its derivatives are'
                                 ' controlled completely by the given command options'))
    parser.add_option('-k', '--keep', dest='keep', action='store_true',
                      default=False, help='keep the generated JRXML files')
    parser.add_option('-f', '--force', dest='overwrite', action='store_true',
                      default=False, help='overwrite all generated JRXML files that are kept')
    parser.add_option('-d', '--dry-run', dest='dry_run', action='store_true',
                      default=False, help='do not compile, only generate the JRXML files')
    parser.add_option('-p', '--preview', dest='preview', action='store_true',
                      default=False, help='[Debugging] only run the transformation logics without generating and compiling any files')
    parser.add_option('', '--keep-ref', dest='keep_ref', action='store_true',
                      default=False, help='[Debugging] keep the generated *_ref.jrxml even when compilation fails')
    parser.add_option('-c', '--compile-only', dest='compile_only', action='store_true',
                      default=False, help='compile the given JRXML files, do not generate any derivative')

    option_parsers = []
    for set_cmd_opts in [entry[0] for entry in (_jrxml_preprocessors + _jrxml_generators)]:
        option_parsers.append(set_cmd_opts(parser))

    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error('incorrect number of arguments')
    elif len(args) == 1:
        exit(0)

    for option_parser in option_parsers:
        option_parser(options)

    global _CMD_OPTIONS
    _CMD_OPTIONS = options

    ireport_libs_dir_path = path.abspath(args[0])

    oerp_rpt_regs_opts = {}
    jrxml_file_paths = []
    for arg in args[1:]:
        if arg.find(':') == -1:
            jrxml_file_paths.append(path.abspath(arg))
        else:
            parts = arg.split(':')
            jrxml_file_path = path.abspath(parts[0])
            jrxml_file_paths.append(jrxml_file_path)

            if parts[1] == '':
                rpt_reg_file_path = path.splitext(jrxml_file_path)[0] + '_registration.xml'
            else:
                rpt_reg_file_path = path.abspath(parts[1])

            rpt_reg_xml = get_xml(rpt_reg_file_path)
            rpt_names = []
            for rpt_name_field in rpt_reg_xml.xpath("//field[@name='report_name']"):
                rpt_file = rpt_name_field.getparent().xpath("./field[@name='report_file']")[0]
                rpt_file_path = rpt_file.text or literal_eval(rpt_file.get('eval'))

                if (rpt_file_path
                    and re.match(r'^(.*/)?%s(_.+)?\.jrxml$'
                                 % path.splitext(path.basename(jrxml_file_path))[0],
                                 rpt_file_path)):
                    rpt_names.append(rpt_name_field.text)

            # [ASSUME] I rely on the behavior of deepcopy(options) not to copy
            # the values set after (options, ...) = parser.parse_args() has been
            # called
            jrxml_compilation_opts = deepcopy(_CMD_OPTIONS)
            for jrxml_mod_rpt_names_to_opts in [entry[2] for entry in _jrxml_generators]:
                jrxml_mod_rpt_names_to_opts(rpt_names, jrxml_compilation_opts)
            oerp_rpt_regs_opts[jrxml_file_path] = jrxml_compilation_opts

    return (ireport_libs_dir_path, jrxml_file_paths, oerp_rpt_regs_opts)

def get_xml(xml_file_path):
    return etree.parse(xml_file_path,
                       parser=etree.XMLParser(strip_cdata=False,
                                              remove_blank_text=True))

def get_jrxml(jrxml_file_path):
    return get_xml(jrxml_file_path)

def get_src_file_name():
    return path.basename(_JRXML_COMPILER_SRC_PATH)

def get_class_name():
    return path.splitext(get_src_file_name())[0]

def get_class_file_name():
    return get_class_name() + '.class'

def get_ireport_cp(ireport_libs_dir_path):
    return path.join(ireport_libs_dir_path, r'*')

def get_working_dir(jrxml_file_path):
    return path.dirname(jrxml_file_path)

def get_jrxml_reference_path(jrxml_file_path):
    return path.join(get_working_dir(jrxml_file_path),
                     path.splitext(path.basename(jrxml_file_path))[0] + '_ref.jrxml')

def get_jasper_path(jrxml_file_path):
    return path.splitext(jrxml_file_path)[0] + '.jasper'

_generated_files = []

def gen_jrxml_compiler(ireport_libs_dir_path, working_dir):
    shutil.copy(_JRXML_COMPILER_SRC_PATH, working_dir)
    _generated_files.append(path.join(working_dir, get_src_file_name()))

    subprocess.check_call(['javac', '-cp', get_ireport_cp(ireport_libs_dir_path),
                           get_src_file_name()],
                          cwd=working_dir)
    _generated_files.append(path.join(working_dir, get_class_file_name()))

def compile_jrxml(ireport_libs_dir_path, jrxml_file_path):
    subprocess.check_call(['java', '-cp',
                           ':'.join([get_ireport_cp(ireport_libs_dir_path),
                                     '.']),
                           get_class_name(),
                           jrxml_file_path],
                          cwd=get_working_dir(jrxml_file_path))

def main():
    (ireport_libs_dir_path, jrxml_file_paths, oerp_rpt_regs_opts) = parse_cmd()

    try:
        # Compile the JasperCompiler with the right iReport version
        unique_working_dirs = set(map(lambda e: path.dirname(e), jrxml_file_paths))
        if not _CMD_OPTIONS.preview:
            for working_dir in unique_working_dirs:
                gen_jrxml_compiler(ireport_libs_dir_path, working_dir)

        for jrxml_file_path in jrxml_file_paths:
            # Compile the main report jrxmls
            reference_jrxml = get_jrxml(jrxml_file_path)
            for preprocess in [entry[1] for entry in _jrxml_preprocessors]:
                preprocess(reference_jrxml, _CMD_OPTIONS)
            if not _CMD_OPTIONS.dry_run and not _CMD_OPTIONS.preview:
                jrxml_path = write_jrxml(reference_jrxml,
                                         output_file_path=get_jrxml_reference_path(jrxml_file_path))
                if not _CMD_OPTIONS.keep_ref:
                    _generated_files.append(jrxml_path)
                compile_jrxml(ireport_libs_dir_path, jrxml_path)
                shutil.move(get_jasper_path(jrxml_path), get_jasper_path(jrxml_file_path))
                if _CMD_OPTIONS.keep:
                    del _generated_files[-1]

            if _CMD_OPTIONS.compile_only:
                continue

            # Generate the derivative jrxmls and compile them
            for jrxml_modifier in [entry[1] for entry in _jrxml_generators]:
                for jrxml in jrxml_modifier(deepcopy(reference_jrxml),
                                            oerp_rpt_regs_opts.get(jrxml_file_path, _CMD_OPTIONS)):
                    if jrxml is None or _CMD_OPTIONS.preview:
                        continue

                    jrxml_path = write_jrxml(jrxml,
                                             output_file_path=get_working_dir(jrxml_file_path),
                                             dry_run=True)

                    if (not path.islink(jrxml_path) and path.isfile(jrxml_path)
                        and not _CMD_OPTIONS.overwrite):
                            # There is a custom modification to the generated JRXML,
                            # so just compile
                            if not _CMD_OPTIONS.dry_run:
                                compile_jrxml(ireport_libs_dir_path, jrxml_path)
                    else:
                        if path.islink(jrxml_path):
                            # Prevent write to the original JRXML
                            os.unlink(jrxml_path)

                        write_jrxml(jrxml,
                                    output_file_path=get_working_dir(jrxml_file_path))
                        if not _CMD_OPTIONS.dry_run:
                            compile_jrxml(ireport_libs_dir_path, jrxml_path)

                        if not _CMD_OPTIONS.keep:
                            os.unlink(jrxml_path)
                            os.symlink(path.basename(jrxml_file_path),
                                       path.join(get_working_dir(jrxml_file_path),
                                                 path.basename(jrxml_path)))
    finally:
        for _path in _generated_files:
            print('ini brooo', _path)
            try:
                os.unlink(_path)
            except OSError as e:
                if 'No such file or directory' not in e:
                    raise e

if __name__ == '__main__':
    main()
