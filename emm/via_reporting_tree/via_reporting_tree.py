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
    from osv import osv, fields, orm
    from tools.translate import _
    from lxml import etree
    from ast import literal_eval
    from specialization_link_types import one2many as one2many_link
    from via_reporting_utility.pgsql import create_composite_type
    from via_reporting_utility.pgsql import create_plpgsql_proc
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import osv, fields, orm
    from openerp.tools.translate import _
    from specialization_link_types import one2many as one2many_link
    from openerp.addons.via_reporting_utility.pgsql import create_composite_type
    from openerp.addons.via_reporting_utility.pgsql import create_plpgsql_proc

from via_reporting_tree_sql import via_tree_node_level_tagger_def
from via_reporting_tree_sql import via_tree_node_parent_left_right_tagger_def
from via_reporting_tree_sql import via_tree_node_unroller_def
from via_reporting_tree_sql import via_tree_node_count_children_def
from lxml import etree
from ast import literal_eval

class tree_type(osv.osv):
    _name = 'via.reporting.tree.type'
    _description = 'VIA Reporting Tree Type'
    __doc__ = ('A VIA Reporting Tree Type is used to define special nodes that'
               ' every tree having this particular type must have')

    _columns = {
        'name': fields.char('Name', required=True, size=128, select=True,
                            readonly=True),
        'tree_node_type': fields.char('Tree Node Type', required=True, size=64,
                                      select=True, readonly=True),
    }

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         'The name of a tree type must be unique !')
    ]

    def copy(self, cr, uid, src_id, default=None, context=None):
        raise NotImplementedError(_('The copy method is not implemented on this'
                                    ' object !'))

    def copy_data(self, cr, uid, src_id, default=None, context=None):
        raise NotImplementedError(_('The copy_data method is not implemented on'
                                    ' this object !'))
tree_type()

