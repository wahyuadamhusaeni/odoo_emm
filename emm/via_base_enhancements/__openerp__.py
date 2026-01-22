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

{
    'name': 'VIA Enhancements for OpenERP Base',
    'version': '1.7',
    'category': 'Hidden/Dependency',
    'complexity': 'easy',
    'description': """
    This module provides enhancements or fixes to the existing OpenERP base functionalities:
    - Various utility tools:
      To use this utility, include the following: from via_base_enhancements import tools.resolve_o2m_operations
      * Tool for resolving o2m operations.  It receives various form o2m result and returns
        a dictionary of read result (fields can be specified) of the objects.
        Signature:
            resolve_o2m_operations(cr, uid, target_osv, operations, fields=[], context=None)
        operations format of o2m operation tuple, can be 0, 1, or 4
      * Tool for preparing dictionary returned from orm.read (val) so that it can be used for write.
        It will translate relation fields from tuples to the corresponding id.
        Signature:
            prep_dict_for_write(cr, uid, val, context=None)
      * Tool for preparing dictionary returned from orm.read (val) so that it can be used in Python string formatting operation.
        It will translate relation fields from tuples to the corresponding name and boolean False value to empty string.
        Signature:
            prep_dict_for_formatting(cr, uid, val, context=None)
      * Tool for running a command (popenargs) in terminal and obtaining the stdout output.
        The command line and its argument is passed as a list of strings.
        Signature:
            check_output(*popenargs, **kwargs):
      * Tool for reading a file identified by (path) and return the entire content.
        Signature:
            get_file_content(path='')
      * Tool for writing (content) to temporary file.
        Signature:
            write_temp_file(content='')
      * Tool for purging a given temporary file (path) with a random characters.
        Signature:
            purge_temp_file(path='')
      * Function decorator for Least Recent Used function call caching
        Signature:
            @lru_cache
      * Function to get the precision of a given number
        Signature:
            get_precision(number)
      * Incorporate changes merged into r9897 of ~openerp/openobject-addons/7.0 to handle incorrect
        redefition of method load() by ir.translation.
      * Fix default Record Rules for ir.values object to allow for Create, Write, and Delete of ir.values
        of types other than 'default' for all users.
      * Tool to check wheter an ORM method (validate_hook) exist in an ORM model (model)
        Signature:
            orm_method_exist(obj, cr, uid, model, validate_hook, context=None)
      * Tool to get ORM Object from single string XML (xml)
        Signature:
            get_object_from_xml(obj, cr, uid, xml, context=None)
      * Tool to format a given string with a key-value pair (dict) and/or current timestamp using strftime
        Signature:
            format_file_name(template='', dict={})
      * Tool to translate Python formatspec syntax (format_spec) to re syntax:
        Signature:
            formatspec_to_re(format_spec)
        Supporting function signatures:
            formatspectype_to_reclass(type), to convert formatspec type (e.g. s, d, etc.) to compatible RE class
            strftimespec_to_reclass(literal), to convert strftime literal (e.g. %%Y, %%m, %%s) to compatible RE class
      * Provision of default domain list that can be used by other developments to set a domain (default) based by
        selecting the relevant default domain configuration.  To use, the model must include a many2one field of
        default.domain.  The domain from the selected default.domain model can then be used.
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'base',
        'base_import',
    ],
    'data': [
        'security/via_base_enhancement_security.xml',
        'default_domain_view.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
