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

from osv import orm, fields
from tools.translate import _
from account_receivable_report_by_customer_sql import ar_cust_sql
from via_jasper_report_utils.framework import register_report_wizard, wizard
from via_reporting_utility.pgsql import list_to_pgTable


RPT_NAME = 'Account Receivable Report By Customer'


class via_jasper_report(orm.TransientModel):
    _inherit = 'via.jasper.report'
    _description = 'Account Receivable Report By Customer'

    _columns = {
    }

    _defaults = {
    }

via_jasper_report()


class wizard(wizard):
    def onchange_company_ids(cr, uid, ids, com_ids, context=None):
        # Sample com_ids = [(6, 0, [14, 11])]
        if len(com_ids) == 0:
            return {
                'domain': {
                    'customer_ids': [('company_id', '=', False), ('customer', '=', True)],
                },
                'value': {'customer_ids': False},
            }
        return {
            'domain': {
                'customer_ids': [('company_id', 'in', com_ids[0][2]), ('customer', '=', True)],
            },
            'value': {'customer_ids': False},
        }

    _onchange = {
        'company_ids': (onchange_company_ids, 'company_ids', 'context'),
    }

    _visibility = [
        'company_ids',
        'customer_ids',
        ['from_dt', 'to_dt'],
    ]

    _required = [
        'from_dt',
        'to_dt',
    ]

    _readonly = [
    ]

    _attrs = {
    }

    _domain = {
    }

    _label = {
        'from_dt': 'Invoice Date From',
    }

    _defaults = {
    }

    _states = [
    ]

    _tree_columns = {
    }

    def get_receivable(self, cr, uid, form, context=None):
        cust_ids = form.get_customer_ids(context=context)
        sql_receive = """
            SELECT
                aml.partner_id,
                COALESCE(sum(COALESCE(aml.debit, 0.0) - COALESCE(aml.credit, 0.0)), 0.0)
            FROM
                account_move_line aml
            JOIN
                account_account aa ON (aa.id = aml.account_id AND aa.type IN ('receivable'))
            WHERE
                aml.partner_id IN (%s)
            GROUP BY
                aml.partner_id,
                aml.account_id
        """
        cr.execute(sql_receive % (','.join(str(cust_id) for cust_id in cust_ids),))
        rv = cr.fetchall()
        return rv

    def get_payable(self, cr, uid, form, context=None):
        cust_ids = form.get_customer_ids(context=context)
        sql_receive = """
            SELECT
                aml.partner_id,
                COALESCE(sum(COALESCE(aml.credit, 0.0) - COALESCE(aml.debit, 0.0)), 0.0)
            FROM
                account_move_line aml
            WHERE
                aml.partner_id IN (%s)
                AND aml.account_id IN (
                    SELECT
                        id
                    FROM
                        account_account
                    WHERE
                        type IN ('payable')
                    UNION
                    SELECT
                        rc.payment_holding_account
                    FROM
                        res_company rc
                    WHERE
                        rc.id IN (%s)
                    )
            GROUP BY
                aml.partner_id
        """
        cr.execute(sql_receive % (','.join(str(cust_id) for cust_id in cust_ids),
                                  ','.join(str(com_id.id) for com_id in form.company_ids),))
        rv = cr.fetchall()
        return rv

    def get_currency_company(self, cr, uid, form, context=None):
        sql_curr_comp = """
            SELECT
                rcu.symbol
            FROM
                res_company rc
            JOIN
                res_currency rcu ON rcu.id = rc.currency_id
            WHERE
                rc.id IN (%s)
        """
        cr.execute(sql_curr_comp % (','.join(str(com_id.id) for com_id in form.company_ids),))
        rv = cr.fetchall()
        if len(rv):
            for item in rv:
                rv = item[0]
        return rv

    def validate_parameters(self, cr, uid, form, context=None):
        if len(form.company_ids) == 0:
            raise orm.except_orm(_('Caution !'),
                                 _('No page will be printed !'))

    def print_report(self, cr, uid, form, context=None):
        self.validate_parameters(cr, uid, form, context=context)
        form.add_marshalled_data('SQL_PARAMS', ar_cust_sql())
        if len(form.customer_ids) == 0:
            #TODO: Nothing
            sql_cust_ids = ''
        else:
            cust_list = form.get_customer_ids(context=None)
            cust_ids = ",".join(str(n) for n in cust_list)
            sql_cust_ids = ' AND id.partner IN (%s)' % cust_ids
        form.add_marshalled_data('CUSTOMER_IDS', sql_cust_ids)
        receivable = self.get_receivable(cr, uid, form, context=context)
        receivable_table = list_to_pgTable(
            receivable,
            'receivable_table',
            [('partner_id', 'INTEGER'),
             ('receivable', 'NUMERIC')]
        )
        form.add_marshalled_data('RECEIVABLE_TABLE', receivable_table)
        payable = self.get_payable(cr, uid, form, context=context)
        payable_table = list_to_pgTable(
            payable,
            'payable_table',
            [('partner_id', 'INTEGER'),
             ('payable', 'NUMERIC')]
        )
        form.add_marshalled_data('PAYABLE_TABLE', payable_table)
        currency_company = self.get_currency_company(cr, uid, form, context=context)
        form.add_marshalled_data('CURRENCY_SYMBOL', currency_company)

register_report_wizard(RPT_NAME, wizard)
