# -*- coding: utf-8 -*-
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

'''This module contains tools to craft pgSQL query code.'''

try:
    import release
    from osv import osv
except ImportError:
    import openerp
    from openerp import release
    from openerp.osv import osv

from re import sub

class via_reporting_pgsql_language(osv.osv):
    _name = 'via.reporting.pgsql.language'
    _auto = False
    _description = 'VIA Reporting Utility PostgreSQL Language'
    def _auto_init(self, cr, context=None):
        super(via_reporting_pgsql_language, self)._auto_init(cr, context=context)
        cr.execute(" SELECT *"
                   " FROM pg_language"
                   " WHERE LANNAME = 'plpgsql'")
        if cr.rowcount == 0:
            cr.execute("CREATE LANGUAGE plpgsql")
via_reporting_pgsql_language()

def create_composite_type(cr, type_name, member_names_types):
    cr.execute(" SELECT *"
               " FROM pg_type"
               " WHERE typname = '%s'" % type_name)
    if cr.rowcount == 1:
        cr.execute("DROP TYPE %s CASCADE" % type_name)
    cr.execute("CREATE TYPE %s AS (%s)"
               % (type_name,
                  ', '.join([' '.join(name_type)
                             for name_type in member_names_types])))

def create_aggregator(cr, proc_name, input_type, member_fields_values):
    cr.execute(" SELECT *"
               " FROM pg_proc"
               " WHERE proname = '%s' AND proisagg IS TRUE" % proc_name)
    if cr.rowcount == 1:
        cr.execute(" SELECT"
                   "  'drop aggregate '"
                   "  || proname || '('"
                   "  || (SELECT COALESCE(ARRAY_TO_STRING(ARRAY_AGG(typname), ', '), '')"
                   "      FROM pg_type"
                   "       INNER JOIN REGEXP_SPLIT_TO_TABLE(proargtypes::TEXT, ' ') prm_oid"
                   "        ON pg_type.oid = NULLIF(prm_oid, '')::OID)"
                   "  || ') cascade' AS drop_function_ddl"
                   " FROM pg_proc"
                   " WHERE proname = '%s' AND proisagg IS TRUE" % proc_name)
        cr.execute(cr.fetchone()[0])
    cr.execute(" CREATE AGGREGATE %s(%s)"
               " (%s)" % (proc_name, input_type,
                          ', '.join((k + ' = ' + v) for k, v in member_fields_values.iteritems())))

def create_plpgsql_proc(cr, proc_name, prm_dirs_names_types, return_type,
                        proc_body, proc_properties='', update_definition_only=False):
    if not update_definition_only:
        cr.execute(" SELECT *"
                   " FROM pg_proc"
                   " WHERE proname = '%s'" % proc_name)
        if cr.rowcount == 1:
            cr.execute(" SELECT"
                       "  'drop function '"
                       "  || proname || '('"
                       "  || (SELECT COALESCE(ARRAY_TO_STRING(ARRAY_AGG(typname), ', '), '')"
                       "      FROM pg_type"
                       "       INNER JOIN REGEXP_SPLIT_TO_TABLE(proargtypes::TEXT, ' ') prm_oid"
                       "        ON pg_type.oid = NULLIF(prm_oid, '')::OID)"
                       "  || ') cascade' AS drop_function_ddl"
                       " FROM pg_proc"
                       " WHERE proname = '%s'" % proc_name)
            cr.execute(cr.fetchone()[0])
    cr.execute('CREATE %s FUNCTION %s(%s) RETURNS %s AS $BODY$ %s $BODY$ LANGUAGE plpgsql %s'
               % (update_definition_only and 'OR REPLACE' or '',
                  proc_name,
                  ', '.join([' '.join(prm_dir_name_type)
                             for prm_dir_name_type in prm_dirs_names_types]),
                  return_type,
                  proc_body,
                  proc_properties))

