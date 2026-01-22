# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
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

from osv import osv
from osv import fields
import logging


_logger = logging.getLogger(__name__)


class res_company(osv.osv):
    _inherit = 'res.company'

    def get_signatory_by_doc_id(self, cr, uid, ids, doc_id, context=None):
        if not context:
            context = {}
        _doc_type = self.pool.get('code.decode').read(cr, uid, doc_id, ['code'], context=context)
        _doc_type = _doc_type.get('code', '')
        res = self.get_signatory_by_doc_name(cr, uid, ids, _doc_type, context=context)
        return res

    def get_signatory_by_doc_name(self, cr, uid, ids, doc_name, context=None):
        res = {}
        if not context:
            context = {}
        if isinstance(ids, (list, tuple, dict, )):
            select = list(ids)
        else:
            select = [ids]

        _doc_pool = self.pool.get('document.signature')
        for _obj in self.pool.get('res.company').browse(cr, uid, select, context=context):
            res[_obj.id] = _doc_pool.get_signatory(cr, uid, doc_name, _obj.id, context=context)

        if isinstance(ids, (int, long, )):
            return res[ids]
        else:
            return res

    def get_signatory_by_xml(self, cr, uid, ids, module, xml_id, context=None):
        res = {}
        if not context:
            context = {}
        if isinstance(ids, (list, tuple, dict, )):
            select = list(ids)
        else:
            select = [ids]

        _imd_pool = self.pool.get('ir.model.data')
        for _obj in self.pool.get('res.company').browse(cr, uid, select, context=context):
            _doc_id = False
            try:
                _doc_id = _imd_pool.get_object_reference(cr, uid, module, xml_id)
            except ValueError:
                _logger.error("External Identifier %s.%s is not found.", module, xml_id)
            except:
                raise
            _coy_po_sig = _doc_id and _obj.get_signatory_by_doc_id(_doc_id[1]) or False
            res[_obj.id] = _coy_po_sig and _coy_po_sig.signature or ''

        if isinstance(ids, (int, long, )):
            return res[ids]
        else:
            return res

    _columns = {
        'document_signature': fields.one2many('document.signature', 'company_id', 'Documents Signature'),
    }

res_company()
