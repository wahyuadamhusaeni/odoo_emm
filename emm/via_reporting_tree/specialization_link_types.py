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
    from osv import fields
    import pooler
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import fields
    from openerp import pooler

from lxml import etree

class one2many(object):
    def __init__(self, tree_node_type):
        self.tree_node_type = tree_node_type
        self.one2many_name = tree_node_type + '_tree_node_ids'
        self.model = 'via.' + tree_node_type + '.tree.node'
        self.field_name = tree_node_type.capitalize() + ' Tree Nodes'

    def get_field_defs(self):
        return {
            self.one2many_name: {
                'type': 'one2many',
                'relation': self.model,
                'string': self.field_name,
                'domain': "[('company_id','child_of',company_id)]",
                'context': {
                    'via_reporting_tree.tree_node_specialization_name':
                        self.tree_node_type,
                },
            }
        }

    def get_columns(self):
        return {
            self.one2many_name: fields.one2many(self.model,
                                                'node_id',
                                                self.field_name, context={
                'via_reporting_tree.tree_node_specialization_name':
                    self.tree_node_type,
            })
        }

    def reader(self, cr, uid, ids, fields, context):
        pool = pooler.get_pool(cr.dbname).get(self.model)
        res = {}
        for i in ids:
            read_ids = pool.search(cr, uid, [('node_id','in',ids)],
                                   context=context)
            res[i] = {self.one2many_name: read_ids}
        return res

    def writer(self, cr, uid, ids, vals, context):
        directives = vals[self.one2many_name]
        pool = pooler.get_pool(cr.dbname).get(self.model)
        if directives is False:
            criteria = [('node_id','in',(isinstance(ids, (int, long))
                                         and [ids]
                                         or ids))]
            existing_ids = pool.search(cr, uid, criteria, context=context)
            if len(existing_ids):
                pool.unlink(cr, uid, existing_ids, context=context)
            return
        for directive in directives:
            cmd = directive[0]
            if cmd == 0:
                for i in ids:
                    vs = {'node_id': i}
                    vs.update(directive[2])
                    pool.create(cr, uid, vs, context=context)
            elif cmd == 1:
                pool.write(cr, uid, directive[1], directive[2], context=context)
            elif cmd == 2:
                pool.unlink(cr, uid, directive[1], context=context)
            elif cmd == 3:
                pool.write(cr, uid, directive[1], {'node_id': False},
                           context=context)
            elif cmd == 4:
                pool.write(cr, uid, directive[1], {'node_id': ids[0]},
                           context=context)
            elif cmd == 5:
                affected_ids = pool.search(cr, uid,
                                           [('node_id','in',ids)],
                                           context=context)
                pool.write(cr, uid, affected_ids, {'node_id': False},
                           context=context)
