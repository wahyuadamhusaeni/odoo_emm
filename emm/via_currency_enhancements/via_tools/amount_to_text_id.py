# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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

from tools.translate import _
from tools.amount_to_text import _translate_funcs, add_amount_to_text_function
from tools.amount_to_text_en import english_number
from via_l10n_id.via_tools.amount_to_text_id import indonesian_number
import logging
import inspect


_logger = logging.getLogger(__name__)


# Copied from via_l10n_id/via_tools/amount_to_text_id.py
# to be redefined to accept currency_obj

def amount_to_text_id(number, currency, currency_obj=False):
    number = '%.2f' % number
    list = str(number).split('.')
    start_word = indonesian_number(int(list[0]))
    end_word = indonesian_number(int(list[1]))
    cents_number = int(list[1])
    units_name = currency_obj and currency_obj.full_name or currency or ''
    cents_name = currency_obj and currency_obj.fraction_name or 'Sen'
    display_cents = True
    if currency_obj and not currency_obj.display_fraction:
        display_cents = False

    return ' '.join(filter(None, [start_word, units_name, (start_word or units_name) and ((end_word or cents_name) and ((cents_number > 0) or display_cents)) and 'and', ((cents_number > 0) or display_cents) and end_word, ((cents_number > 0) or display_cents) and cents_name]))


# Copied from via_l10n_id/via_tools/amount_to_text_id.py
# to be redefined to accept currency_obj

def amount_to_text_en(number, currency, currency_obj=False):
    number = '%.2f' % number
    list = str(number).split('.')
    start_word = english_number(int(list[0]))
    end_word = english_number(int(list[1]))
    cents_number = int(list[1])
    units_name = currency_obj and currency_obj.full_name or currency or ''
    cents_name = currency_obj and currency_obj.fraction_name or 'Cent' + ((cents_number > 1) and 's' or '')
    display_cents = True
    if currency_obj and not currency_obj.display_fraction:
        display_cents = False

    return ' '.join(filter(None, [start_word, units_name, (start_word or units_name) and ((end_word or cents_name) and ((cents_number > 0) or display_cents)) and 'and', ((cents_number > 0) or display_cents) and end_word, ((cents_number > 0) or display_cents) and cents_name]))


#-------------------------------------------------------------
# Generic functions
#-------------------------------------------------------------
add_amount_to_text_function('id', amount_to_text_id)
add_amount_to_text_function('en', amount_to_text_en)


def amount_to_text(nbr, lang='id', currency='Rupiah',  currency_obj=False):
    lang = lang[:2]
    if lang not in _translate_funcs:
        _logger.info(_("WARNING: no translation function found for lang: '%s'") % (lang,))

    _func_to_call = _translate_funcs[lang]
    _func_args = inspect.getargspec(_func_to_call).args
    if len(_func_args) == 3 and ('currency_obj' in _func_args) and currency_obj:
        return _func_to_call(abs(nbr), currency, currency_obj=currency_obj)
    else:
        # For backward compability
        return _func_to_call(abs(nbr), currency)
