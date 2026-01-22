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

from openerp.osv import orm, fields
from tools.translate import _


class account_journal(orm.Model):
    _inherit = "account.journal"

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if context is None:
            context = {}

        if args is None:
            args = []

        _dom = context.pop('domain', [])
        _dom = _dom and eval(_dom) or []
        _new_dom = []

        for _leaf in _dom:
            if isinstance(_leaf, (tuple, )):
                _new_dom.append(list(_leaf))
            else:
                _new_dom.append(_leaf)
        args.extend(_new_dom)
        return super(account_journal, self).name_search(cr, user, name=name, args=args, operator=operator, context=context, limit=limit)


class company_journal(orm.Model):
    _name = "company.journal"
    _rec_name = "domain_id"

    def _get_domain(self, cr, uid, ids, name, args, context=None):
        res = {}
        for _obj in self.browse(cr, uid, ids, context=context):
            res[_obj.id] = _obj.domain_id and _obj.domain_id.domain or ""
        return res

    _columns = {
        'company_id': fields.many2one('res.company', 'Company'),
        'domain_id': fields.many2one('default.domain', 'Journal For'),
        'filter_domain': fields.function(_get_domain, type="text", string='Domain'),
        'journal_id': fields.many2one('account.journal', 'Journal'),
    }

    _sql_constraints = [
        ('domain_uniq', 'unique(domain_id, company_id)', _('Default Journals in Configuration Tab cannot have more than one setting for the same Journal For per Company!')),
    ]

    def get_domain_journal(self, cr, uid, ids, domain_id, context=None):
        domain = domain_id and self.pool.get('default.domain').browse(cr, uid, domain_id, context=context) or False
        domain_journal = domain and domain.domain or []

        return {
            'value': {'filter_domain': domain_journal, 'journal_id': False},
            'domain': {'journal_id': domain_journal},
        }


class res_company(orm.Model):
    _inherit = "res.company"

    _columns = {
        'default_journal': fields.one2many('company.journal', 'company_id', 'Default Journals'),
    }

    def get_journal_for(self, cr, uid, ids, codename, context=None):
        res = False

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_id = user.company_id.id

        if not ids or ids != company_id:
            ids = [company_id]

        for company in self.browse(cr, uid, ids, context=context):
            for item in company.default_journal:
                if item.domain_id.domain_code == codename:
                    res = item.journal_id and item.journal_id.id or False
                    break
                else:
                    res = False
        return res
