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

{
    'name': 'VIA Document Signatory',
    'version': '1.4',
    'category': 'Hidden/Dependency',
    #'sequence': 19,
    'complexity': 'easy',
    'description': """
    Add the capability to register document signatories in companies per document type
     - Administration >> Company >> Company (Configuration Tab)

     The document signature can be obtained programmatically through the res.company object:
     - via get_signatory_by_doc_id(cr, uid, ids, doc_id, context=context)
       where ids is the company's id(s) and doc_id is the document type's id (code.decode object id)
     - via get_signatory_by_doc_name(cr, uid, ids, doc_name, context=context)
       where ids is the company's id(s) and doc_name is the document type's doc_name (code.decode object's code)
     - via get_signatory_by_xml(cr, uid, ids, module, xml_id, context=None)
       where ids is the company's id(s) and (module, xml_id) is a pair that uniquely identifies an object's XML ID (External Identifier).
       If the object with the specified XML ID is not found, then it will return empty string

     or through the document.signature object:
     - via get_signatory_by_doc_id(cr, uid, ids, doc_id, company_id, context=context)
       where doc_id is the document type's id (code.decode object id) and company_id is the company's id (one at a time)
     - via get_signatory(cr, uid, ids, doc_name, company_id, context=context)
       where doc_name is the document type's doc_name (code.decode object's code) and company_id is the company's id (one at a time)
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    #'images' : ['images/purchase_order.jpeg', 'images/purchase_analysis.jpeg', 'images/request_for_quotation.jpeg'],
    'depends': [
        'via_code_decode'
    ],
    'data': [
        'security/ir.model.access.csv',
        'document_signature_data.xml',
        'company_view.xml',
        'document_signature_view.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    #'certificate': '0057234283549',
    'application': False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