def create_trigger(cr, name, table, before, row_level, proc,
                   on_insert=False, on_update=False, on_delete=False,
                   update_definition_only=False):
    fn_name = '%s_proc' % name
    create_plpgsql_proc(cr, fn_name, [], 'TRIGGER', proc,
                        update_definition_only=update_definition_only)

    if update_definition_only:
        cr.execute(" SELECT *"
                   " FROM pg_trigger"
                   " WHERE tgname = '%s'" % name)
        if cr.rowcount == 1:
            return

    cr.execute("DROP TRIGGER IF EXISTS %s ON %s CASCADE"
               % (fn_name, table))
    cr.execute("CREATE TRIGGER %s %s %s ON %s FOR EACH %s EXECUTE PROCEDURE %s()"
               % (name,
                  before and 'BEFORE' or 'AFTER',
                  ' OR '.join((on_insert and ['INSERT'] or [])
                              + (on_update and ['UPDATE'] or [])
                              + (on_delete and ['DELETE'] or [])),
                  table,
                  row_level and 'ROW' or 'STATEMENT',
                  fn_name))

def _stringify_element(e):
    if isinstance(e, basestring):
        e = "'" + sub(r"(\\|')", r'\\\1', e) + "'"
    if type(e) == unicode:
        return e.encode('utf-8')
    elif type(e) == float:
        return repr(e)
    else:
        return str(e)

def _stringify_element_list(n):
    return '(' + ', '.join(_stringify_element(e) for e in n) + ')'

def _make_pgArray(stringified_l):
    return ', '.join(stringified_l).replace('None', 'NULL')

def _type_pgArray(untyped_pgArray, pgArray_pattern, types):
    element_count = len(types)
    prefix = ''
    suffix = ', '
    if element_count > 1:
        prefix = '('
        suffix = ')'

    def typer(matchobj):
        res = []
        dict_ = matchobj.groupdict()
        for idx in range(element_count):
            word = dict_['e' + str(idx)]
            if types[idx] == 'INTEGER':
                if word.upper() != 'NULL':
                    # Sometimes Python can give something like '44L' instead
                    # of '44'
                    word = word.replace('L', '')
                res.append(word + '::INTEGER')
            else:
                res.append(word + '::' + types[idx])
        return prefix + ', '.join(res) + suffix
    return unicode(sub(pgArray_pattern, typer, untyped_pgArray), 'utf-8')

_element_patt = ("NULL"
                 "|True"
                 "|False"
                 "|[-0-9.]+"
                 r"|'.*?'")

def list_to_pgArray(l, type_cast):
    '''Given a list of elements, convert it into a pgSQL query code
    that evaluates to an array of elements. The type_cast is needed to
    give type to each element in the array. The value 'INTEGER' should
    be used to type_cast ID values (integral primary keys). For
    example:
        list_to_pgArray(['Hello' + unichr(0x2013) + 'Hello', 'World', None], 'TEXT')
    will result in:
        ARRAY['Hello–Hello'::TEXT, 'World'::TEXT, NULL::TEXT]::TEXT[]
    '''
    untyped_pgArray = _make_pgArray(_stringify_element(n) for n in l) + ', '
    pgArray_pattern = "(?P<e%d>%s), " % (0, _element_patt)
    return ('ARRAY['
            + _type_pgArray(untyped_pgArray, pgArray_pattern, [type_cast])[:-2]
            + (']::%s[]' % type_cast))

def list_to_pgArrayOfRecords(l, type_cast):
    '''Given a list of tuples (or lists), convert it into a pgSQL
    query code that evaluates to an array of records. The type_cast is
    needed to give type to each element in the tuple. The value
    'INTEGER' should be used to type_cast ID values (integral primary
    keys). For example:
        list_to_pgArrayOfRecords([(7L, 'Hello' + unichr(0x2013) + 'Hello'), (8, 'World'), (9, None)], ['INTEGER', 'TEXT'])
    will result in:
        ARRAY[(7::INTEGER, 'Hello–Hello'::TEXT), (8::INTEGER, 'World'::TEXT), (9::INTEGER, NULL::TEXT)]::RECORD[]
    Exception is raised for the following situations:
    1. Length of type_cast is less than 2
    2. Length of each record in l is not uniform
    3. Length of each record in l does not match the length of type_cast
    '''
    if len(type_cast) < 2:
        raise Exception('At least two type cast are needed')
    if len(l):
        reference_record_len = len(l[0])
        if reference_record_len != len(type_cast):
            raise Exception('Record length does not match available type cast')
        if len(filter(lambda e: len(e) != reference_record_len, l)):
            raise Exception('Record length is not uniform')

    untyped_pgArray = _make_pgArray(_stringify_element_list(n) for n in l)

    patt_elements = ["\("]
    i = -1  # In case len(type_cast) == 1, i must be defined manually
    for i in range(len(type_cast) - 1):
        patt_elements.append("(?P<e%d>%s), " % (i, _element_patt))
    patt_elements.append("(?P<e%d>%s)\)" % (i + 1, _element_patt))
    pgArray_pattern = ''.join(patt_elements)
    return ('ARRAY['
            + _type_pgArray(untyped_pgArray, pgArray_pattern, type_cast)
            + ']::RECORD[]')


