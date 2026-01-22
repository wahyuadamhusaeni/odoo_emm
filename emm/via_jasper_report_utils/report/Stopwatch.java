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

public class Stopwatch
{
    public Date timeStart;
    public Date timeEnd;
    public long deltaMs;

    public Stopwatch start()
    {
        timeStart = new Date();
        return this;
    }

    public Stopwatch stop()
    {
        if (timeEnd == null) {
            timeEnd = new Date();
        }
        return this;
    }

    public Stopwatch unstop()
    {
        timeEnd = null;
        return this;
    }

    public Stopwatch computeDeltaMs()
    {
        deltaMs = timeEnd.getTime() - timeStart.getTime();
        return this;
    }
}
