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
import java.io.*;
import java.text.*;

public class ValueChangeDetector
{
    private TreeMap<String, Object> lastValue;
    private PrintStream log;
    private Format dateFormatter;
    private boolean loggingOn;

    public Object logObjects(String prefix, Object objectToReturn, Object... objectsToInspect)
    {
        String messageUnit = " %s (%s)";
        String message = "";

        if (prefix != null) {
            message = prefix;
        }

        if (objectsToInspect != null) {
            for (Object objectToInspect : objectsToInspect) {
                if (objectToInspect == null) {
                    message += String.format(messageUnit, "null", "");
                } else {
                    message += String.format(messageUnit,
                                             objectToInspect.getClass().getCanonicalName(),
                                             objectToInspect.toString());
                }
            }
        } else {
            message += String.format(messageUnit, "null", "");
        }

        log(message, objectToReturn);

        return objectToReturn;
    }

    public Object log(String message, Object objectToReturn)
    {
        log.printf("[%s] %s\n", dateFormatter.format(new Date()), message);
        return objectToReturn;
    }

    public ValueChangeDetector()
    {
        lastValue = new TreeMap<String, Object>();
        dateFormatter = new SimpleDateFormat("yyyy-MM-dd H:m:s.S");
        try {
            log = new PrintStream(new FileOutputStream("/tmp/vcd.log", true));
        } catch(FileNotFoundException fnfe) {
            throw new IllegalStateException(fnfe);
        }
    }

    public ValueChangeDetector(boolean loggingOn)
    {
        this();
        this.loggingOn = loggingOn;
    }

    public ValueChangeDetector createDetector(String[] fieldNames)
    {
        for (String fieldName : fieldNames) {
            lastValue.put(fieldName, null);
        }
        return this;
    }

    public boolean detectChange(String fieldName, Object newValue)
    {
        Object oldValue = lastValue.get(fieldName);

        if (loggingOn) logObjects("[VCD] detectChange:", null, fieldName, oldValue, newValue);

        if (oldValue == null) {
            lastValue.put(fieldName, newValue);
            if (loggingOn) logObjects("[VCD] detectChange: oldValue == null",
                                      null, fieldName, new Boolean(newValue != null));
            return newValue != null;
        }

        if (loggingOn) logObjects("[VCD] detectChange: oldValue != null", null, fieldName);

        if (oldValue.equals(newValue)) {
            if (loggingOn) logObjects("[VCD] detectChange: oldValue == newValue", null, fieldName);
            return false;
        } else {
            lastValue.put(fieldName, newValue);
            if (loggingOn) logObjects("[VCD] detectChange: oldValue != newValue", null, fieldName);
            return true;
        }
    }

    public static void main(String args[])
    {
        ValueChangeDetector vcd = new ValueChangeDetector();
        assert(vcd.detectChange("field1", "xxx") == true);
        assert(vcd.detectChange("field1", "xxx") == false);
        assert(vcd.detectChange("field1", "xxx") == false);
        assert(vcd.detectChange("field1", "xxy") == true);
        assert(vcd.detectChange("field1", "xxy") == false);
        assert(vcd.detectChange("field2", "xxy") == true);
        assert(vcd.detectChange("field2", "xxy") == false);
        assert(vcd.detectChange("field2", "xxx") == true);
        vcd = vcd.createDetector(new String[] {"field1"});
        assert(vcd.detectChange("field1", "xxx") == true);
        assert(vcd.detectChange("field2", "xxx") == false);
        vcd = vcd.createDetector(new String[] {"field2"});
        assert(vcd.detectChange("field1", "xxx") == false);
        assert(vcd.detectChange("field2", "xxx") == true);
        vcd = vcd.createDetector(new String[] {"field1", "field2"});
        assert(vcd.detectChange("field1", "xxx") == true);
        assert(vcd.detectChange("field2", "xxx") == true);
        assert(vcd.detectChange("field2", null) == true);
        assert(vcd.detectChange("field2", null) == false);
        assert(vcd.detectChange("field2", null) == false);
        assert(vcd.detectChange("field2", "www") == true);
        assert(vcd.detectChange("field2", "www") == false);
        assert(vcd.detectChange("field2", null) == true);
        assert(vcd.detectChange("field2", null) == false);

        assert(vcd.detectChange("field3", Arrays.asList("Dept1", "PR1")) == true);
        assert(vcd.detectChange("field3", Arrays.asList("Dept1", "PR1")) == false);
        assert(vcd.detectChange("field3", Arrays.asList("Dept2", "PR1")) == true);
        assert(vcd.detectChange("field3", Arrays.asList("Dept2", "PR1")) == false);
        assert(vcd.detectChange("field3", Arrays.asList("Dept2", "PR2")) == true);
        vcd = vcd.createDetector(new String[] {"field3"});
        assert(vcd.detectChange("field3", Arrays.asList("Dept2", "PR2")) == true);
        assert(vcd.detectChange("field3", Arrays.asList("Dept2", "PR2")) == false);
        assert(vcd.detectChange("field3", Arrays.asList("Dept1", "PR2")) == true);
        assert(vcd.detectChange("field3", Arrays.asList((Object) null, "PR2")) == true);
        assert(vcd.detectChange("field3", Arrays.asList((Object) null, null)) == true);
        assert(vcd.detectChange("field3", Arrays.asList((Object) null, null)) == false);
        assert(vcd.detectChange("field3", Arrays.asList("Dept1", "PR2")) == true);
        assert(vcd.detectChange("field3", Arrays.asList("Dept1", "PR2")) == false);
        assert(vcd.detectChange("field3", Arrays.asList("Dept1", null)) == true);
        assert(vcd.detectChange("field3", Arrays.asList("Dept1", null)) == false);

        assert(vcd.detectChange("field4", Arrays.asList((Object) null)) == true);
        assert(vcd.detectChange("field4", Arrays.asList((Object) null)) == false);
        assert(vcd.detectChange("field4", Arrays.asList("Dept1")) == true);
        assert(vcd.detectChange("field4", Arrays.asList("Dept1")) == false);
    }
}