def list_to_pgTable(l, table_name, fields):
    '''This works in the same way as function list_to_pgArrayOfRecords
    when fields has more than one element but in the same way as
    function list_to_pgArray when fields has only one element, except
    that a pgSQL query code that evaluates to a table is returned. The
    argument fields is a list of tuple of two elements. The first
    element specifies the field name while the second one specifies
    the data type. For example:
        list_to_pgTable([(7L, 'Hello' + unichr(0x2013) + 'Hello'), (8, 'World'), (9, None)], 't', [('pk', 'INTEGER'), ('name', 'TEXT')])
    will result in:
        UNNEST(ARRAY[(7::INTEGER, 'Hello–Hello'::TEXT), (8::INTEGER, 'World'::TEXT), (9::INTEGER, NULL::TEXT)]::RECORD[]) AS t (pk INTEGER, name TEXT)

    The following illustrates the case when fields has only one element:
        list_to_pgTable(['Hello' + unichr(0x2013) + 'Hello', 'World', None], 't', [('name', 'TEXT')])
    will result in:
        UNNEST(ARRAY['Hello–Hello'::TEXT, 'World'::TEXT, NULL::TEXT]::TEXT[]) AS t (name)
    Exception is raised for the following case:
    1. Empty fields
    2. When fields length is more than one:
       2.1. length of each record in l is not uniform
       2.2. length of each record in l does not match the length of fields
    '''
    if len(fields) == 0:
        raise Exception('At least one field must be defined')
    if len(fields) == 1:
        field_name = fields[0][0]
        field_type = fields[0][1]
        return ('UNNEST('
                + list_to_pgArray(l, field_type)
                + ') AS ' + table_name
                + ' (' + field_name + ')')
    return ('UNNEST('
            + list_to_pgArrayOfRecords(l,
                                       [type_ for (name, type_) in fields])
            + ') AS ' + table_name
            + ' ('
            + ', '.join(name + ' ' + type_ for (name, type_) in fields)
            + ')')

