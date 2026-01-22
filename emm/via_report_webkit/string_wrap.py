# -*- encoding: utf-8 -*-
##############################################################################
#
#    PT Vikasa Infinity Anugrah
#    Copyright (c) 2011 - 2014 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from textwrap import wrap
from copy import copy


def wrap_line(column_list_source, column_width_list):
    total_column = len(column_width_list)
    # Return empty value if column_width_list has no value
    if not total_column:
        return [-1, [], [], 0]

    # If the length of column_list_source and olumn_width_list is not the same, raise an error
    if total_column != len(column_list_source):
        raise IndexError("The number of columns in the provided value list differs from that of column width list.")

    source_list = copy(column_list_source)
    dest_list = []
    wrapped_column = 0
    wrappable_column = 0

    for _idx, _width in enumerate(column_width_list):
        # Wrap the text, take the first wrapped text and return the remaining text as source
        # If there is nothing wrapped, return an empty string
        source_list_idx = source_list and unicode(source_list[_idx]).strip() or ''
        _source_list_filtered = source_list_idx.replace('<br/>', '\n')
        _string_to_wrap = _source_list_filtered.split('\n', 1)
        _string_to_wrap = _string_to_wrap and _string_to_wrap[0] or ''
        _wrapped = wrap(_string_to_wrap, _width)
        _to_append = _wrapped and _wrapped[0].strip() or ''
        dest_list.append(_to_append)
        source_list[_idx] = _source_list_filtered[len(_to_append):].strip()

        # Prepare the return values
        rv = len(source_list[_idx])
        wrapped_column += (rv) and 1 or 0
        wrappable_column += ((rv > _width) or source_list[_idx].find('\n')) and 1 or 0

    return [wrapped_column, source_list, dest_list, wrappable_column]


def text_wrap(text, width, maxwrap=None, **kwargs):
    _notes_line = []
    for line in (text or '').splitlines():
        _notes_line.extend(wrap(line, width, **kwargs))

    _numlines = len(_notes_line)
    _maxwrap = min([maxwrap or _numlines, _numlines])
    return _notes_line[:_maxwrap]
