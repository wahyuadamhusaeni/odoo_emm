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
    'name': 'VIA Web Theme',
    'version': '1.1',
    'category': 'Hidden',
    'description': """
- Customization of web module for PT Vikasa Infinity Anugrah:
  * Setting favicon
  * Default nologo.png to Infinity's Logo
- Provision of common web libraries and enhancements:
  * jQuery Barcode Plugin
  * Ported numberFormat from version 2.3.2 of underscore.string
  * Bootstraping the proper CultureInfo for datejs
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': [
        'web',
    ],
    'js': [
        'static/src/js/via_web.js',
        'static/src/js/jquery-barcode.min.js',
        # 'static/src/js/jquery-barcode.js',
        'static/src/js/qrcode.js',
        'static/src/js/jquery.qrcode.min.js',
        # 'static/src/js/jquery.qrcode.js',
    ],
    'css': [
        'static/src/css/via_web.css',
    ],
    'qweb': [
        'static/src/xml/via_web*.xml',
    ],
    'auto_install': True,
}
