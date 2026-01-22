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
    'name': 'Indonesian Tax Form',
    'version': '1.9',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'description': """
    Feature to produce and print Indonesian Taxforms:
    - Faktur Pajak PPN
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'via_partner_enhancements',
        'via_document_signature',
        'via_account_enhancements',
        'via_code_decode',
        'via_form_templates',
    ],
    'data': [
        'security/ir.model.access.csv',
        'account_taxform_data.xml',
        'report/template_headers.xml',
        'wizard/account_taxform_create_new_sequence.xml',
        'wizard/account_taxform_select_existing_sequence.xml',
        'wizard/account_invoice_createtaxform.xml',
        'report/account_taxform_report.xml',
        'account_taxform_taxes_view.xml',
        'account_tax_view.xml',
        'account_taxform_view.xml',
        'account_taxform_line_view.xml',
        'account_invoice_view.xml',
        'company_view.xml',
        'res_partner_view.xml',
        'account_taxform_reusable_sequences_view.xml',
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