class tree(osv.osv):
    _name = 'via.reporting.tree'
    _description = 'VIA Reporting Tree'
    __doc__ = ('A VIA Reporting Tree object is used to report data in a certain'
               ' tree structure defined by this object.')

    def _get_root_node(self, cr, uid, ids, field_names, arg=None, context=None):
        if type(ids) != list:
            ids = [ids]
        res = dict.fromkeys(ids, False)
        pool = self.pool.get('via.reporting.tree.node')
        node_ids = pool.search(cr, uid, [('tree_id','in',ids),
                                        ('parent_id','=',False)],
                              context=context)
        nodes = pool.browse(cr, uid, node_ids, context=context)
        for node in nodes:
            res[node.tree_id.id] = node.id
        return res

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True,
                                      select=True),
        'name': fields.char('Name', size=128, required=True, select=True),
        'tree_type_id': fields.many2one('via.reporting.tree.type', 'Tree Type',
                                        required=True, select=True),
        'tree_type_name': fields.related('tree_type_id', 'name',
                                         type='text', string='Tree Type Name',
                                         readonly=True),
        'node_ids': fields.one2many('via.reporting.tree.node', 'tree_id',
                                    'Tree Nodes'),
        'tree_node_type': fields.related('tree_type_id', 'tree_node_type',
                                         type='char', size=64, readonly=True,
                                         string='Tree Node Type'),
        'root_node_id': fields.function(_get_root_node, method=True,
                                        type='many2one', string='Root Node',
                                        relation='via.reporting.tree.node'),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, uid, context=ctx).company_id.id
    }

    _sql_constraints = [
        ('name_type_uniq', 'unique (name, tree_type_id)',
         'The name of a tree must be unique per tree type !')
    ]

    @staticmethod
    def traverse(node,
                 upon_entering_fn=(lambda node, context: None),
                 before_each_child_fn=(lambda child, context: None),
                 after_each_child_fn=(lambda child, context: None),
                 before_leaving_fn=(lambda node, context: None),
                 context=None):

        def _traverse(node, upon_entering_fn, before_each_child_fn,
                      after_each_child_fn, before_leaving_fn, context):
            context = context.copy()

            upon_entering_fn(node, context)
            for child in node.children:
                before_each_child_fn(child, context)
                _traverse(child, upon_entering_fn, before_each_child_fn,
                          after_each_child_fn, before_leaving_fn, context)
                after_each_child_fn(child, context)
            before_leaving_fn(node, context)

        if context is None:
            context = {}

        upon_entering_fn(node, context)
        for child in node.children:
            before_each_child_fn(child, context)
            _traverse(child, upon_entering_fn, before_each_child_fn,
                      after_each_child_fn, before_leaving_fn, context)
            after_each_child_fn(child, context)
        before_leaving_fn(node, context)
    def copy(self, cr, uid, src_id, default=None, context=None):
        raise NotImplementedError(_('The copy method is not implemented on this'
                                    ' object !'))

    def copy_data(self, cr, uid, src_id, default=None, context=None):
        raise NotImplementedError(_('The copy_data method is not implemented on'
                                    ' this object !'))
    @staticmethod
    def propagate_up(node, attach_datum, propagate_datum, combine_data):
        dummy_nodes = []

        def upon_entering_fn(node, context):
            attach_datum(node)
            if node.dummy_node:
                dummy_nodes.append(node)

        def after_each_child_fn(child, context):
            if not child.dummy_node and not child.parent_id.dummy_node:
                propagate_datum(child.parent_id, child)

        tree.traverse(node,
                      upon_entering_fn=upon_entering_fn,
                      after_each_child_fn=after_each_child_fn)

        for dummy_node in dummy_nodes:
            combine_data(dummy_node, dummy_node.associated_node_ids)

    @staticmethod
    def linearize(node, linearize_node):
        res = []
        def upon_entering_fn(node, context):
            res.extend(linearize_node(node))
        tree.traverse(node,
                      upon_entering_fn=upon_entering_fn)
        return res

    @staticmethod
    def calculate(node, datasource):
        tree_node_type = node.tree_node_type
        registry_entry = node._specialization_registry[tree_node_type]
        available_calculators = registry_entry.calculators

        def attach_datum(node):
            node_data = datasource.get_view(node.id)
            def node_initializer(keys):
                v = node_data.get_value(*keys)
                v.node = node
            node_data.traverse(node_initializer)
        def propagate_datum(parent_node, child_node):
            parent_datum = datasource.get_view(parent_node.id)
            child_datum = datasource.get_view(child_node.id)
            calculator = available_calculators[parent_node.calculation]
            parent_datum.update(child_datum, calculator)
        def combine_data(target_node, source_nodes):
            target_datum = datasource.get_view(target_node.id)
            calculator = available_calculators[target_node.calculation]
            for source_node in source_nodes:
                source_datum = datasource.get_view(source_node.id)
                target_datum.update(source_datum, calculator)

        tree.propagate_up(node,
                          attach_datum,
                          propagate_datum,
                          combine_data)

    def action_via_reporting_tree_node_chart(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'via_reporting_tree', 'action_via_reporting_tree_node_chart')
        _id = result and result[1] or False

        result = act_obj.read(cr, uid, [_id], context=context)[0]
        result['domain'] = str([('parent_id','=',False),('tree_id','=',ids[0])])

        return result
tree()

