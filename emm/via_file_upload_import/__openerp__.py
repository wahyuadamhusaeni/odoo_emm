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
    'name': 'File Upload and Import Utility',
    'version': '0.1',
    'author': 'Vikasa Infinity Anugrah, PT',
    'description': """
This module provide a facility to create a configurable file upload and import processing.
User has the option to run the file upload and import with various options:

- Format Type: whether the file is a Comma Separated Value (interpreted through field mapping) or an arbitrary file format that will be parsed by a parsing method available in the Model
- Import Handling: whether the data from the uploaded file will be saved by a method in the Model or by Python Code configured.
- When data will be saved: upon successful processing of a record or a file.
    """,
    'website': '',
    'license': 'GPL-3',
    'category': 'Tools',
    'depends': [
        'base'
    ],
    'init_xml': [],
    'demo_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'file_upload_import_view_70.xml',
    ],
    'active': False,
    'installable': True,
}
