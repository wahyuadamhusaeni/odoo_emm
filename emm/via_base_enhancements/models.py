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

import logging

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import psycopg2

from openerp.osv import orm, fields
from openerp.osv.orm import BaseModel
from openerp.tools.translate import _
_logger = logging.getLogger(__name__)


def orm_method_exist(obj, cr, uid, model, validate_hook, context=None):
    # Check whether the method exist in the Model
    return model and validate_hook in dir(obj.pool.get(model) or []) or False


def get_object_from_xml(obj, cr, uid, xml, context=None):
    if xml:
        _mod = xml.split('.')
        if len(_mod) == 1:
            # If the given XML ID does not contain '.' assume that it does not specify module
            # and use this module name instead
            module = obj._module
        else:
            module = _mod[0]
            xml = _mod[1]

    if module and xml:
        return obj.pool.get('ir.model.data').get_object(cr, uid, module, xml, context=context)

    return False


class ir_import(orm.TransientModel):
    _inherit = 'base_import.import'

    def do(self, cr, uid, id, fields, options, dryrun=False, context=None):
        """
        This method incorporates changes merged into revision 9897 of
        ~openerp/openobject-addons/7.0 to handle the incorrect re-definition
        of load method by ir_translation.

        :param fields: import mapping: maps each column to a field,
                       ``False`` for the columns to ignore
        :type fields: list(str|bool)
        :param dict options:
        :param bool dryrun: performs all import operations (and
                            validations) but rollbacks writes, allows
                            getting as much errors as possible without
                            the risk of clobbering the database.
        :returns: A list of errors. If the list is empty the import
                  executed fully and correctly. If the list is
                  non-empty it contains dicts with 3 keys ``type`` the
                  type of error (``error|warning``); ``message`` the
                  error message associated with the error (a string)
                  and ``record`` the data which failed to import (or
                  ``false`` if that data isn't available or provided)
        :rtype: list({type, message, record})
        """
        cr.execute('SAVEPOINT import')

        (record,) = self.browse(cr, uid, [id], context=context)
        try:
            data, import_fields = self._convert_import_data(
                record, fields, options, context=context)
        except ValueError, e:
            return [{
                'type': 'error',
                'message': unicode(e),
                'record': False,
            }]

        _logger.info('importing %d rows...', len(data))
        # DO NOT FORWARD PORT, already fixed in trunk
        # hack to avoid to call the load method from ir_translation (name clash)
        if record.res_model == 'ir.translation':
            import_result = BaseModel.load(self.pool['ir.translation'], cr, uid, import_fields, data, context=context)
        else:
            import_result = self.pool[record.res_model].load(cr, uid, import_fields, data, context=context)
        _logger.info('done')

        # If transaction aborted, RELEASE SAVEPOINT is going to raise
        # an InternalError (ROLLBACK should work, maybe). Ignore that.
        # TODO: to handle multiple errors, create savepoint around
        #       write and release it in case of write error (after
        #       adding error to errors array) => can keep on trying to
        #       import stuff, and rollback at the end if there is any
        #       error in the results.
        try:
            if dryrun:
                cr.execute('ROLLBACK TO SAVEPOINT import')
            else:
                cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        return import_result['messages']
