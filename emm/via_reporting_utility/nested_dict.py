# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
#    Copyright (c) 2011 - 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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


class NestedDictCat(object):
    def __init__(self, name, keys, subcat=None):
        self.name = name
        self.ordered_keys = keys
        self.keys = set(keys)
        self.subcat = subcat

    def traverse(self, process_cat):
        def _traverse(cat):
            if cat is None:
                return
            process_cat(cat)
            _traverse(cat.subcat)
        _traverse(self)

    def as_list(self):
        result = []
        self.traverse(lambda cat: result.append(cat))
        return result

class NestedDict(object):
    def __init__(self, nested_dict_cat, initial_value=None, _nested_dict=None):
        self.initial_value = initial_value
        self.cat = nested_dict_cat
        if _nested_dict is not None:
            self.nested_dict = _nested_dict
            self.cat_count = 0
            cat = self.cat
            while cat:
                self.cat_count += 1
                cat = cat.subcat
        else:
            (self.nested_dict,
             self.cat_count) = self._create_nested_dict()

    def get_initial_value(self):
        if callable(self.initial_value):
            return self.initial_value()
        else:
            return self.initial_value

    def traverse(self, process_leaf):
        keys = []

        def _traverse(cat):
            if cat is None:
                process_leaf(list(keys))
                return
            for key in cat.keys:
                keys.append(key)
                _traverse(cat.subcat)
                keys.pop()
        _traverse(self.cat)

    def update(self, nested_dict, updater):
        # Ensure that nested_dict has the same topology
        cat = self.cat
        another_cat = nested_dict.cat
        while cat and another_cat:
            if (cat.name != another_cat.name
                or cat.keys != another_cat.keys):
                raise KeyError('NestedDict update data has different category !')
            cat = cat.subcat
            another_cat = another_cat.subcat
        if cat is not None or another_cat is not None:
            raise KeyError('NestedDict update data has different category !')

        def _updater(keys):
            new_val = updater(self.get_value(*keys),
                              nested_dict.get_value(*keys))
            keys.append(new_val)
            self.set_value(*keys)
        self.traverse(_updater)

    def set_value(self, *args):
        keys = args[:-1]
        value = args[-1]
        self._validate_keys(keys)
        return self._go_to_leaf(keys, value)

    def get_value(self, *keys):
        self._validate_keys(keys)
        return self._go_to_leaf(keys)

    def get_view(self, *keys):
        if self.cat_count < len(keys):
            raise KeyError('Invalid keys length (at most: %d)' % self.cat_count)

        invalid_key = self._all_keys_exist(keys)
        if invalid_key is not None:
            raise KeyError('Invalid key "%s" for cat "%s"'
                           % (invalid_key[0], invalid_key[1]))

        if len(keys) == self.cat_count:
            return None

        cat = self.cat
        _nested_dict = self.nested_dict
        for key in keys:
            _nested_dict = _nested_dict[key]
            cat = cat.subcat
        return NestedDict(cat, initial_value=self.initial_value,
                          _nested_dict=_nested_dict)

    def reset(self):
        def _reset(keys):
            keys.append(self.get_initial_value())
            self.set_value(*keys)
        self.traverse(_reset)

    def _validate_keys(self, keys):
        if self.cat_count != len(keys):
            raise KeyError('Invalid keys length (expected: %d)' % self.cat_count)

        invalid_key = self._all_keys_exist(keys)
        if invalid_key is not None:
            raise KeyError('Invalid key "%s" for cat "%s"'
                           % (invalid_key[0], invalid_key[1]))

    def _go_to_leaf(self, keys, value=None):
        dict_ = self.nested_dict
        prev_dict = dict_
        for key in keys:
            prev_dict = dict_
            dict_ = dict_[key]

        last_key = key
        value_prev = dict_
        dict_ = prev_dict
        if value is not None:
            dict_[last_key] = value
        return value_prev

    def _all_keys_exist(self, keys):
        idx = 0
        cat = self.cat
        while cat:
            try:
                key = keys[idx]
            except IndexError:
                return None
            if key not in cat.keys:
                return (str(key), cat.name)
            idx += 1
            cat = cat.subcat
        return None

    def _create_nested_dict(self):
        '''Given a NestedDictCat like "Month" containing "January" and "February"
        that is linked to NestedDictCat "Company" containing "Com 1", "Com 2" and
        "Com 3", return:
        {
            "January": {
                "Com 1": initial_value,
                "Com 2": initial_value,
                "Com 3": initial_value
            },
            "February": {
                "Com 1": initial_value,
                "Com 2": initial_value,
                "Com 3": initial_value
            },
        }
        '''
        def create_dict(column_names):
            res = {}
            for name in column_names:
                res[name] = {}
            return res

        cat = self.cat
        cat_count = 1

        dict_ = create_dict(cat.keys)

        # Craft the nested dictionary
        bottom_level_entries = list(dict_.itervalues())
        prev_bottom_level_entries = [dict_]
        while cat.subcat:
            cat = cat.subcat
            cat_count += 1
            prev_bottom_level_entries = bottom_level_entries
            bottom_level_entries = []
            for entry in prev_bottom_level_entries:
                _dict_ = create_dict(cat.keys)
                entry.update(_dict_)
                bottom_level_entries.extend(_dict_.itervalues())

        # Set all leave nodes to be None
        for entry in prev_bottom_level_entries:
            for k in entry.iterkeys():
                entry[k] = self.get_initial_value()

        return (dict_, cat_count)