class tree_node(osv.osv):
    _name = 'via.reporting.tree.node'
    _description = 'VIA Reporting Tree Node'
    __doc__ = ('A VIA Reporting Tree Node object is used to construct a tree of'
               ' objects of this class, each of which is associated with zero'
               ' or more objects of the same model.')
    _order = 'sequence'
    _parent_order = _order
    _parent_store = True
    def _auto_init(self, cr, context=None):
        super(tree_node, self)._auto_init(cr, context=context)
        create_composite_type(cr, 'via_tree_node',
                              [('id', 'BIGINT'),
                               ('parent_id', 'BIGINT')])
        create_composite_type(cr, 'via_tree_node_unrolled',
                              [('id', 'BIGINT'),
                               ('parent_id', 'BIGINT'),
                               ('level', 'BIGINT'),
                               ('parent_left', 'BIGINT'),
                               ('parent_right', 'BIGINT')])
        create_composite_type(cr, 'via_tree_node_level_tagger_datum',
                              [('id', 'BIGINT'),
                               ('parent_id', 'BIGINT'),
                               ('level', 'BIGINT'),
                               ('unrolling_pid', 'BIGINT'),
                               ('unique_id', 'BIGINT'),
                               ('unique_parent_id', 'BIGINT')])
        create_composite_type(cr, 'via_tree_node_child_count',
                              [('id', 'BIGINT'),
                               ('parent_id', 'BIGINT'),
                               ('level', 'BIGINT'),
                               ('unique_id', 'BIGINT'),
                               ('unique_parent_id', 'BIGINT'),
                               ('child_count', 'BIGINT')])
        create_plpgsql_proc(cr, 'via_tree_node_unroller',
                            [('IN', 'tree_nodes', 'VIA_TREE_NODE[]')],
                            'SETOF VIA_TREE_NODE_LEVEL_TAGGER_DATUM',
                            via_tree_node_unroller_def)
        create_plpgsql_proc(cr, 'via_tree_node_count_children',
                            [('IN', 'unrolled_tree_nodes', 'VIA_TREE_NODE_LEVEL_TAGGER_DATUM[]')],
                            'SETOF VIA_TREE_NODE_CHILD_COUNT',
                            via_tree_node_count_children_def)
        create_plpgsql_proc(cr, 'via_tree_node_parent_left_right_tagger',
                            [('IN', 'unrolled_tree_nodes', 'VIA_TREE_NODE_CHILD_COUNT[]')],
                            'SETOF VIA_TREE_NODE_UNROLLED',
                            via_tree_node_parent_left_right_tagger_def)
        create_plpgsql_proc(cr, 'via_tree_node_level_tagger',
                            [('IN', 'tree_nodes', 'VIA_TREE_NODE[]')],
                            'SETOF VIA_TREE_NODE_UNROLLED',
                            via_tree_node_level_tagger_def)
    def copy(self, cr, uid, src_id, default=None, context=None):
        raise NotImplementedError(_('The copy method is not implemented on this'
                                    ' object !'))

    def copy_data(self, cr, uid, src_id, default=None, context=None):
        raise NotImplementedError(_('The copy_data method is not implemented on'
                                    ' this object !'))

    def _get_level(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        nodes = self.browse(cr, uid, ids, context=context)
        for node in nodes:
            level = 0
            if node.parent_id:
                obj = self.browse(cr, uid, node.parent_id.id)
                level = obj.level + 1
            res[node.id] = level
        return res

    def _get_available_calculation(self, cr, uid, context=None):
        if context is None:
            context = {}

        tree_node_types = []
        tree_node_type = context.get('via_reporting_tree.tree_node_specialization_name',
                                     False)
        if tree_node_type is False:
            tree_id = context.get('via_reporting_tree.tree_id', False)
            if tree_id is not False:
                tree_pool = self.pool.get('via.reporting.tree')
                tree = tree_pool.browse(cr, uid, tree_id, context)
                tree_node_types = [tree.tree_type_id.tree_node_type]
            else:
                # This happens when importing CSV data through the web client
                tree_node_types = list(self._specialization_registry.iterkeys())
        else:
            tree_node_types = [tree_node_type]

        available_calcs = set()
        for type_ in tree_node_types:
            calcs = self._specialization_registry[type_].calculators
            for k in calcs.iterkeys():
                available_calcs.add(k)

        return [(calc, calc.capitalize()) for calc in available_calcs]

    _columns = {
        'company_id': fields.related('tree_id', 'company_id', type='many2one',
                                     relation='res.company', string='Company',
                                     store=True, readonly=True),
        'tree_id': fields.many2one('via.reporting.tree', 'Tree', required=True),
        'tree_type_name': fields.related('tree_id', 'tree_type_id', 'name',
                                         type='text', string='Tree Type Name',
                                         readonly=True),
        'tree_node_type': fields.related('tree_id', 'tree_type_id',
                                         'tree_node_type',
                                         type='char', string='Tree Node Type',
                                         readonly=True, size=64),
        'sequence': fields.integer('Sequence', required=True),
        'name': fields.char('Name', size=128, required=True, select=True),
        'parent_id': fields.many2one('via.reporting.tree.node', 'Parent',
                                     ondelete='cascade',
                                     domain="[('tree_id','=',tree_id)]"),
        'parent_left': fields.integer('Parent Left', select=1),
        'parent_right': fields.integer('Parent Right', select=1),
        'level': fields.function(_get_level, string='Level', method=True,
                                 store=True, type='integer'),
        'children': fields.one2many('via.reporting.tree.node', 'parent_id',
                                    'Children'),
        'calculation': fields.selection(_get_available_calculation,
                                        'Method',
                                        required=True),
        'dummy_node': fields.boolean('Dummy Node'),
        'associated_node_ids': fields.many2many('via.reporting.tree.node',
                                                'via_reporting_tree_node_rel',
                                                'node_id', 'associate_id',
                                                'Associated Nodes'),
        # Formatting attributes
        'bold': fields.boolean('Bold'),
        'italic': fields.boolean('Italic'),
        'underline': fields.boolean('Underline'),
        'blank_line': fields.boolean('Blank Line'),
        'title_line': fields.boolean('Title Line'),
    }

    def get_rtype(self, cr, uid, ids, context=None):
        def _get_rtype(bold=False, italic=False, underline=False,
                       blank_line=False, title_line=False):
            return '%s-%s-%s-%s-%s' % (str(bold).lower(), str(italic).lower(),
                                       str(underline).lower(),
                                       str(blank_line).lower(),
                                       str(title_line).lower())
        if isinstance(ids, (int, long)) or len(ids) == 1:
            if type(ids) == list:
                ids = ids[0]
            o = self.browse(cr, uid, ids, context=context)
            return _get_rtype(o.bold, o.italic, o.underline, o.blank_line,
                              o.title_line)

        res = dict.fromkeys(ids, _get_rtype())
        for o in self.browse(cr, uid, ids, context=context):
            res[o.id] = _get_rtype(o.bold, o.italic, o.underline, o.blank_line,
                                   o.title_line)
        return res

    def default_get_tree_id(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('via_reporting_tree.tree_id', None)

    def default_get_tree_type_name(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('via_reporting_tree.tree_type_name', None)

    def default_get_tree_node_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('via_reporting_tree.tree_node_specialization_name', None)

    def default_get_calculation(self, cr, uid, context=None):
        if context is None:
            context = {}
        tree_node_type = context.get('via_reporting_tree.tree_node_specialization_name',
                                     False)
        if tree_node_type is False:
            tree_id = context.get('via_reporting_tree.tree_id', False)
            if tree_id is not False:
                t = self.pool.get('via.reporting.tree').browse(cr, uid, tree_id,
                                                               context=context)
                tree_node_type = t.tree_node_type

        if tree_node_type is False:
            return 'none'

        return tree_node._specialization_registry[tree_node_type].default_calculation

    _defaults = {
        'tree_id': default_get_tree_id,
        'tree_type_name': default_get_tree_type_name,
        'tree_node_type': default_get_tree_node_type,
        'calculation': default_get_calculation,
        'dummy_node': False,
        'bold': False,
        'italic': False,
        'underline': False,
        'blank_line': False,
        'title_line': False,
    }

    def _check_single_root_node(self, cr, uid, ids, context=None):
        nodes = self.browse(cr, uid, ids, context=context)
        for node in nodes:
            if node.parent_id and node.parent_id.id:
                continue
            root_node_ids = self.search(cr, uid,
                                        [('tree_id','=',node.tree_id.id),
                                         ('parent_id','=',False)],
                                        context=context)
            if len(root_node_ids) > 1:
                return False
        return True

    def _non_dummy_no_associated_nodes(self, cr, uid, ids, context=None):
        nodes = self.browse(cr, uid, ids, context=context)
        for node in nodes:
            if not node.dummy_node and len(node.associated_node_ids) != 0:
                return False
        return True

    def _calculation_none_no_associated_node(self, cr, uid, ids, context=None):
        nodes = self.browse(cr, uid, ids, context=context)
        for node in nodes:
            if node.calculation == 'none' and len(node.associated_node_ids) != 0:
                return False
        return True

    def _calculation_sum_dummy_has_associated_node(self, cr, uid, ids, context=None):
        nodes = self.browse(cr, uid, ids, context=context)
        for node in nodes:
            if node.calculation == 'sum' and node.dummy_node and len(node.associated_node_ids) == 0:
                return False
        return True

    _constraints = [
        (_check_single_root_node, 'You cannot have more than one root node !',
         ['parent_id']),
        (_non_dummy_no_associated_nodes,
         'A non-dummy node cannot have an associated node !',
         ['associated_node_ids', 'dummy_node']),
        (_calculation_none_no_associated_node,
         'Calculation NONE must have no associated node !',
         ['associated_node_ids', 'calculation']),
        (_calculation_sum_dummy_has_associated_node,
         'Calculation SUM on a dummy node must have at least one associated node !',
         ['associated_node_ids', 'calculation', 'dummy_node']),
    ]

    _sql_constraints = [
        ('sequence_tree_uniq', 'unique (sequence, tree_id)',
         'The sequence of a tree node must be unique per tree !'),
    ]

    _specialization_registry = {}

    @classmethod
    def register_specialization(cls, tree_node_type, link_type, calculators,
                                default_calculation='none'):
        if tree_node_type in cls._specialization_registry:
            raise osv.except_osv(_('Error !'),
                                 _('Tree node specialization "%s" already'
                                   ' exists !') % tree_node_type)

        link = None
        if link_type == 'one2many':
            link = one2many_link(tree_node_type)
        else:
            raise osv.except_osv(_('Error !'),
                                 _('Unrecognized node specialization link type'
                                   ' "%s" !') % link_type)

        class registry_entry(object):
            def __init__(self, tree_node_type, link, calculators,
                         default_calculation):
                self.tree_node_type = tree_node_type
                self.link = link
                self.calculators = calculators
                self.calculators.update({'none': (lambda parent_datum,
                                                  child_datum: None)})
                self.default_calculation = default_calculation
                if self.default_calculation not in self.calculators:
                    raise osv.except_osv(_('Error !'),
                                         _('Default calculation is not in calculators'))

        entry = registry_entry(tree_node_type, link, calculators,
                               default_calculation)
        cls._specialization_registry[tree_node_type] = entry

        cls._columns.update(link.get_columns())

    def fields_get(self, cr, uid, fields=None, context=None):
        if context is None:
            context = {}
        res = super(tree_node, self).fields_get(cr, uid, fields, context)

        name = context.get('via_reporting_tree.tree_node_specialization_name',
                           False)
        if name is False:
            return res

        field_defs = self._specialization_registry[name].link.get_field_defs()
        needed_fields = []
        if (fields
            and not context.get('via_reporting_tree.tree_node_fields_view_get',
                                False)):
            for f in field_defs.iterkeys():
                if f in fields:
                    needed_fields.append(f)
        else:
            needed_fields = list(field_defs.iterkeys())

        for f in needed_fields:
            res[f] = field_defs[f]

        return res

    def read(self, cr, uid, ids, fields=None, context=None,
             load='_classic_read'):
        if type(ids) != list:
            ids = [ids]
        res = super(tree_node, self).read(cr, uid, ids, fields, context, load)

        if fields is None:
            fields = []
        if not fields or not res:
            return res

        unread_fields = set(fields)
        for k in res[0].iterkeys():
            try:
                unread_fields.remove(k)
            except KeyError:
                pass # Some extra keys are included (e.g., id)
        if len(unread_fields) == 0:
            return res
        else:
            unread_fields = list(unread_fields)

        if context is None:
            context = {}

        names = {}
        for node in self.browse(cr, uid, ids, context=context):
            l = names.setdefault(node.tree_id.tree_node_type, [])
            l.append(node.id)

        for (name, _ids) in names.iteritems():
            reader = self._specialization_registry[name].link.reader
            update_data = reader(cr, uid, _ids, unread_fields, context)
            for record in res:
                tree_node_id = record['id']
                record.update(update_data[tree_node_id])

        return res

    def write(self, cr, uid, ids, vals, context=None):
        if type(ids) != list:
            ids = [ids]

        if context is None:
            context = {}

        names = {}
        for node in self.browse(cr, uid, ids, context=context):
            l = names.setdefault(node.tree_id.tree_node_type, [])
            l.append(node.id)
            if vals.get('tree_id', node.tree_id.id) != node.tree_id.id:
                raise osv.except_osv(_('Error !'),
                                     _('Cannot change tree !'))

        specific_name_vals = {}
        for name in names:
            field_defs = self._specialization_registry[name].link.get_field_defs()
            for f in field_defs.iterkeys():
                if f not in vals:
                    continue
                d = specific_name_vals.setdefault(name, {})
                d[f] = vals[f]
                del vals[f]

        if vals:
            super(tree_node, self).write(cr, uid, ids, vals, context)

        for (name, specific_vals) in specific_name_vals.iteritems():
            writer = self._specialization_registry[name].link.writer
            writer(cr, uid, ids, specific_vals, context)

        return True

tree_node()
