###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

try:
    import release
    import pooler
    from osv import fields, osv
    from tools.translate import _
except ImportError:
    import openerp
    from openerp import release
    from openerp import pooler
    from openerp.osv import fields, osv
    from openerp.tools.translate import _

from wizard.account_tree import account_tree


class res_company(osv.osv):
    _name = 'res.company'
    _inherit = 'res.company'
    _description = 'VIA Financial Reports res.company'
    _columns = {
        'asset_head_account': fields.many2one(
            'account.account',
            'Asset Head Account',
            domain="[('type', '=', 'view')]",
            help=("This account is the head account of a group of asset accounts"
                  " to be reported in the asset part of VIA Combined Balance"
                  " Sheet report.")),
        'liability_head_account': fields.many2one(
            'account.account',
            'Liability Head Account',
            domain="[('type', '=', 'view')]",
            help=("This account is the head account of a group of liability"
                  " accounts to be reported in the liability part of VIA"
                  " Combined Balance Sheet report.")),
        'income_head_account': fields.many2one(
            'account.account',
            'Income Head Account',
            domain="[('type', '=', 'view')]",
            help=("This account is the head account of a group of income"
                  " accounts to be reported in the income part of VIA Combined"
                  " Balance Sheet and VIA Combined Profit/Loss reports.")),
        'expense_head_account': fields.many2one(
            'account.account',
            'Expense Head Account',
            domain="[('type', '=', 'view')]",
            help=("This account is the head account of a group of expense"
                  " accounts to be reported in the expense part of VIA Combined"
                  " Balance Sheet and VIA Combined Profit/Loss reports.")),
        # The following field is used because fields.property is company
        # specific so that the value set in a child company by the admin of that
        # child company will be different from the value set in the child
        # company by the admin of the parent company. That is, each admin must
        # set the value for property_reserve_and_surplus_account for all
        # companies that the admin can see. This is painful.
        'reserve_and_surplus_account': (float(release.major_version) >= 7.0
                                        and fields.many2one('account.account',
                                                            string='Reserve and Profit/Loss Account',
                                                            domain="[('type', '!=','view')]",
                                                            help=("This account is the account used to report the profit/loss"
                                                                  " amount of this company in VIA Combined Balance Sheet"
                                                                  " report."))
                                        or fields.related('property_reserve_and_surplus_account',
                                                          type='many2one',
                                                          relation='account.account',
                                                          string='Reserve and Profit/Loss Account',
                                                          store=True,
                                                          readonly=True,
                                                          domain="[('type', '!=','view')]",
                                                          help=("This account is the account used to report the profit/loss"
                                                                " amount of this company in VIA Combined Balance Sheet"
                                                                " report."))),
        'exchange_gain_loss_account': fields.many2one(
            'account.account',
            'Currency Exchange Gain/Loss Account',
            help=("This account is the account used to report the currency"
                  " exchange gain/loss amount of this company in VIA Combined"
                  " Balance Sheet report.")),
        'consolidation_exchange_rate_bs': fields.many2one(
            'res.currency',
            'B/S Consolidation Target Currency',
            help=("This currency is used to convert the value of an account"
                  " in multi-company multi-currency setting for non-income"
                  " and non-expense accounts.")),
        'consolidation_exchange_rate_pl': fields.many2one(
            'res.currency',
            'P&L Consolidation Target Currency',
            help=("This currency is used to convert the value of an account"
                  " in multi-company multi-currency setting for income and"
                  " expense accounts.")),
        'consolidation_exchange_rate': fields.many2one(
            'res.currency',
            'Consolidation Target Currency',
            help=("This currency is used to convert the value of an account"
                  " in multi-company multi-currency setting.")),
    }

    def _check_proper_head_accounts(self, cr, uid, ids, context=None):
        # Get company root accounts
        pool = pooler.get_pool(cr.dbname)
        root_account_ids = account_tree.get_root_account_ids(pool, cr, uid, ids,
                                                             context)

        coms = self.browse(cr, uid, ids, context)
        acc_pool = pool.get('account.account')
        # Check for same company head accounts
        res = {}
        for com in coms:
            msg = res.setdefault(com.name, [])
            if (com.asset_head_account
                and com.asset_head_account.company_id.id != com.id):
                msg.append('asset')
            if (com.liability_head_account
                and com.liability_head_account.company_id.id != com.id):
                msg.append('liability')
            if (com.income_head_account
                and com.income_head_account.company_id.id != com.id):
                msg.append('income')
            if (com.expense_head_account
                and com.expense_head_account.company_id.id != com.id):
                msg.append('expense')
            if len(msg) != 0 and root_account_ids[com.id] is None:
                raise osv.except_osv(_('Error !'),
                                     _("Companies '%s' do not have root account")
                                     % com.name)

        improper_coms = filter(lambda (k, v): len(v) != 0, res.iteritems())
        if len(improper_coms) != 0:
            msgs = []
            for (k, v) in improper_coms:
                msgs.append(_("company '%s' has its '%s' head account(s) belonging"
                              " to different companies") % (k, "', '".join(v)))
            raise osv.except_osv(_('Error !'), ", ".join(msgs))

        # Check for nested head accounts
        res = {}

        def __check_proper_head_accounts(root_account, head_account_ids,
                                         head_account_id=None):
            """Check the complete tree using depth-first search."""
            if root_account.id in head_account_ids:
                if head_account_id is None:
                    head_account_id = root_account.id
                else:
                    # root_account is a nested head account
                    return (root_account.id, head_account_id)
            for acc in root_account.child_id:
                res = __check_proper_head_accounts(acc,
                                                   head_account_ids,
                                                   head_account_id)
                if res is not None:
                    return res
            return None
        for com in coms:
            head_account_ids = [com.asset_head_account.id,
                                com.liability_head_account.id,
                                com.income_head_account.id,
                                com.expense_head_account.id, ]
            root_acc_id = root_account_ids[com.id]
            if root_acc_id is None:
                res[com.name] = None
                continue
            root_account = acc_pool.browse(cr, uid, root_acc_id,
                                           context=context)
            res[com.name] = __check_proper_head_accounts(root_account,
                                                         head_account_ids)
        improper_coms = filter(lambda (k, v): v is not None, res.iteritems())
        if len(improper_coms) != 0:
            msgs = []

            def get_acc_head_type(acc_id):
                if (com.asset_head_account
                    and acc_id == com.asset_head_account.id):
                    return 'asset'
                elif (com.liability_head_account
                      and acc_id == com.liability_head_account.id):
                    return 'liability'
                elif (com.income_head_account
                      and acc_id == com.income_head_account.id):
                    return 'income'
                elif (com.expense_head_account
                      and acc_id == com.expense_head_account.id):
                    return 'expense'
            for (k, (child_acc_id, head_acc_id)) in improper_coms:
                msgs.append(_("company '%s' has its %s head account nested under"
                              " its %s head account")
                            % (k,
                               get_acc_head_type(child_acc_id),
                               get_acc_head_type(head_acc_id)))
            raise osv.except_osv(_('Error !'), ", ".join(msgs))

    def write(self, cr, uid, ids, vals, context=None):
        res = super(res_company, self).write(cr, uid, ids, vals, context=context)
        self._check_proper_head_accounts(cr, uid, ids, context=context)
        return res

    def create(self, cr, uid, vals, context=None):
        res = super(res_company, self).create(cr, uid, vals, context=context)
        self._check_proper_head_accounts(cr, uid, [res], context=context)
        return res

res_company()
