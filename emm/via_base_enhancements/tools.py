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

# Used for check_output
import subprocess
from subprocess import CalledProcessError

# Used for temp file utilities
from random import randint
from os import remove, SEEK_END
import hashlib

# Function caching
import sys
if sys.version_info.major == 2 and sys.version_info.minor >= 7:
    from python3functool_lru import lru_cache
elif sys.version_info.major >= 3:
    from functools import lru_cache
else:
    from python3functool_lru import lru_cache_dummy as lru_cache

# Used by get_precision
from math import log10, floor

# Used by formatspec_to_re:
from string import Formatter
import re
from datetime import datetime as dt


def resolve_o2m_operations(cr, uid, target_osv, operations, fields=[], context=None):
    """
    This is a copy of resolve_o2m_operations method found in account_voucher/account_voucher.py
    made available here for generic use.
    The method receive multiple form of m2o result and return a dictionary of the object read.
    The fields read can be specified.
    """
    results = []
    for operation in operations:
        result = None
        if not isinstance(operation, (list, tuple)):
            result = target_osv.read(cr, uid, operation, fields, context=context)
        elif operation[0] == 0:
            # may be necessary to check if all the fields are here and get the default values?
            result = operation[2]
        elif operation[0] == 1:
            result = target_osv.read(cr, uid, operation[1], fields, context=context)
            if not result:
                result = {}
            result.update(operation[2])
        elif operation[0] == 4:
            result = target_osv.read(cr, uid, operation[1], fields, context=context)
        if result is not None:
            results.append(result)
    return results


def prep_dict_for_write(cr, uid, val, context=None):
    """
    Prepare a dictionary for create or write method of ORM.
    The oft needed actions are translating the foreign key tuple (id, name) values
    to only the id.

    Return the passed in value unchanged in case of any error.
    """
    result = val
    if isinstance(result, dict):
        for (k, v) in result.items():
            if (isinstance(v, tuple) and (len(v) == 2)):
                result[k] = (v[0] is None and False) or v[0]
            if k in ('id', 'create_date', 'create_uid', 'write_date', 'write_uid'):
                del result[k]

    return result


def prep_dict_for_formatting(cr, uid, val, context=None):
    """
    Prepare a dictionary for string formatting operation.
    The oft needed actions are translating the foreign key tuple (id, name) values
    to only the name.

    Return the passed in value unchanged in case of any error.
    """
    result = val
    if isinstance(result, dict):
        for (k, v) in result.items():
            # Change (ID, NAME) tuples to the Name only
            if (isinstance(v, tuple) and (len(v) == 2)):
                if v[0] is None:
                    result[k] = ''
                else:
                    result[k] = v[1]
            # Change boolean value to empty string
            if (isinstance(v, bool)):
                if v is False:
                    result[k] = ''
                else:
                    result[k] = str(v)

    return result


def check_output(*popenargs, **kwargs):
    """
    This is a helper method to overcome the fact that check_output is only available
    with Python version 2.7
    """
#    if 'check_output' in dir(subprocess):
#        return subprocess.check_output(*popenargs, **kwargs)
#    else:
    _stream = ''
    _pipe = subprocess.PIPE
    try:
        if 'stdin' in kwargs:
            del kwargs['stdin']
        if 'stdout' in kwargs:
            del kwargs['stdout']
        if 'stderr' in kwargs:
            del kwargs['stderr']
        _stream = subprocess.Popen(*popenargs, stdin=_pipe, stdout=_pipe, stderr=_pipe, **kwargs).communicate()
        _stream = ' '.join(_stream)
    except:
        raise

    return _stream.strip()


def get_file_content(path=''):
    """
    This method will open a file, read all the content, and close it
    Returns the content of the file
    """
    rv = None
    try:
        _fo = open(path, 'r')
        _fo.seek(0, SEEK_END)
        _fs = _fo.tell()
        _fo.seek(-1 * _fs, SEEK_END)
        rv = _fo.read(_fs)
    except:
        raise
    finally:
        _fo.close()
    return rv


