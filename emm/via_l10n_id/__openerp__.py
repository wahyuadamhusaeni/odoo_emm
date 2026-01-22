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
    'name': 'VIA Indonesian Localisation (L10N)',
    'version': '1.1',
    'category': 'Hidden/Dependency',
    'complexity': 'normal',
    'description': """
    This module provides various enhancements that is specific to Indonesian market:
    * Tool for converting numbers to Indonesian language:
      To use the functions, import it through 'from via_l10n_id import amount_to_text_id'
      - amount_to_text(number, currency='Rupiah', cents_name='Sen') is used to convert
        decimal numbers to a currency compatible said amount. It will only process
        2 decimal points in which it is treated as cents
        (e.g. 123.02 is 'Seratus Dua Puluh Tiga Rupiah Dua Sen')
      - number_to_text(number) is used to convert decimal numbers to Indonesian language representation.
        It differs from amount_to_text in that it does not spell out the currency and cents
        (e.g 123.02 is 'Seratus Dua Puluh Tiga koma Nol Dua')
      - number_to_day(number) will provide the Indonesian day of week names, with 0 = Minggu.
      - number_to_month(number) will provide the Indonesian month names, with 1 = Januari.
    """,
    'author': 'Vikasa Infinity Anugrah, PT',
    'website': 'http://www.infi-nity.com',
    'depends': ['base', 'account'],
    'data': [
        'data/res.country.state.csv',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
