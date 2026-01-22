# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 - 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

import types
from os import access, W_OK, listdir, path, rename
import re
import csv
import sys
import base64

from openerp.tools.safe_eval import safe_eval, test_expr, _SAFE_OPCODES
from osv import osv, orm, fields
from tools.translate import _
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import logging
from openerp.tools.misc import attrgetter

from base.ir.ir_model import _get_fields_type
from via_base_enhancements.models import orm_method_exist
from via_base_enhancements.tools import formatspec_to_re, prep_dict_for_formatting, format_file_name


logger = logging.getLogger(__name__)

################################################################################
# Upload configuration
################################################################################

CRON_PERIOD = [
    ('adhoc', 'Ad-Hoc'),
    ('hour', 'Hour(s)'),
    ('day', 'Day(s)'),
    ('month', 'Month(s)'),
    ('year', 'Year(s)'),
]

FORMAT_TYPE = [
    ('csv', 'Comma Separated-Values'),
    ('method', 'Method Parsing'),
]

IMPORT_TYPE = [
    ('method', 'Model Method'),
    ('code', 'Python Code'),
]

FAILURE_HANDLING = [
    ('file', 'Sucessful File'),
    ('record', 'Successful Record'),
]


class file_upload_import_config(orm.Model):
    """
    File upload and import utility configuration holds sets of information that is
    used to process a file upload either ad-hoc or periodically.
    """
    _name = 'file.upload.import.config'
    _description = 'Configuration for file upload and import utility'

    def _validate_values(self, cr, uid, vals, model_id=False, context=None):
        """
        This method is used to validate the value dictionary (vals) to be used
        in write or create method.
        """
        # Frequency cannot be 0 unless if it is adhoc
        _value = vals.get('frequency_period', None)
        if _value is not None and _value not in ('adhoc'):
            _value2 = vals.get('frequency_int', None)
            if _value2 is not None and not _value2:
                raise osv.except_osv(_('Error!'), _('Frequency cannot be 0!'))

        # Validate that the working_folder exist
        _value = vals.get('working_folder', None)
        logger.info("working_folder is %s" % (_value))
        if _value is not None and not access(_value, W_OK):
            raise osv.except_osv(_('Error!'), _('%s is not valid folder in the server!  Please contact your administrator.') % (_value))

        # Validate that the format regex are valid
        for _field in ['file_name_format', 'log_name_format', 'processed_name_format']:
            _value = vals.get(_field, '')
            logger.info("%s is %s" % (_field, _value))
            try:
                re.compile(_value)
            except:
                raise osv.except_osv(_('Error!'), _('Value %s for field %s is not a valid regular expression!') % (_value, self._columns[_field].string))

        # Validate that the methods exist
        _model = model_id or vals.get('model_id', None)
        _model = _model and self.pool.get('ir.model').browse(cr, uid, _model, context=context) or False
        _model = _model and _model.model or ''
        if _model:
            for k, v in {'format_type': ('method', 'parse_method'), 'import_handling': ('method', 'import_hook')}.iteritems():
                if vals.get(k, None) == v[0]:
                    _value = vals.get(v[1], None)
                    _check = orm_method_exist(self, cr, uid, _model, _value, context=context)
                    if not _check:
                        raise osv.except_osv(_('Error!'), _('Method %s has not been developed for model %s!') % (_value, _model))

        return True

    def execute(self, cr, uid, ids, context=None):
        """
        TODO:
        """
        if context is None:
            context = {}

        res = {}
        _log_pool = self.pool.get('file.upload.import.log')
        _working_folder = context.get('working_folder', '')
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = []
            # Validate that all information are OK
            _defs = {'run_logs': [(6, 0, [])]}
            _obj_vals = self.copy_data(cr, uid, _obj.id, default=_defs, context=context)
            if _working_folder:
                _obj_vals.update({'working_folder': _working_folder})
            else:
                _working_folder = _obj_vals.get('working_folder', '')
            self._validate_values(cr, uid, _obj_vals, context=context)

            # Browse through the working_folder for files that matches the file_name_format
            # and process it one by one
            _name_re = re.compile(formatspec_to_re(_obj.file_name_format))
            _model = _obj.model_id.model
            _mdl_pool = self.pool.get(_model)
            _imd_pool = self.pool.get('ir.model.data')
            _att_pool = self.pool.get('ir.attachment')
            for _node in listdir(_working_folder):
                _match = _name_re.match(_node)
                if _match:
                    _dict = _match.groupdict()
                    # Prepare the dictionary to be used for file name generator
                    x, y = path.splitext(path.basename(_node))
                    _dict.update({'original_file': x, 'original_ext': y})
                    _file = path.join(_working_folder, _node)

                    # Generate the logfile name
                    _logfile = format_file_name(template=_obj_vals.get('log_name_format', ''), dict=_dict)
                    _logfile_path = path.join(_working_folder, _logfile)
                    _logfile_stream = open(_logfile_path, 'a+')

                    # Generate the processed file name
                    _processed_file = format_file_name(template=_obj_vals.get('processed_name_format', ''), dict=_dict)
                    _processed_file_path = path.join(_working_folder, _processed_file)

                    _file_data = {}

                    _logfile_stream.write("Start processing file %s %s\n" % (_node, dt.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)))
                    if _obj_vals.get('format_type', None) == 'csv':
                        # Open the file to be processed as CSV
                        _file_reader = csv.reader(open(_file), delimiter=str(_obj_vals.get('csv_delim', ',')), quotechar=str(_obj_vals.get('csv_quote', '"')))
                        for _idx, _line in enumerate(_file_reader):
                            if _idx < _obj.csv_skip:
                                continue

                            # Process the line one at a time
                            _vals = {}
                            for _map in _obj.field_mapping:
                                # Sequence is 1-based while index is 0-based
                                _value = _line[_map.sequence - 1]

                                try:
                                    if _map.ttype in ('many2one'):
                                        # Get the ID of the object based on the record_match method
                                        if _map.record_match == 'id':
                                            _vals.update({_map.field_id.name: _value})
                                        elif _map.record_match == 'xml_id':
                                            module = False
                                            xml_id = False
                                            if _value and ('.' in _value):
                                                assert len(_value.split('.')) == 2, _("'%s' contains too many dots. XML ids should not contain dots ! These are used to refer to other modules data, as in module.reference_id") % _value
                                                module, xml_id = _value.split('.')
                                            _objmdl, _value = _imd_pool.get_object_reference(cr, uid, module, xml_id)
                                            assert (_value), _("External ID %s.%s is not found when processing line %d") % (module, xml_id, str(_idx))

                                            _vals.update({_map.field_id.name: _value})
                                        else:  # Assumes name
                                            _rel = _map.field_id.relation
                                            _rel_obj = self.pool.get(_rel)
                                            _found = _rel_obj.name_search(cr, uid, name=_value, context=context, limit=1)
                                            assert (_found), _("%s %s is not found when processing line %d") % (_rel_obj._name, _value, str(_idx))

                                            _vals.update({_map.field_id.name: _found[0][0]})
                                    elif _map.ttype in ('date'):
                                        _value = dt.strptime(_value, _map.date_format)
                                        _value = _value.strftime(DEFAULT_SERVER_DATE_FORMAT)
                                        _vals.update({_map.field_id.name: _value})
                                    elif _map.ttype in ('datetime'):
                                        _value = dt.strptime(_value, _map.date_format)
                                        _value = _value.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                                        _vals.update({_map.field_id.name: _value})
                                    elif _map.ttype in ('one2many', 'many2many'):
                                        # Currently does not handles these types
                                        pass
                                    else:
                                        _vals.update({_map.field_id.name: _value})
                                except:
                                    # Log the error
                                    _logfile_stream.write("File %s line %s column %s: %s, error: %s\n" % (_node, str(_idx - 1), _map.field_id.name, _line, sys.exc_info()[1]))
                                    if (_obj_vals.get('failure_handling', 'record') == 'file') or context.get('abort', False):
                                        _logfile_stream.flush()
                                        _logfile_stream.close()
                                        # Raise error
                                        raise osv.except_osv(_('Error!'), _('Import failed.  Please check log file %s.') % (_logfile))

                            _file_data.update({_idx + 1: _vals})
                    elif _obj_vals.get('format_type', None) == 'method':
                        # Get the model and method, call the method passing the file name
                        # The method should return an iterable which members is dictionary
                        # compatible with ORM's write method
                        # _file_data = getattr(_mdl_pool, _obj.parse_method)()
                        pass
                    else:  # Unhandled format type
                        pass

                    # Process the values
                    _import_handling_type = _obj_vals.get('import_handling', '')
                    _aborted = False
                    _ctx = {}
                    for _idx, _line in _file_data.iteritems():
                        try:
                            if (_import_handling_type == 'method'):
                                _ctx = context.copy()
                                _ctx.update(_dict)
                                _ctx.update({'line_data': _line})
                                _mdl_pool.__getattribute__(_obj.import_hook)(cr, uid, config_id=_obj.id, context=_ctx)
                            elif (_import_handling_type == 'code'):
                                # test_expr(_obj.python_code, _SAFE_OPCODES, mode="exec")(cr, uid, _node, _line, config_id=_obj.id, context=context)
                                # (, globals_dict={}, locals_dict={}, mode="exec")
                                pass
                            else:
                                pass
                        except:
                            # Log the error
                            _logfile_stream.write("File %s line %s: %s, error: %s\n" % (_node, str(_idx), _line, sys.exc_info()[1]))
                            if (_obj_vals.get('failure_handling', 'record') == 'file') or context.get('abort', False):
                                _aborted = True
                                if context.get('raise_exception', False):
                                    _logfile_stream.flush()
                                    _logfile_stream.close()
                                    # Raise error
                                    raise osv.except_osv(_('Error!'), _('Import failed.  Please check log file %s.') % (_logfile))

                    # Do post processing
                    if not _aborted:
                        try:
                            if (_import_handling_type == 'method'):
                                _ctx = context.copy()
                                _ctx.update(_dict)
                                _mdl_pool.__getattribute__(_obj.post_import_hook)(cr, uid, config_id=_obj.id, context=_ctx)
                            elif (_import_handling_type == 'code'):
                                # test_expr(_obj.python_code, _SAFE_OPCODES, mode="exec")(cr, uid, _node, _line, config_id=_obj.id, context=context)
                                # (, globals_dict={}, locals_dict={}, mode="exec")
                                pass
                            else:
                                pass

                            rename(_file, _processed_file_path)
                        except:
                            # Log the error
                            _logfile_stream.write("File %s: %s, error: %s\n" % (_node, sys.exc_info()[1]))
                            if (_obj_vals.get('failure_handling', 'record') == 'file') or context.get('abort', False):
                                _aborted = True
                                if context.get('raise_exception', False):
                                    # Raise error
                                    raise osv.except_osv(_('Error!'), _('Import failed.  Please check log file %s.') % (_logfile))

                    _logfile_stream.write("Finished processing file %s %s\n\n\n\n\n" % (_node, dt.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)))
                    _logfile_stream.flush()
                    _logfile_stream.close()
                    _logfile_stream = open(_logfile_path)
                    _logcontent = _logfile_stream.read()
                    _logfile_stream.close()

                    # Create the run log and attach the log file
                    _vals = {
                        'config_id': _obj.id,
                        'model_id': _obj.model_id.id,
                        'run_time': fields.datetime.now(),
                        'working_folder': _working_folder,
                        'file_name': _node,
                        'log_name': _logfile,
                        'processed_file': _processed_file,
                    }
                    _res_id = _ctx.get('res_id', False)
                    if _res_id:
                        _vals.update({'res_id': _res_id})
                    _new_log = _log_pool.create(cr, uid, _vals, context=context)
                    res[_obj.id].append(_new_log)

                    # Make the log as attachment to the run log
                    _vals = {
                        'name': _logfile,
                        'datas': base64.encodestring(_logcontent),
                        'datas_fname': _logfile,
                        'res_model': _log_pool._name,
                        'res_id': _new_log,
                    }
                    _att_pool.create(cr, uid, _vals, context=context)
        return res

    def generate_templates(self, cr, uid, ids, context=None):
        """
        TODO:
        """
        if context is None:
            context = {}

        res = {}
        _working_folder = context.get('working_folder', '')
        _att_pool = self.pool.get('ir.attachment')
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = []

            # Validate that all information are OK
            _defs = {'run_logs': [(6, 0, [])]}
            _obj_vals = self.copy_data(cr, uid, _obj.id, default=_defs, context=context)
            if _working_folder:
                _obj_vals.update('working_folder', _working_folder)
            else:
                _working_folder = _obj_vals.get('working_folder', '')
            self._validate_values(cr, uid, _obj_vals, context=context)

            # Prepare the dictionary to be used for file name generator
            _model = context.get('active_model', False)
            _ids = context.get('active_ids', [])
            if _model and _ids:
                _mdl_pool = self.pool.get(_model)
                for _todo in _mdl_pool.browse(cr, uid, _ids, context=context):
                    # Generate the download file name
                    _dict = prep_dict_for_formatting(cr, uid, _mdl_pool.read(cr, uid, _todo.id, context=context), context=context)
                    _file = format_file_name(template=_obj_vals.get('file_name_format', ''), dict=_dict)
                    _file_path = path.join(_working_folder, _file)

                    if _obj_vals.get('format_type', None) == 'csv':
                        # Open the file to be processed as CSV
                        _file_stream = open(_file_path, 'w+')
                        _file_writer = csv.writer(_file_stream, delimiter=str(_obj_vals.get('csv_delim', ',')), quotechar=str(_obj_vals.get('csv_quote', '"')))
                        for _map in _obj.field_mapping:
                            _file_writer.writerow([_map.field_id.field_description or '' for _map in _obj.field_mapping if _map.field_id])

                        _file_stream.flush()
                        _file_stream.close()
                    elif _obj_vals.get('format_type', None) == 'method':
                        # Get the model and method, call the method passing the file name
                        # The method should return an iterable which members is dictionary
                        # compatible with ORM's write method
                        # _file_data = getattr(_mdl_pool, _obj.parse_method)()
                        pass
                    else:  # Unhandled format type
                        pass

                    # Make the log as attachment to the run log
                    _file_stream = open(_file_path)
                    _filecontent = _file_stream.read()
                    _file_stream.flush()
                    _file_stream.close()

                    _vals = {
                        'name': _file,
                        'datas': base64.encodestring(_filecontent),
                        'datas_fname': _file,
                        'res_model': context.get('res_model', False),
                        'res_id': context.get('res_id', False),
                    }
                    _new_att = _att_pool.create(cr, uid, _vals, context=context)
                    res[_obj.id].append(_new_att)
        return res

    def create(self, cr, uid, vals, context=None):
        self._validate_values(cr, uid, vals, context=context)
        return super(file_upload_import_config, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        for _obj in self.browse(cr, uid, ids, context=context):
            _model_id = vals.get('model_id', None) or (_obj.model_id and _obj.model_id.id) or False
            self._validate_values(cr, uid, vals, model_id=_model_id, context=context)

        return super(file_upload_import_config, self).write(cr, uid, ids, vals, context=context)

    def activate(self, cr, uid, ids, context=None):
        # Set the configuration to be effective so that it can be executed
        self.write(cr, uid, ids, {'effective': True}, context=context)
        return True

    def deactivate(self, cr, uid, ids, context=None):
        # Set the configuration to be effective so that it can be executed
        self.write(cr, uid, ids, {'effective': False}, context=context)
        return True

    _columns = {
        'name': fields.char('Name', size=64, select=True, required=True),
        'model_id': fields.many2one('ir.model', 'Master Model', required=True, select=True, help="The OSV Master Model that will be processed by this configuration.  The Model will hold the Import Hook Method if any."),
        'effective': fields.boolean('Effective', readonly=True),

        'frequency_int': fields.integer('Frequency', help="What is the running frequency by period.  In conjunction with frequency_period it specifies the frequency of running the scheme periodically."),
        'frequency_period': fields.selection(CRON_PERIOD, 'Period', required=True, help="What is the running frequency period.  In conjunction with frequency_int it specifies the frequency of running the scheme periodically."),
        'last_run': fields.datetime('Last Run', readonly=True, select=True, help="When a configuration is last run."),
        'next_run': fields.datetime('Next Run', readonly=True, select=True, help="When a configuration is scheduled to run next."),

        'working_folder': fields.char('Working Folder', required=True, help="A folder at the server where the files will be uploaded to and processed from."),
        'file_name_format': fields.char('File Name Format', required=True, help="Regular Expression representation of the file name format.  Parts will be parsed for further processing."),
        'log_name_format': fields.char('Log Name Format', required=True, help="Regular Expression representation of the log file name format."),
        'processed_name_format': fields.char('Processed Name Format', required=True, help="Regular Expression representation of the processed file name format."),

        'format_type': fields.selection(FORMAT_TYPE, 'Format Type', required=True, help="""
            How the uploaded file will be parsed:
            - Comma Separated Value: the file will be treated as Comma Separated Values and mapped by means of the Field Mapping,
            - Method Parsing: arbitrary format which will be parsed by the File Parse Method,
            """),
        'parse_method': fields.char('File Parse Method', help="The method that should be available in Master Model and will be called when the Upload is executed.  The signature should be def parse_method(cr, uid, config_id, context=context) where config_id is the this configuration's Database ID."),
        'csv_delim': fields.char('Column Delimiter', size=1, help="The character that is used to mark columns in the file."),
        'csv_quote': fields.char('Text Delimiter', size=1, help="The character that is used to surround text values in the file."),
        'csv_skip': fields.integer('Lines to Skip (e.g. Headers)', help="The number of lines to skip for processing."),
        'field_mapping': fields.one2many('file.upload.import.field.mapping', 'config_id', 'Field Mapping', help="List of field mapping for this configuration."),

        'import_handling': fields.selection(IMPORT_TYPE, 'Import Handling', required=True, help="""
            How the data will be imported or written:
            - Model Method: data will be imported through the Import Hook Method defined in the Master Model,
            - Python Code: data will be imported through the code provided in the Python Code.  TODO: What does the Python Code has access to?,
            """),
        'import_hook': fields.char('Import Hook Method', help="The method that should be available in Master Model and will be called when importing each record.  The signature should be def import_hook(cr, uid, file_name, vals, config_id, context=context) where config_id is the this configuration's Database ID."),
        'post_import_hook': fields.char('Post Import Hook Method', help="The method that should be available in Master Model and will be called after all records have been processed.  The signature should be def import_hook(cr, uid, config_id, context=context) where config_id is the this configuration's Database ID."),
        'python_code': fields.text('Python Code', help="Python code that will be used to import/save each record of data uploaded."),
        'post_python_code': fields.text('Post Python Code', help="Python code that will be called after all data is processed."),

        'failure_handling': fields.selection(FAILURE_HANDLING, 'Save On', required=True, help="""
            Controls when successful data is saved:
            - Sucessful File: save only if entire file can be processed successfully,
            - Sucessful Record: save only if entire record can be processed successfully,
            """),

        'run_logs': fields.one2many('file.upload.import.log', 'config_id', 'Run Logs', readonly=True),
    }

    _defaults = {
        'effective': lambda *a: False,
        'frequency_period': lambda *a: 'adhoc',
        'format_type': lambda *a: 'csv',
        'csv_delim': lambda *a: ',',
        'csv_quote': lambda *a: '"',
        'csv_skip': lambda *a: 0,
        'import_handling': lambda *a: 'method',
        'failure_handling': lambda *a: 'file',
    }


def _get_classic_fields_type():
    rs = [k for k, v in fields.__dict__.iteritems()
          if (isinstance(v, (types.TypeType, )) and
              issubclass(v, fields._column) and
              v != fields._column and
              not v._deprecated and
              v._classic_write and
              v._classic_read and
              not issubclass(v, fields.function))]
    rs.append('many2one')
    return rs

RECORD_MATCH = [
    ('id', 'Database ID'),
    ('xml_id', 'External ID'),
    ('name', 'Name Search'),
]


class file_upload_import_field_mapping(orm.Model):
    """
    Field Mapping to be used by file upload and import utility when the Format Type is Comma Separated Values
    """
    _name = 'file.upload.import.field.mapping'
    _description = 'File upload and import utility field mapping'
    _rec_name = "field_id"
    _order = 'config_id, sequence'

    def _validate_values(self, cr, uid, vals, context=None):
        """
        This method is used to validate the value dictionary (vals) to be used
        in write or create method.
        """
        # date_format is required if ttype is 'date' or 'datetime' and must be valid
        _value = vals.get('date_format', None)
        _value2 = vals.get('ttype', None)
        if _value2 in ('datetimviewe', 'date') and not _value:
            raise osv.except_osv(_('Error!'), _('Date Format is required for Field Type date and datetime!'))
        elif _value2 in ('datetime', 'date'):
            try:
                _check = dt.now()
                if _check.day != dt.strptime(_check.strftime(_value), _value).day:
                    raise osv.except_osv(_('Error!'), _('Date Format %s must contains at least one date directive.') % (_value))
            except osv.except_osv:
                raise
            except:
                raise osv.except_osv(_('Error!'), _('Date Format %s is not recognized!') % (_value))

        return True

    def create(self, cr, uid, vals, context=None):
        self._validate_values(cr, uid, vals, context=context)
        return super(file_upload_import_field_mapping, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        for _obj in self.browse(cr, uid, ids, context=context):
            _vals = self.copy_data(cr, uid, _obj.id, context=context)
            _vals.update(vals)
            self._validate_values(cr, uid, _vals, context=context)

        return super(file_upload_import_field_mapping, self).write(cr, uid, ids, vals, context=context)

    def onchange_field_id(self, cr, uid, ids, field_id, date_format, record_match, context=None):
        res = {'value': {}}
        if field_id:
            res['value'].update({'ttype': self.pool.get('ir.model.fields').browse(cr, uid, field_id, context=context).ttype})

        if res['value']['ttype'] not in ('date', 'datetime'):
            res['value'].update({'date_format': ''})
        else:
            res['value'].update({'date_format': date_format})

        if res['value']['ttype'] not in ('many2one'):
            res['value'].update({'record_match': ''})
        else:
            res['value'].update({'record_match': record_match or 'name'})

        return res

    _columns = {
        'config_id': fields.many2one('file.upload.import.config', 'Configuration', readonly=True, ondelete='cascade'),
        'model_id': fields.related('config_id', 'model_id', type='many2one', relation='ir.model', readonly=True, string='Master Model'),
        'sequence': fields.integer('Sequence', help="Sequence of the value to be mapped to this Field."),
        # Filter out field types that cannot be handled
        'field_id': fields.many2one('ir.model.fields', 'Field Name', domain="[('model_id', '=', model_id), ('ttype', 'in', ['%s'])]" % ("','".join(_get_classic_fields_type())), help="Master Model's Field that will be populated by the value."),
        'ttype': fields.related('field_id', 'ttype', string='Field Type', type="selection", selection=_get_fields_type, size=64),
        'date_format': fields.char('Date Format', size=64, help="The date format to interpret Date and DateTime fields.  Need to be a format that is understood by Python's strptime."),
        'record_match': fields.selection(RECORD_MATCH, 'Related Record Matching', help="""
            How related record (many2one) will be referenced in the file:
            - Database ID: the value is internal database ID corresponding to the record,
            - External ID: the value is external XML ID corresponding to the record,
            - Name Search: the value is a string that will be used to search the record by name_search,
            """),
        # 'name': fields.funtion(_get_name, size=64, readonly=True, required=True, help="Will be used as variable name for this formula."),
    }

    _defaults = {
    }

    _sql_constraints = [
        ('config_field_uniq', 'UNIQUE (config_id, field_id)', 'One field can only hold one value in one configuration!')
    ]


class file_upload_import_log(orm.Model):
    """
    File upload and import utility log holds the list of upload and import run.
    """
    _name = 'file.upload.import.log'
    _description = 'Log of file upload and import utility'
    _rec_name = 'run_time'
    _order = 'run_time DESC'

    def _models_get(self, cr, uid, context=None):
        res = set()
        _mdl_pool = self.pool.get('ir.model')
        for _mdl in _mdl_pool.search(cr, uid, [], context=context):
            _mdl_obj = _mdl_pool.browse(cr, uid, _mdl, context=context)
            res.add((_mdl_obj.model, _mdl_obj.name))
        return list(res)

    def _logfile_get(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}

        result = {}
        _att_pool = self.pool.get('ir.attachment')

        _ctx = context.copy()
        _ctx.update({'bin_size': (not bool(context.get('__ref', False))) and (len(context) > 0)})

        for _obj in self.browse(cr, uid, ids, context=context):
            # Look for the attachment
            _att_ids = _att_pool.search(cr, uid, [('res_model', '=', self._name), ('res_id', '=', _obj.id)], context=context)

            # Assume only 1 attachment
            _att = _att_ids and _att_pool.browse(cr, uid, _att_ids[0], context=_ctx)
            result[_obj.id] = _att and _att.datas or ''

        return result

    _columns = {
        'config_id': fields.many2one('file.upload.import.config', 'Configuration', readonly=True, ondelete='cascade'),
        'model_id': fields.many2one('ir.model', 'Master Model', required=True, select=True, help="The OSV Master Model that will be processed by this configuration.  The Model will hold the Import Hook Method if any."),
        'res_id': fields.reference('Resource', selection=_models_get, size=128, select=1),
        'run_time': fields.datetime('Executed On', readonly=True, select=True, help="When the upload and import is executed."),
        'working_folder': fields.char('Working Folder', required=True, help="A folder at the server where the files will be uploaded to and processed from."),
        'file_name': fields.char('File Name', size=256, readonly=True, required=True),
        'log_name': fields.char('Log File', size=256, readonly=True, required=True),
        'processed_file': fields.char('Processed File', size=256, readonly=True, required=True),
        'logfile_data': fields.function(_logfile_get, string='Log File', type="binary", nodrop=True),
    }
