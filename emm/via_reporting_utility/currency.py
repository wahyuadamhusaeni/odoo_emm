###############################################################################
#
#    Vikasa Infinity Anugrah, PT
#  Copyright (C) 2011 - 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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
###############################################################################

try:
    import release
    from osv import osv
    import pooler
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import osv
    from openerp import pooler

from pgsql import create_composite_type, create_plpgsql_proc
from currency_sql import _VIA_CURRENCY_CONVERTER_DEF

class via_reporting_currency(osv.osv):
    _name = 'via.reporting.currency'
    _auto = False
    _description = 'VIA Reporting Utility For Currency'

    def _auto_init(self, cr, context=None):
        super(via_reporting_currency, self)._auto_init(cr, context=context)
        create_composite_type(cr, 'via_currency_rate',
                              [('date_start', 'DATE'),
                               ('date_stop', 'DATE'),
                               ('rate', 'NUMERIC')])
        create_composite_type(cr, 'via_currency_link',
                              [('level', 'BIGINT'),
                               ('currency_id', 'BIGINT'),
                               ('currency_rates', 'VIA_CURRENCY_RATE[]'),
                               ('consolidating_currency_id', 'BIGINT'),
                               ('consolidating_currency_rates', 'VIA_CURRENCY_RATE[]')])
        create_plpgsql_proc(cr, 'via_currency_converter',
                            [('IN', 'amount', 'NUMERIC'),
                             ('IN', 'rates_chain', 'VIA_CURRENCY_LINK[]'),
                             ('IN', 'conversion_date', 'DATE'),],
                            'NUMERIC',
                            _VIA_CURRENCY_CONVERTER_DEF)

via_reporting_currency()


def get_currency_toolkit(cr, uid, to_currency, context=None):
    currency_pool = pooler.get_pool(cr.dbname).get('res.currency')
    if isinstance(to_currency, (int, long)):
        to_curr_id = to_currency
        to_curr = currency_pool.browse(cr, uid, to_curr_id, context=context)
    else:
        to_curr = to_currency
        to_curr_id = to_currency.id

    def currency_normalizer(from_curr_id, amount):
        return currency_pool.compute(cr, uid, from_curr_id, to_curr_id,
                                     amount, context)
    def currency_rounder(amount):
        return currency_pool.round(cr, uid, to_curr, amount)
    def currency_is_zero(amount):
        return currency_pool.is_zero(cr, uid, to_curr, amount)

    return (currency_normalizer, currency_rounder, currency_is_zero)

def chained_currency_converter(currency_list, amount, date):
    '''Given a currency list containing pairs of objects from OERP
    model res.currency like [(JPY COM E, SGD COM E), (SGD COM D, USD
    COM D)], return the amount converted to SGD COM E from JPY COM E,
    and then treating the result to be in SGD COM D, it is converted
    to USD COM D. At each conversion, the most recent rate with regard
    to the given date is used.
    '''
    if len(currency_list) == 0 or amount == 0.0:
        return amount
    return currency_list[-1][0].compute(currency_list[-1][1].id,
                                        chained_currency_converter(currency_list[:-1],
                                                                   amount,
                                                                   date),
                                        round=False,
                                        context={'date': date})

# The following inheritance is needed to make
# currency_list[-2].compute(...)  works because it turns out that
# orm.py:class browse_record always passes a list of integers while
# method compute of res_currency.py is not smart enough to extract the
# sole member of the list.
class res_currency(osv.osv):
    _inherit = 'res.currency'

    if float(release.major_version) >= 6.1:
        def compute(self, cr, uid, from_currency_id, to_currency_id, from_amount,
                    round=True, currency_rate_type_from=False, currency_rate_type_to=False, context=None):
            if isinstance(from_currency_id, list):
                from_currency_id = from_currency_id[0]
            return super(res_currency, self).compute(cr, uid, from_currency_id, to_currency_id, from_amount,
                    round=round, currency_rate_type_from=currency_rate_type_from,
                    currency_rate_type_to=currency_rate_type_to, context=context)
    elif float(release.major_version) == 6.0:
        def compute(self, cr, uid, from_currency_id, to_currency_id, from_amount,
                    round=True, context=None):
            if isinstance(from_currency_id, list):
                from_currency_id = from_currency_id[0]
            return super(res_currency, self).compute(cr, uid, from_currency_id,
                                                     to_currency_id, from_amount,
                                                     round=round, context=context)

res_currency()
