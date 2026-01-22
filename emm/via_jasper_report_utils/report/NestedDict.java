/*******************************************************************************
 *                                                                             *
 *  Vikasa Infinity Anugrah, PT                                                *
 *  Copyright (C) 2011-2012 Vikasa Infinity Anugrah <http://www.infi-nity.com> *
 *                                                                             *
 *  This program is free software: you can redistribute it and/or modify       *
 *  it under the terms of the GNU Affero General Public License as             *
 *  published by the Free Software Foundation, either version 3 of the         *
 *  License, or (at your option) any later version.                            *
 *                                                                             *
 *  This program is distributed in the hope that it will be useful,            *
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of             *
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              *
 *  GNU Affero General Public License for more details.                        *
 *                                                                             *
 *  You should have received a copy of the GNU Affero General Public License   *
 *  along with this program.  If not, see http://www.gnu.org/licenses/.        *
 *                                                                             *
 *******************************************************************************/

import java.util.*;

public class NestedDict
{
    protected String cat[];
    protected String field[];
    protected InitialValueFactory initValFactory;
    protected int keyLength;
    protected HashMap<Object, Object> nestedDict;
    protected HashMap<String, Integer> field2idx;

    public interface InitialValueFactory
    {
        public Object getInitialValue(String fieldName);
    }

    public NestedDict(String cat[], String field[],
                      InitialValueFactory initValFactory)
    {
        if (field == null || field.length == 0) {
            throw new IllegalArgumentException("Parameter field must contain at"
                                               + " least one element");
        }
        if (initValFactory == null) {
            throw new IllegalArgumentException("Parameter initValFactory cannot"
                                               + " be null");
        }
        this.cat = cat;
        if (this.cat == null) {
            this.cat = new String[0];
        }
        this.field = field;
        this.initValFactory = initValFactory;
        this.keyLength = cat.length + 1;
        this.nestedDict = new HashMap<Object, Object>();

        createFieldToEntryIndexMapping();
    }

    protected void checkKeys(String keys[])
    {
        if (keys.length != keyLength) {
            throw new IllegalArgumentException("Key length is " + keys.length
                                               + " (Expected: " + keyLength
                                               + ")");
        }
    }

    protected HashMap<Object, Object> goToLeafAtEachNode(String keys[],
                                                         HashMap<Object, Object> nd)
    {
        String key = keys[0];

        if (keys.length == 1) {
            Object o = nd.get(key);
            if (o == null) {
                nd.put(key, initValFactory.getInitialValue(key));
            }
            return nd;
        }

        HashMap<Object, Object> next_nd = (HashMap<Object, Object>) nd.get(key);
        if (next_nd == null) {
            next_nd = new HashMap<Object, Object>();
            nd.put(key, next_nd);
        }

        String next_keys[] = new String[keys.length - 1];
        System.arraycopy(keys, 1, next_keys, 0, keys.length - 1);
        return goToLeafAtEachNode(next_keys, next_nd);
    }

    protected HashMap<Object, Object> goToLeaf(String keys[])
    {
        return goToLeafAtEachNode(keys, nestedDict);
    }

    public void setValue(String keys[], Object value)
    {
        checkKeys(keys);
        goToLeaf(keys).put(keys[keys.length - 1], value);
    }

    public Object getValue(String keys[])
    {
        checkKeys(keys);
        return goToLeaf(keys).get(keys[keys.length - 1]);
    }

    private void getListAtEachNode(int keyIdx, HashMap<Object, Object> nd,
                                   HashMap<String, Object> recordValue,
                                   List<Object[]> result)
    {
        // DFT
        Iterator<Map.Entry<Object, Object>> itr = nd.entrySet().iterator();
        while (itr.hasNext()) {
            Map.Entry<Object, Object> entry = itr.next();

            if (keyIdx + 1 == keyLength) {
                recordValue.put((String) entry.getKey(), entry.getValue());
            } else {
                recordValue.put((String) cat[keyIdx], entry.getKey());
                getListAtEachNode(keyIdx + 1,
                                  (HashMap<Object, Object>) entry.getValue(),
                                  recordValue,
                                  result);
            }
        }

        // Complete data for one record have been read into recordValue
        if (keyIdx + 1 == keyLength) {
            Object[] record = new Object[field2idx.size()];
            Iterator<Map.Entry<String, Integer>> mapper = field2idx.entrySet().iterator();
            while (mapper.hasNext()) {
                Map.Entry<String, Integer> entry = mapper.next();
                record[entry.getValue()] = recordValue.get(entry.getKey());
            }
            result.add(record);
        }
    }

    public List<Object[]> getList()
    {
        return this.getList(new Comparator<Object[]>() {
            public boolean equals(Object obj) {
                return obj.equals(this);
            }

            public int compare(Object[] o1, Object[] o2) {
                if (o1.length != o2.length) {
                    throw new ClassCastException("o1.length != o2.length");
                }
                int last_comparison = 0;
                for (int idx = 0; idx < cat.length; idx++) {
                    if (o1[idx] == null && o2[idx] == null) {
                        last_comparison = 0;
                    } else if (o1[idx] == null) {
                        last_comparison = 1;
                    } else if (o2[idx] == null) {
                        last_comparison = -1;
                    } else if (o1[idx] instanceof Comparable) {
                        last_comparison = ((Comparable) o1[idx]).compareTo(o2[idx]);
                    } else if (o2[idx] instanceof Comparable) {
                        last_comparison = -((Comparable) o2[idx]).compareTo(o1[idx]);
                    } else {
                        throw new ClassCastException("Both o1 and o2 are not null and not instances of Comparable");
                    }
                    if (last_comparison != 0) {
                        return last_comparison;
                    }
                }
                return last_comparison;
            }
        });
    }

    public List<Object[]> getList(Comparator<Object[]> sorter)
    {
        ArrayList<Object[]> result = new ArrayList<Object[]>();
        getListAtEachNode(0, nestedDict, new HashMap<String, Object>(), result);
        Collections.sort(result, sorter);
        return result;
    }

    public Map<String, Integer> getFieldToEntryIndexMapping()
    {
        return field2idx;
    }

    protected void createFieldToEntryIndexMapping()
    {
        int cnt = 0;
        field2idx = new HashMap<String, Integer>();
        for (String c : cat) {
            field2idx.put(c, cnt++);
        }
        for (String f : field) {
            field2idx.put(f, cnt++);
        }
    }
}
