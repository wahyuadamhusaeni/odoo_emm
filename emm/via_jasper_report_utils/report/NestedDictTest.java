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
import java.math.*;

public class NestedDictTest
{
    public static void main(String args[])
    {
        NestedDict nd = new NestedDict(new String[] {"description", "location", "month"},
                                       new String[] {"unit", "lt", "lb", "np"},
                                       new NestedDict.InitialValueFactory() {
                                           public Object getInitialValue(String fieldName)
                                           {
                                               if (fieldName.equals("unit")) {
                                                   return new Integer(0);
                                               } else if (fieldName.equals("lt")
                                                          || fieldName.equals("lb")
                                                          || fieldName.equals("np")) {
                                                   return new BigDecimal("0");
                                               } else {
                                                   throw new IllegalArgumentException("Unknown field name: "
                                                                                      + fieldName);
                                               }
                                           }
                                       });

        String[] fields = new String[] {"description", "location", "month", "unit", "lt", "lb", "np"};
        Object[] testData = {new Object[] {"House", "Area 54", "January", 1, new BigDecimal("1.3"), new BigDecimal("2.4"), new BigDecimal("722.2")},
                             new Object[] {"House", "Area 54", "January", 1, new BigDecimal("1.7"), new BigDecimal("2.6"), new BigDecimal("727.8")},
                             new Object[] {"House", "Area 11", "February", 1, new BigDecimal("1.7"), new BigDecimal("2.6"), new BigDecimal("727.8")},
                             new Object[] {"Apartment", "D 54", "March", 1, new BigDecimal("1.7"), new BigDecimal("2.6"), new BigDecimal("727.8")}};
        Object[] expectedRows = {new Object[] {"Apartment", "D 54", "March", 1, new BigDecimal("1.7"), new BigDecimal("2.6"), new BigDecimal("727.8")},
                                 new Object[] {"House", "Area 11", "February", 1, new BigDecimal("1.7"), new BigDecimal("2.6"), new BigDecimal("727.8")},
                                 new Object[] {"House", "Area 54", "January", 2, new BigDecimal("3.0"), new BigDecimal("5.0"), new BigDecimal("1450.0")}};

        for (int i = 0; i < testData.length; i++) {
            Object[] testDatum = (Object[]) testData[i];

            String[] keys = new String[4];
            System.arraycopy(testDatum, 0, keys, 0, keys.length - 1);

            keys[3] = "unit";
            Integer unit = (Integer) nd.getValue(keys);
            unit += (Integer) testDatum[3];
            nd.setValue(keys, unit);

            keys[3] = "lt";
            BigDecimal lt = (BigDecimal) nd.getValue(keys);
            lt = lt.add((BigDecimal) testDatum[4]);
            nd.setValue(keys, lt);

            keys[3] = "lb";
            BigDecimal lb = (BigDecimal) nd.getValue(keys);
            lb = lb.add((BigDecimal) testDatum[5]);
            nd.setValue(keys, lb);

            keys[3] = "np";
            BigDecimal np = (BigDecimal) nd.getValue(keys);
            np = np.add((BigDecimal) testDatum[6]);
            nd.setValue(keys, np);
        }

        int nth_row = 0;
        Map<String, Integer> field2idx = nd.getFieldToEntryIndexMapping();
        for (Object[] record : nd.getList()) {
            for (String field_name : fields) {
                assert(record[field2idx.get(field_name)].equals(((Object[]) expectedRows[nth_row])[field2idx.get(field_name)]));
            }
            nth_row++;
        }
    }
}