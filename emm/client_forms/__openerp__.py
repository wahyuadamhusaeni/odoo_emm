# -*- encoding: utf-8 -*-
###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
#
###############################################################################

{
    'name': 'Client Forms',
    'version': '1.0',
    'category': 'Forms',
    'description': """
    This module provides Client forms.
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'images': [],
    'depends': [
        'via_form_templates',
        'via_document_signature',
        'client_signatories',
        'sale_stock',
        'purchase',
    ],
    'data': [
        'report/faktur_id.xml',
        'report/faktur_en.xml',
        'report/nota_terima_id.xml',
        'report/nota_terima_en.xml',
        'report/kwitansi_id.xml',
        'report/kwitansi_en.xml',
        'report/order_pembelian_id.xml',
        'report/order_pembelian_en.xml',
        'report/quotation_en.xml',
        'report/quotation_id.xml',
        'report/permintaan_penawaran_id.xml',
        'report/permintaan_penawaran_en.xml',
        'report/order_penjualan_id.xml',
        'report/order_penjualan_en.xml',
        'report/surat_jalan_id.xml',
        'report/surat_jalan_en.xml',
        'report/packing_list_id.xml',
        'report/packing_list_en.xml',
        'report/daftar_pengambilan_barang.xml',
        'report/daftar_pengumpulan_barang.xml',
    ],

    'test': [
    ],
    'demo': [
    ],
    'license': 'GPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
