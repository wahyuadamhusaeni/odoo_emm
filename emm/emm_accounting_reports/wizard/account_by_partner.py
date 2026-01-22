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

from osv import orm, fields
from tools.translate import _
from via_jasper_report_utils.framework import register_report_wizard, wizard


RPT_NAME = 'Account by Partner'

report_sql = """
WITH transactions AS (
   SELECT
     aml.partner_id AS partner_id,
     aml.company_id AS company_id,
     aml.account_id AS account_id,
     rp.name AS partner,
     rc.name AS company,
     aa.code || '' || aa.name AS account,
     ap.name AS period,
     aml.date AS date,
     aj.code AS journal,
     am.name AS entry,
     aml.name AS description,
     COALESCE(aml.debit,0) AS debit,
     COALESCE(aml.credit,0) AS credit,
     COALESCE(aml.debit,0) - COALESCE(aml.credit,0) AS balance
   FROM
     account_move_line aml
     JOIN account_move am ON (am.id = aml.move_id AND am.state = 'posted')
     LEFT JOIN res_partner rp ON (rp.id = aml.partner_id)
     LEFT JOIN res_company rc ON (rc.id = aml.company_id)
     JOIN account_account aa ON (aa.id = aml.account_id)
     JOIN account_period ap ON (ap.id = aml.period_id)
     JOIN account_journal aj ON (aml.journal_id = aj.id AND aj.type != 'situation')
   WHERE
     aml.date <= $P{TO_DATE_2} --To Date
     AND aml.partner_id IN ($P!{CUSTOMER_IDS}) --Partner IDs
     AND aml.account_id IN ($P!{ACC_IDS}) --Account IDs
)
SELECT
    COALESCE(trl.partner, bgp.partner) AS partner,
    COALESCE(trl.account, bgp.account) AS account,
    COALESCE(bgp.begin_debit, 0.0) AS begin_debit,
    COALESCE(bgp.begin_credit, 0.0) AS begin_credit,
    COALESCE(bgp.begin_balance, 0.0) AS begin_balance,
    period,
    date,
    journal,
    entry,
    description,
    debit,
    credit,
    balance
  FROM
  (--detailed transaction line tr
  SELECT *
   FROM
     transactions
   WHERE
     date BETWEEN $P{FROM_DATE_2} AND $P{TO_DATE_2}
  ) trl
  FULL JOIN
  (--beginning balance per partner bgp
   SELECT
     partner_id,
     company_id,
     account_id,
     partner,
     account,
     SUM(COALESCE(debit,0)) AS begin_debit,
     SUM(COALESCE(credit,0)) AS begin_credit,
     SUM(COALESCE(debit,0) - COALESCE(credit,0)) AS begin_balance
   FROM
     transactions
   WHERE
     date <= $P{FROM_DATE_2}
   GROUP BY
     partner_id,
     company_id,
     account_id,
     partner,
     account
  ) bgp ON (trl.partner_id = bgp.partner_id AND trl.company_id = bgp.company_id AND trl.account_id = bgp.account_id)
  WHERE (begin_balance != 0 OR balance IS NOT NULL)
  ORDER BY COALESCE(bgp.company_id, trl.company_id),
           COALESCE(trl.partner_id, bgp.partner_id),
           COALESCE(bgp.account_id, trl.account_id),
           date
"""


class via_jasper_report(orm.TransientModel):
    _inherit = 'via.jasper.report'
    _description = 'Account by Partner'

    _columns = {
    }

    _defaults = {
    }

via_jasper_report()


class wizard(wizard):

    #code below used to reset the acc_ids and customer_ids when there is a change in company_id
    def onchange_company_id(cr, uid, ids, com_id, context=None):
        if com_id is None:
            return {
                'domain': {
                    'acc_ids': [('type', 'not in', ['view', 'consolidation']), ('company_id', '=', False)],
                    'customer_ids': [('company_id', '=', False)],
                },
                'value': {'acc_ids': False, 'customer_ids': False},
            }
        return {
            'domain': {
                'acc_ids': [('type', 'not in', ['view', 'consolidation']), '|', ('company_id', 'child_of', com_id), ('company_id', '=', False)],
                'customer_ids': ['|', ('company_id', 'child_of', com_id), ('company_id', '=', False)]
            },
            'value': {'acc_ids': False, 'customer_ids': False},
        }

    _onchange = {
        'company_id': (onchange_company_id, 'company_id', 'context'),
    }

    _visibility = [
        'company_id',
        ['from_dt', 'to_dt'],
        'acc_ids',
        'customer_ids',
    ]

    _required = [
        'company_id',
        'from_dt',
        'to_dt',
    ]

    _attrs = {
    }

    _label = {
        'from_dt': 'Date From',
        'customer_ids': 'Partners'
    }

    _domain = {
        'acc_ids': "[('type','not in',['view','consolidation']), '|',('company_id','child_of',company_id),('company_id','=',False)]",
        'customer_ids': "['|',('company_id','child_of',company_id),('company_id','=',False)]",
    }

    def validate_parameters(self, cr, uid, form, context=None):
        if len(str(form.company_id.id)) == 0:
            raise orm.except_orm(_('Caution !'),
                                 _('No page will be printed !'))

    def print_report(self, cr, uid, form, context=None):
        self.validate_parameters(cr, uid, form, context=context)

        temp = []
        temp_name = []
        limit = 18  # Length limit of the account name and customer name shown in the report
        # Code below used to return all the ids and the name of all the accounts related to the selected company
        if len(form.acc_ids) == 0:
            _dom = [('type', 'not in', ['view', 'consolidation']), '|', ('company_id', 'child_of', form.company_id.id), ('company_id', '=', False)]
            temp = self.pool.get('account.account').search(cr, uid, _dom)
            temp.append(0)
            acc_ids = ",".join(str(n) for n in temp)
            acc_names = "ALL"
            form.add_marshalled_data('ACC_IDS', acc_ids)
        else:
            for account in form.acc_ids:
                if (account.code + '' + account.name) not in temp_name:
                    temp_name.append(account.code + '' + account.name)
            temp_name = list(set(temp_name))
            acc_names = ", ".join(str(n) for n in temp_name[:limit]) + (len(temp_name) > limit and " ..." or '')

        crit = []
        crit_name = []
        #code below used to return all the ids and the name of all the customers related to the selected company
        if len(form.customer_ids) == 0:
            _dom = ['|', ('company_id', '=', False), ('company_id', 'child_of', form.company_id.id)]
            crit = self.pool.get('res.partner').search(cr, uid, _dom)
            crit.append(0)
            customer_ids = ",".join(str(n) for n in crit)
            customer_names = "ALL"
            form.add_marshalled_data('CUSTOMER_IDS', customer_ids)
        else:
            for customer in form.customer_ids:
                if customer.name not in crit_name:
                    crit_name.append(customer.name)
            crit_name = list(set(crit_name))
            customer_names = ", ".join(str(n) for n in crit_name[:limit]) + (len(crit_name) > limit and " ..." or '')

        #code below used to pass the variable into the parameter in the jrxml file
        form.add_marshalled_data('REPORT_SQL', report_sql)
        form.add_marshalled_data('ACC_NAMES', acc_names)
        form.add_marshalled_data('CUSTOMER_NAMES', customer_names)

register_report_wizard(RPT_NAME, wizard)
