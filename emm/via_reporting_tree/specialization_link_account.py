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

'''This specialization link expects NestedDict value to be an instance of
class AccountTreeNodeValue.
'''

try:
    import release
    from osv import osv, fields
    from tools.translate import _
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import osv, fields
    from openerp.tools.translate import _

from via_reporting_tree import tree_node

_node_tags_registry = {}

def register_node_tags(tree_type_name, node_tags_selection):
    if tree_type_name in _node_tags_registry:
        raise Exception('Tree type name "%s" already registered its node tags'
                        % tree_type_name)
    _node_tags_registry.update({tree_type_name: node_tags_selection})

class reporting_tree_node(osv.osv):
    _inherit = 'via.reporting.tree.node'

    def _get_available_node_tags(self, cr, uid, context=None):
        if context is None:
            context = {}
        tree_type_name = context.get('via_reporting_tree.tree_type_name', False)
        if not tree_type_name:
            return [(k, '')
                    for (k, v) in reduce(lambda x, y: x + y,
                                         _node_tags_registry.itervalues(),
                                         [])]
        return _node_tags_registry.get(tree_type_name, [])

    def _node_tag_na(self, cr, uid, ids, name, args, context=None):
        return dict([(o.id,
                      len(_node_tags_registry.get(o.tree_id.tree_type_id.name,
                                                  [])) == 0)
                     for o in self.browse(cr, uid, (isinstance(ids, (int, long))
                                                    and [ids]
                                                    or ids), context=context)])

    _columns = {
        'node_tag': fields.selection(_get_available_node_tags, 'Node Tag'),
        'node_tag_not_applicable': fields.function(_node_tag_na, string='Node Tag N/A',
                                                   type='boolean', method=True),
    }

    _defaults = {
        'node_tag_not_applicable': lambda self, cr, uid, ctx: len(self._get_available_node_tags(cr, uid, context=ctx)) == 0,
    }
reporting_tree_node()

_tags_registry = {}

def register_tags(tree_type_name, tags_selection):
    if tree_type_name in _tags_registry:
        raise Exception('Tree type name "%s" already registered its tags'
                        % tree_type_name)
    _tags_registry.update({tree_type_name: tags_selection})

class account_tree_node(osv.osv):
    _name = 'via.account.tree.node'
    _description = 'VIA Account Tree Node'
    __doc__ = ('A VIA Account Tree Node object links in one account to one VIA'
               ' Reporting Tree Node object.')
    def my_name(self, cr, uid, ids, field_names, arg=None, context=None):
        res = dict.fromkeys(ids, '')
        for n in self.browse(cr, uid, ids, context=context):
            res[n.id] = ('%s @ %.2f%%'
                         % (n.account_id.name_get(context=context)[0][1],
                            n.multiplier * 100.0))
        return res

    def _get_available_tags(self, cr, uid, context=None):
        if context is None:
            context = {}
        tree_type_name = context.get('via_reporting_tree.tree_type_name', False)
        if not tree_type_name:
            return [(k, '')
                    for (k, v) in reduce(lambda x, y: x + y,
                                         _tags_registry.itervalues(),
                                         [])]
        return _tags_registry.get(tree_type_name, [])

    def _tag_na(self, cr, uid, ids, name, args, context=None):
        return dict([(o.id,
                      len(_tags_registry.get(o.node_id.tree_id.tree_type_id.name,
                                             [])) == 0)
                     for o in self.browse(cr, uid, (isinstance(ids, (int, long))
                                                    and [ids]
                                                    or ids), context=context)])

    _columns = {
        'name': fields.function(my_name, type='char', size=128, string="Name",
                                method=True),
        'company_id': fields.related('node_id', 'tree_id', 'company_id',
                                     type='many2one',
                                     relation='res.company', string='Company',
                                     store=True, readonly=True),
        'node_id': fields.many2one('via.reporting.tree.node',
                                   'Reporting Tree Node', required=True),
        'account_id': fields.many2one('account.account', 'Account',
                                      required=True,
                                      domain="[('company_id','child_of',company_id)]"),
        'multiplier': fields.float('Multiplier (%)', required=True,
                                   digits=(14,4)),
        'tag': fields.selection(_get_available_tags, 'Tag'),
        'tag_not_applicable': fields.function(_tag_na, string='Tag N/A',
                                              type='boolean', method=True),
    }

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]

        account_ids = []
        for r in self.read(cr, uid, ids, ['account_id'], context,
                           load='_classic_write'):
            account_ids.append(r['account_id'])

        pool = self.pool.get('account.account')
        return pool.name_get(cr, uid, account_ids, context=context)

    _defaults = {
        'multiplier': 1.0,
        'tag_not_applicable': lambda self, cr, uid, ctx: len(self._get_available_tags(cr, uid, context=ctx)) == 0,
        'company_id': lambda self, cr, uid, ctx: ctx.get('via_reporting_tree.tree_node_company_id', False),
    }
    _sql_constraints = [
        ('multiplier_is_percentage', 'check (multiplier BETWEEN 0.0 AND 1.0)',
         'A multiplier must be between 0.0 and 1.0, inclusive !'),
    ]
    def copy(self, cr, uid, src_id, default=None, context=None):
        raise NotImplementedError(_('The copy method is not implemented on this'
                                    ' object !'))
    def copy_data(self, cr, uid, src_id, default=None, context=None):
        raise NotImplementedError(_('The copy_data method is not implemented on'
                                    ' this object !'))
account_tree_node()

class AccountTreeNodeValue(object):
    def __init__(self, currency_normalizer, currency_rounder,
                 currency_is_zero, currency_id=None,
                 bd=0.0, bc=0.0, dr=0.0, cr=0.0, node=None, linearize_me=False):
        self.normalizer = currency_normalizer
        self.rounder = currency_rounder
        self.is_zero = currency_is_zero
        self.currency_id = currency_id
        self.node = node
        self.linearize_me = linearize_me
        self.set(currency_id, bd, bc, dr, cr)

    def _adapt(self, currency_id, value):
        normalizer = self.normalizer
        if self.currency_id == currency_id:
            normalizer = lambda _, amount: amount
        return self.rounder(normalizer(currency_id, value))

    def _update(self):
        self.mv = self.rounder(self.dr - self.cr)
        self.bb = self.rounder(self.bd - self.bc)
        self.eb = self.rounder(self.bb + self.mv)

    def set(self, currency_id, bd, bc, dr, cr):
        self.bd = self._adapt(currency_id, bd)
        self.bc = self._adapt(currency_id, bc)
        self.dr = self._adapt(currency_id, dr)
        self.cr = self._adapt(currency_id, cr)
        self._update()

    def add(self, currency_id, bd, bc, dr, cr):
        self.bd = self.rounder(self.bd + self._adapt(currency_id, bd))
        self.bc = self.rounder(self.bc + self._adapt(currency_id, bc))
        self.dr = self.rounder(self.dr + self._adapt(currency_id, dr))
        self.cr = self.rounder(self.cr + self._adapt(currency_id, cr))
        self._update()

def account_sum(parent_datum, child_datum):
    parent_datum.add(child_datum.currency_id, child_datum.bd, child_datum.bc,
                     child_datum.dr, child_datum.cr)
    parent_datum.linearize_me = child_datum.linearize_me
    return parent_datum

tree_node.register_specialization(tree_node_type='account',
                                  link_type='one2many',
                                  calculators={
                                      'sum': account_sum,
                                  },
                                  default_calculation='sum')
