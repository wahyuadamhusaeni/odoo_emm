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

from osv import osv, fields


class document_signature(osv.osv):
    _name = 'document.signature'
    _description = 'Document Signature'

    def _get_document_types(self, cr, uid, context=None):
        res = self.pool.get('code.decode').get_company_selection_for_category(cr, uid, 'via_document_signature', 'doc_signature_type_category', context=context)
        return res

    _columns = {
        'doc_type': fields.selection(_get_document_types, 'Document Type', required=True, help="Document type that will use selected user's signature"),
        'user_id': fields.many2one('res.users', 'User', readonly=False, required=True, help="The document will use this user signature"),
        'company_id': fields.many2one('res.company', 'Company', required=True, ondelete='cascade', select=True),
    }

    def get_signatory_by_doc_id(self, cr, uid, doc_id, company_id, context=None):
        _doc_type = self.pool.get('code.decode').read(cr, uid, doc_id, ['code'], context=context)
        _doc_type = _doc_type.get('code', '')
        return self.get_signatory(cr, uid, _doc_type, company_id, context=context)

    def get_signatory(self, cr, uid, document, company_id, context=None):
        _doc_pool = self.pool.get('document.signature')
        _doc_id = document and _doc_pool.search(cr, uid, [('doc_type', '=', document), ('company_id', '=', company_id)]) or []
        usr = _doc_id and _doc_pool.browse(cr, uid, _doc_id[0], context=context) or False
        return usr and usr.user_id or False

document_signature()