def purge_temp_file(path=''):
    """
    This method will open a temp file, write garbase into it, close it, and remove it
    """
    try:
        _fo = open(path, 'w')
        _fo.seek(0, SEEK_END)
        _fs = _fo.tell()
        _fo.seek(-1 * _fs, SEEK_END)
        _repeat = (_fs // 120) + 1
        _fo.writelines([hashlib.sha512(path).hexdigest()] * _repeat)
    finally:
        _fo.close()
        remove(path)


def write_temp_file(content=''):
    """
    This method will open a temp file, write the given content, and close it
    Returns the temp file's name
    """
    _fpath = '/tmp/%12d' % (randint(1, 999999999999))
    _fo = open(_fpath, 'w')
    _fo.write(content)
    _fo.flush()
    _fo.close()

    return _fpath


@lru_cache(maxsize=100)
def get_precision(number):
    """
    This method will return the precision of the given number
    """
    # If the given input is not a number, return 0
    try:
        number = float(number)
    except:
        return 10

    # If the precision is less than 0, return 0
    # This is due to the fact that number need to be printed in 0 digit decimals
    # anyway even if the precision is negative
    return max(-1 * int(floor(log10(number))), 0)


def format_file_name(template='', dict={}):
    _dt = dt.now()
    rv = _dt.strftime(template)
    rv = rv.format(**dict)
    _pattern = re.compile('[\\/:"*?<>|]+')
    return _pattern.sub("", rv)


@lru_cache(maxsize=20)
def formatspectype_to_reclass(type):
    # nan and inf is not handled
    rv = ''
    if type in ('s', 'c'):
        return ' -~'

    if type in ('b'):
        return '01'

    if type in ('o'):
        return '0-7'

    if type.lower() in ('x'):
        rv = '0-9a-f'
        return (type == type.lower()) and rv or rv.upper()

    if type.lower() in ('d', 'f', 'e', 'g', 'n', '%'):
        rv = '0-9.'

    if type.lower() in ('f', 'e', 'g', 'n', '%'):
        rv += '-'

    if type.lower() in ('e', 'g', 'n'):
        rv += 'e+'

    if type.lower() in ('e', 'g', 'n'):
        rv += 'e+'

    if type in ('%'):
        rv += '%'

    return (type == type.lower()) and rv or rv.upper()

STRFTIMESPEC_TO_RECLASS = {
    '%a': '\w{3,}?',                    # Abbreviated weekday
    '%A': '\w{3,}?',                    # Weekday
    '%w': '[0-6]',                      # Weekday as decimal number [0, 6]
    '%d': '[0-3][0-9]',                 # Day of month [01,31]
    '%m': '[01][0-9]',                  # Month as decimal number [01, 12]
    '%b': '\w{3,}?',                    # Abbreviated month name
    '%B': '\w{3,}?',                    # Month name
    '%y': '[0-9]{2}',                   # Year without century [00, 99]
    '%Y': '[0-9]{4}',                   # Year with century [0000, 9999]
    '%j': '[0-3][0-9]{2}',              # Day of year as decimal number [001, 366]
    '%U': '[0-5][0-9]',                 # Week of year as decimal number [00, 53], 01 starting from first Sunday
    '%W': '[0-5][0-9]',                 # Week of year as decimal number [00, 53], 01 starting from first Monday
    '%H': '[0-2][0-9]',                 # 24-hour clock hour [00, 23]
    '%I': '[01][0-9]',                  # 12-hour clock hour [01, 12]
    '%M': '[0-5][0-9]',                 # Minutes as decimal number [00, 59]
    '%S': '[0-6][0-9]',                 # Seconds as decimal number [00, 61]
    '%f': '[0-9]{6}',                   # Microsecond [000000,999999], zero padded
    '%p': '[AP][M]',                    # Locale equivalent of either AM or PM
    '%z': '[+-][01][0-9][0-5][0-9]',    # UTC offset in the form of +HHMM or -HHMM
    '%Z': '[A-Za-z/_0+-]*?',            # Timezone name, checked against http://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    '%x': '[A-za-z0-9\:-+ ]+?',         # Locale date representation
    '%X': '[A-za-z0-9\:-+ ]+?',         # Locale time representation
    '%c': '[A-za-z0-9\:-+ ]+?',         # Locale date time representation
    '%%': '[%]',                        # % character
}


@lru_cache(maxsize=100)
def strftimespec_to_reclass(literal):
    _pattern = re.compile('|'.join(re.escape(key) for key in STRFTIMESPEC_TO_RECLASS.keys()))
    rv = _pattern.sub(lambda x: STRFTIMESPEC_TO_RECLASS[x.group()], literal)

    return rv


@lru_cache(maxsize=100)
def formatspec_to_re(format_spec):
    _parts = Formatter().parse(format_spec)
    _parts_array = []
    for _part in _parts:
        print _part
        # _part is a tuple that contains (literal_text, field_name, format_spec, conversion)
        # conversion will be ignored
        # field_name need to be replaced by (?P<field_name>...)
        # format_spec will fill in the ... in the field_name above
        #     format_spec can be of the following format
        #     [[fill]align][sign][#][0][width][,][.precision][type]
        #     type is the major determinant here, will be translated to re class
        #     the maximum between width and precision will became the number of repetition that may happen to re class
        #     align (1 char, < > = ^) will be ignored
        #     fill (1 char, any character) is to be added to the re class determined by type
        #     sign (1 char, + - or space) will be added to the re class determined by type
        #     # will add box to the re class determined by type (as a representation of binary, octal, or hexadecimal)
        #     0 (1 char) will be ignored as all classes has contained 0
        #     , (1 char) will be added to the re class determined by type
        #     . (1 char) will be added to the re class determined by type
        _re_field = ""
        if _part[1] and _part[2]:
            _format_spec = list(_part[2])
            _type = _format_spec.pop()
            _class = formatspectype_to_reclass(_type)
            if not _class:
                # Last character is not type, so assume string and re-add the last character to _format_spec
                _class = formatspectype_to_reclass("s")  # Defaults to string
                _format_spec.append(_type)

            _width = ""         # Used to collect digits for width
            _precision = 0      # The precision in format_spec
            _alignment = False  # Used to signify that alignment has been found, thus the next character will be fill
            for c in reversed(_format_spec):  # Process from last as it is more predictable
                if re.match('[0-9]', c) and not _alignment:
                    # A digit, either width, precision or 0.  0 will be followed by non digit
                    # Prepend to the last _width
                    _width = c + _width
                elif re.match('[.]', c) and not _alignment:
                    # .
                    # The last collected digits (in _width) is a precision, reset the _width, add . to _class
                    _precision = long(_width or '0')
                    _width = ""
                    _class += (c not in _class) and c or ''
                elif re.match('[,]', c) and not _alignment:
                    # , to be added to _class
                    _class += (c not in _class) and c or ''
                elif re.match('[#]', c) and not _alignment:
                    # b, o, x to be added to _class
                    _class += 'box'
                elif re.match('[-+ ]', c) and not _alignment:
                    # sign
                    # character to be added to _class
                    _class += (c not in _class) and c or ''
                elif re.match('[>=^<]', c) and not _alignment:
                    # align, ignored
                    _alignment = True
                else:
                    # fill, add the character to the _class
                    _class += (c not in _class) and c or ''

            _width = long(_width or '0')
            _width = max(_width, _precision)
            _width = _width and str(_width) or '+'
            _re_field = "(?P<{field_name}>[{re_class}]{width}?)".format(field_name=_part[1], re_class=_class, width=_width)

        # literal_text, if contain bits that are recognized by strftime, convert it to regex
        _literal = _part[0]
        if _literal and "%" in _literal:
            _literal = strftimespec_to_reclass(_literal)

        _parts_array.append("{}{}".format(_literal, _re_field))

    return ''.join(_parts_array)


if __name__ == '__main__':
# Test code for lru_cache and get_precision
#     from datetime import datetime as dt
#     import random
#     import math

#     for i in range(100):
#         a = dt.now()
#         _number = math.pow(10, random.randint(-10, 10))
#         _precision = get_precision(_number)
#         b = dt.now()
#         print "Getting precision of number %22s in %s seconds: %3d" % ('%.10f' % (_number), str(b - a), _precision)
#
#     print get_precision.cache_info()

# Test code for formatspec_to_re
    print formatspec_to_re("SP{id:d}_{name:s}_%Y%m%d.csv")