if __name__ == '__main__':
    levels = NestedDictCat('year', [2011, 2012],
                           NestedDictCat('month', ['January', 'December'],
                                         NestedDictCat('company', ['FSF', 'Google'])))
    assert(len(levels.as_list()) == 3)

    nd = NestedDict(levels)
    assert(nd.nested_dict == (
        {
            2011: {
                'January': {
                    'Google': None,
                    'FSF': None
                },
                'December': {
                    'Google': None,
                    'FSF': None
                }
            },
            2012: {
                'January': {
                    'Google': None,
                    'FSF': None
                },
                'December': {
                    'Google': None,
                    'FSF': None
                }
            },
        }))

    try:
        nd.get_value(2011)
        assert(False)
    except KeyError:
        pass
    try:
        nd.get_value(2011, 'January', 'Googled')
        assert(False)
    except KeyError:
        pass
    try:
        nd.get_value(2011, 'January', 'Google', 'More')
        assert(False)
    except KeyError:
        pass
    try:
        nd.set_value(2011, 'January', 'Google', 'More', 77)
        assert(False)
    except KeyError:
        pass
    try:
        nd.set_value(2011, 'January', 'Google')
        assert(False)
    except KeyError:
        pass
    try:
        nd.set_value(2011, 'January', 'Googled', 7)
        assert(False)
    except KeyError:
        pass

    val_1 = 7.8
    val_2 = 123.11
    assert(nd.set_value(2011, 'December', 'FSF', val_1) is None)
    assert(nd.set_value(2012, 'January', 'Google', val_2) is None)
    assert(nd.nested_dict == (
        {
            2011: {
                'January': {
                    'Google': None,
                    'FSF': None
                },
                'December': {
                    'Google': None,
                    'FSF': val_1
                }
            },
            2012: {
                'January': {
                    'Google': val_2,
                    'FSF': None
                },
                'December': {
                    'Google': None,
                    'FSF': None
                }
            },
        }))

    assert(nd.get_view(2011, 'January', 'FSF') is None)
    assert(nd.get_view().nested_dict == nd.nested_dict)

    view_2011 = nd.get_view(2011)
    assert(view_2011.get_value('December', 'FSF') == val_1)
    view_2011.set_value('January', 'Google', 982922.10)
    assert(view_2011.get_value('January', 'Google')
           == nd.get_value(2011, 'January', 'Google'))

    view_2011_update = NestedDict(NestedDictCat('month',
                                                ['January', 'December'],
                                                NestedDictCat('company',
                                                              ['FSF', 'Google'])))
    view_2011_update.set_value('December', 'Google', 777.87)
    view_2011_update.set_value('December', 'FSF', 500)

    def updater(target, source):
        if target is None:
            target = 0.0
        if source is None:
            source = 0.0
        return target + source
    view_2011.update(view_2011_update, updater)
    assert(nd.nested_dict == (
        {
            2011: {
                'January': {
                    'Google': 982922.10,
                    'FSF': 0.0
                },
                'December': {
                    'Google': 777.87,
                    'FSF': val_1 + 500
                }
            },
            2012: {
                'January': {
                    'Google': val_2,
                    'FSF': None
                },
                'December': {
                    'Google': None,
                    'FSF': None
                }
            },
        }))

    nd_2 = NestedDict(NestedDictCat('Cat 1', ['a', 'b']), initial_value=[0.0])
    nd_2.get_value('a')[0] = 8.0
    assert(nd_2.nested_dict == ({
        'a': [8.0],
        'b': [8.0]
    }))
    nd_2.reset()
    nd_2.get_value('a')[0] = 8.0
    assert(nd_2.nested_dict == ({
        'a': [8.0],
        'b': [8.0]
    }))

    nd_3 = NestedDict(NestedDictCat('Cat 1', ['a', 'b']),
                      initial_value=lambda: [0.0])
    nd_3.get_value('a')[0] = 8.0
    assert(nd_3.nested_dict == ({
        'a': [8.0],
        'b': [0.0]
    }))
    nd_3.reset()
    nd_3.get_value('a')[0] = 8.0
    assert(nd_3.nested_dict == ({
        'a': [8.0],
        'b': [0.0]
    }))

    nd_4 = NestedDict(NestedDictCat('Cat 1', ['a', 'b'],
                                    NestedDictCat('Cat 2', [1, 2])),
                      initial_value=lambda: [0.0])
    assert(nd_4.nested_dict == ({
        'a': {
            1: [0.0],
            2: [0.0]
        },
        'b': {
            1: [0.0],
            2: [0.0]
        }
    }))

    def setter(keys):
        keys.append([0.3])
        nd_4.set_value(*keys)
    nd_4.traverse(setter)
    assert(nd_4.nested_dict == ({
        'a': {
            1: [0.3],
            2: [0.3]
        },
        'b': {
            1: [0.3],
            2: [0.3]
        }
    }))
    nd_4.get_view('b').reset()
    assert(nd_4.nested_dict == ({
        'a': {
            1: [0.3],
            2: [0.3]
        },
        'b': {
            1: [0.0],
            2: [0.0]
        }
    }))