if __name__ == '__main__':
    r = list_to_pgTable([
        ], 't', (('a', 'INTEGER'),
                 ('b', 'TEXT')))
    e = ('UNNEST(ARRAY[]::RECORD[]) AS t ('
         'a INTEGER, '
         'b TEXT)')
    assert(r == e)

    r = list_to_pgTable([
            "My friend's house!",
            r"If \\' is an apostrophe!",
            "He isn't sick!",
            None,
        ], 't', (('a', 'TEXT'),))
    e = ('UNNEST(ARRAY['
         r"'My friend\'s house!'::TEXT, "
         r"'If \\\\\' is an apostrophe!'::TEXT, "
         r"'He isn\'t sick!'::TEXT, "
         r"NULL::TEXT"
         ']::TEXT[]) AS t ('
         'a)')
    assert(r == e)

    r = list_to_pgTable([
            [7, "Hello Shane's!"],
            [20L, 'Wow'],
            [None, 'Really?'],
            [23L, None],
            [None, None],
        ], 't', (('a', 'INTEGER'),
                 ('b', 'TEXT')))
    e = ('UNNEST(ARRAY['
         r"(7::INTEGER, 'Hello Shane\'s!'::TEXT), "
         r"(20::INTEGER, 'Wow'::TEXT), "
         r"(NULL::INTEGER, 'Really?'::TEXT), "
         r"(23::INTEGER, NULL::TEXT), "
         r"(NULL::INTEGER, NULL::TEXT)"
         ']::RECORD[]) AS t ('
         'a INTEGER, '
         'b TEXT)')
    assert(r == e)

    r = list_to_pgTable([
            [7, "My friend's house!"],
            [20L, r"If \\' is an apostrophe!"],
            [None, "He isn't sick!"],
            [23L, None],
            [None, None],
        ], 't', (('a', 'INTEGER'),
                 ('b', 'TEXT')))
    e = ('UNNEST(ARRAY['
         r"(7::INTEGER, 'My friend\'s house!'::TEXT), "
         r"(20::INTEGER, 'If \\\\\' is an apostrophe!'::TEXT), "
         r"(NULL::INTEGER, 'He isn\'t sick!'::TEXT), "
         r"(23::INTEGER, NULL::TEXT), "
         r"(NULL::INTEGER, NULL::TEXT)"
         ']::RECORD[]) AS t ('
         'a INTEGER, '
         'b TEXT)')
    assert(r == e)

    r = list_to_pgTable([
            [7, "My friend's house!", "Puff' 'ffuP"],
            [20L, r"If \\' is an apostrophe!", r"\'\\'\\\''\\"],
            [23L, "If he isn't sick, he doesn't do it", None],
            [232218L, None, "He said: \"C'mon, boy's charm, isn't it?\""],
            [232221, None, None],
            [None, "He isn't sick!", 'Shakespeare said "WoW!"'],
            [None, "He said: \"C'mon, boy's charm, isn't it?\"", None],
            [None, None, "He said: \"C'mon, boy's charm, isn't it?\""],
            [None, None, None],
        ], 't', (('a', 'INTEGER'),
                 ('b', 'TEXT'),
                 ('c', 'TEXT')))
    e = ('UNNEST(ARRAY['
         r"(7::INTEGER, 'My friend\'s house!'::TEXT, 'Puff\' \'ffuP'::TEXT), "
         r"(20::INTEGER, 'If \\\\\' is an apostrophe!'::TEXT, '\\\'\\\\\'\\\\\\\'\'\\\\'::TEXT), "
         r"(23::INTEGER, 'If he isn\'t sick, he doesn\'t do it'::TEXT, NULL::TEXT), "
         r"""(232218::INTEGER, NULL::TEXT, 'He said: "C\'mon, boy\'s charm, isn\'t it?"'::TEXT), """
         r"(232221::INTEGER, NULL::TEXT, NULL::TEXT), "
         r"""(NULL::INTEGER, 'He isn\'t sick!'::TEXT, 'Shakespeare said "WoW!"'::TEXT), """
         r"""(NULL::INTEGER, 'He said: "C\'mon, boy\'s charm, isn\'t it?"'::TEXT, NULL::TEXT), """
         r"""(NULL::INTEGER, NULL::TEXT, 'He said: "C\'mon, boy\'s charm, isn\'t it?"'::TEXT), """
         r"(NULL::INTEGER, NULL::TEXT, NULL::TEXT)"
         ']::RECORD[]) AS t ('
         'a INTEGER, '
         'b TEXT, '
         'c TEXT)')
    assert(r == e)

    try:
        list_to_pgArrayOfRecords([(7L, 'Hello' + unichr(0x2013) + 'Hello'), (8,), (9, None)], ['INTEGER', 'TEXT'])
        assert(False)
    except Exception as e:
        assert(str(e) == 'Record length is not uniform')

    try:
        list_to_pgArrayOfRecords([(7L, 'Hello' + unichr(0x2013) + 'Hello'), (8, 'World'), (9, None)], ['INTEGER', 'TEXT', 'TEXT'])
        assert(False)
    except Exception as e:
        assert(str(e) == 'Record length does not match available type cast')

    try:
        list_to_pgArrayOfRecords([(7,), (8,)], ['INTEGER'])
        assert(False)
    except Exception as e:
        assert(str(e) == 'At least two type cast are needed')

    try:
        list_to_pgTable([], 't', [])
        assert(False)
    except Exception as e:
        assert(str(e) == 'At least one field must be defined')

    r = list_to_pgArray([], 'INTEGER')
    e = 'ARRAY[]::INTEGER[]'
    assert(r == e)

    r = list_to_pgArrayOfRecords([], ['INTEGER', 'TEXT'])
    e = 'ARRAY[]::RECORD[]'
    assert(r == e)

    r = list_to_pgTable([], 't', (('a', 'INTEGER'), ('b', 'TEXT'), ('c', 'TEXT')))
    e = 'UNNEST(ARRAY[]::RECORD[]) AS t (a INTEGER, b TEXT, c TEXT)'
    assert(r == e)
