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

from osv import osv, fields
from tools.translate import _
from via_jasper_report_utils.framework import register_report_wizard, wizard


RPT_NAME = 'Account by Product'

report_sql = """
WITH transactions AS (
   SELECT
     aml.product_id AS product_id,
     aml.company_id AS company_id,
     aml.account_id AS account_id,
     aml.prod_lot_id AS serial_number_id,
     pp.default_code AS product_code,
     pp.name_template AS product_name,
     rc.name AS company,
     aa.code AS account_code,
     aa.name AS account_name,
     spl.name AS serial_number,
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
     LEFT JOIN product_product pp ON (pp.id = aml.product_id)
     LEFT JOIN res_company rc ON (rc.id = aml.company_id)
     LEFT JOIN stock_production_lot spl ON (aml.prod_lot_id = spl.id)
     JOIN account_account aa ON (aa.id = aml.account_id)
     JOIN account_period ap ON (ap.id = aml.period_id)
     JOIN account_journal aj ON (aml.journal_id = aj.id AND aj.type != 'situation')
   WHERE
     aml.date <= $P{TO_DATE_2} --To Date
     AND (aml.product_id IN ($P!{PROD_IDS})
          OR aml.product_id IS NULL) --Product IDs
     AND aml.account_id IN ($P!{ACC_IDS}) --Account IDs
)

SELECT
    COALESCE(trl.product_code, bgp.product_code) AS product_code,
    COALESCE(trl.product_name, bgp.product_name) AS product_name,
    COALESCE(trl.account_code, bgp.account_code) AS account_code,
    COALESCE(trl.account_name, bgp.account_name) AS account_name,
    COALESCE(bgp.begin_debit, 0.0) AS begin_debit,
    COALESCE(bgp.begin_credit, 0.0) AS begin_credit,
    COALESCE(bgp.begin_balance, 0.0) AS begin_balance,
    serial_number,
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
  (--beginning balance per product bgp
   SELECT
     product_id,
     company_id,
     account_id,
     product_code,
     product_name,
     account_code,
     account_name,
     SUM(COALESCE(debit,0)) AS begin_debit,
     SUM(COALESCE(credit,0)) AS begin_credit,
     SUM(COALESCE(debit,0) - COALESCE(credit,0)) AS begin_balance
   FROM
transactions
   WHERE
     date < $P{FROM_DATE_2}
   GROUP BY
     product_id,
     company_id,
     account_id,
     product_code,
     product_name,
     account_code,
     account_name
  ) bgp ON (trl.product_id = bgp.product_id AND trl.company_id = bgp.company_id AND trl.account_id = bgp.account_id)
  WHERE (begin_balance != 0 OR balance IS NOT NULL)
  ORDER BY COALESCE(bgp.company_id, trl.company_id),
           COALESCE(bgp.product_code, trl.product_code),
           COALESCE(bgp.account_code, trl.account_code),
           date,
           serial_number
"""


class via_jasper_report(osv.osv_memory):
    _inherit = 'via.jasper.report'
    _description = 'Account by Product'

    _columns = {
    }

    _defaults = {
    }

via_jasper_report()


class wizard(wizard):

    #code below used to reset the acc_ids and prod_ids when there is a change in company_id
    def onchange_company_id(cr, uid, ids, com_id, context=None):
        if com_id is None:
            return {
                'domain': {'acc_ids': [('type', 'not in', ['view', 'consolidation']), ('company_id', '=', False)], 'prod_ids': [('company_id', '=', False)]},
                'value': {'acc_ids': False, 'prod_ids': False},
            }
        return {
            'domain': {'acc_ids': [('type', 'not in', ['view', 'consolidation']), '|', ('company_id', 'child_of', com_id), ('company_id', '=', False)], 'prod_ids': ['|', ('company_id', 'child_of', com_id), ('company_id', '=', False)]},
            'value': {'acc_ids': False, 'prod_ids': False},
        }

    _onchange = {
        'company_id': (onchange_company_id, 'company_id', 'context'),
    }

    _visibility = [
        'company_id',
        ['from_dt', 'to_dt'],
        'acc_ids',
        'prod_ids',
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
        'prod_ids': 'Products'
    }

    _domain = {
        'acc_ids': "[('type','not in',['view','consolidation']), '|',('company_id','child_of',company_id),('company_id','=',False)]",
        'prod_ids': "['|',('company_id','child_of',company_id),('company_id','=',False)]",
    }

    _tree_columns = {
        'prod_ids': ['name'],
    }

    def validate_parameters(self, cr, uid, form, context=None):
        if len(str(form.company_id.id)) == 0:
            raise osv.except_osv(_('Caution !'),
                                _('No page will be printed !'))

    def print_report(self, cr, uid, form, context=None):
        self.validate_parameters(cr, uid, form, context=context)

        temp = []
        temp_name = []
        limit = 18
        #code below used to return all the ids and the name of all the accounts related to the selected company
        if len(form.acc_ids) == 0:
            temp = self.pool.get('account.account').search(cr, uid, [('type', 'not in', ['view', 'consolidation']), '|', ('company_id', 'child_of', form.company_id.id), ('company_id', '=', False)])
            temp.append(0)
            acc_ids = ",".join(str(n) for n in temp)
            acc_names = "ALL"
            form.add_marshalled_data('ACC_IDS', acc_ids)
        else:
            for account in form.acc_ids:
                if (account.code + '' + account.name) not in temp_name:
                    temp_name.append(account.code + ' ' + account.name)
            temp_name = list(set(temp_name))
            acc_names = ", ".join(str(n) for n in temp_name[:limit]) + (len(temp_name) > limit and " ..." or '')

        crit = []
        crit_name = []
        #code below used to return all the ids and the name of all the products related to the selected company
        if len(form.prod_ids) == 0:
            crit = self.pool.get('product.product').search(cr, uid, ['|', ('company_id', '=', False), ('company_id', 'child_of', form.company_id.id)])
            crit.append(0)
            prod_ids = ",".join(str(n) for n in crit)
            product_names = "ALL"
            form.add_marshalled_data('PROD_IDS', prod_ids)
        else:
            for product in form.prod_ids:
                if product.code:
                    if ('[' + product.code + ']' + ' ' + product.name) not in crit_name:
                        crit_name.append('[' + product.code + ']' + ' ' + product.name)
                else:
                    if (product.name) not in crit_name:
                        crit_name.append(product.name)
            crit_name = list(set(crit_name))
            product_names = ", ".join(str(n) for n in crit_name[:limit]) + (len(crit_name) > limit and " ..." or '')

        #code below used to pass the variable into the parameter in the jrxml file
        form.add_marshalled_data('REPORT_SQL', report_sql)
        form.add_marshalled_data('ACC_NAMES', acc_names)
        form.add_marshalled_data('PRODUCT_NAMES', product_names)

register_report_wizard(RPT_NAME, wizard)
