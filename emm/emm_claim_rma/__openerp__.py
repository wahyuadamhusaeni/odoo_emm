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
    'name': "RMA for PT Eka Maju Mesinindo",
    'version': '1.1',
    'category': 'Customer Relationship Management',
    'description': """
    Provide Return Merchandise Authorization (RMA) functionality.
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'via_account_invoice_refund',
        'sale',
        'crm_claim',
        'emm_stock_enhancements',
    ],
    'data': [
        'crm_claim_rma_parameters.xml',
        'wizard/account_invoice_refund_view.xml',
        'wizard/claim_make_picking_view.xml',
        'wizard/claim_move_history_view.xml',
        'res_partner_view.xml',
        'account_invoice_view.xml',
        'stock_view.xml',
        'crm_claim_rma_view.xml',
        'report/incoming_shipment_form_template.xml',
    ],
    'images': [
    ],
    'installable': True,
    'auto_install': False,
}
