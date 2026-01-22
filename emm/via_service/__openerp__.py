# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 - 2015 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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
    'name': 'VIA Service Request',
    'version': '1.3',
    'description': """
This module provides Service Request functionality.
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'hr',
        'product',
        'project',
        'sale',
        'stock',
        'via_form_templates',
        'document_page',
        'via_document_signature',
    ],
    'data': [
        'service_data.xml',
        'project_task_data.xml',
        'res_company_view.xml',
        'product_view.xml',
        'knowledge_view.xml',
        'hr_employee_view.xml',
        'stock_view.xml',
        'project_task_view.xml',
        'security/service_security.xml',
        'security/ir.model.access.csv',
        'service_sequence.xml',
        'service_view.xml',
        'spare_parts_view.xml',
        'service_fee_view.xml',
        'service_task_view.xml',
        'service_invoice_view.xml',
        'report/service_summary_view.xml',
        'report/form_pickup_sparepart.xml',
        'report/form_return_sparepart.xml',
        'report/form_service_task.xml',
        'report/proforma_invoice.xml',
        'report/form_service_work_order.xml',
        'report/form_work_order_description.xml',
        'report/form_service_history.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
