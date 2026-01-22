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
    'name': 'Barcode Batch Processing for PT Eka Maju Mesinindo',
    'version': '1.0',
    'author': 'Vikasa Infinity Anugrah, PT',
    'description': """
This module provide the necessary configurations, menu and wizards related
to file upload and import.
    """,
    'website': '',
    'license': 'GPL-3',
    'category': 'Tools',
    'depends': [
        'via_file_upload_import',
        'emm_stock_enhancements',
    ],
    'init_xml': [],
    'demo_xml': [],
    'update_xml': [
        'wizard/file_upload_import_wiz_view.xml',
        'wizard/file_upload_import_all_wiz_view.xml',
        'wizard/file_download_template_wiz_view.xml',
        'stock_data.xml',
    ],
    'active': False,
    'installable': True,
}
