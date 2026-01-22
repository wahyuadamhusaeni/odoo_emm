/*****************************************************************************
 * Copyright (C) 2012  Vikasa Infinity Anugrah <http://www.infi-nity.com>    *
 *                                                                           *
 * This program is free software: you can redistribute it and/or modify      *
 * it under the terms of the GNU General Public License as published by      *
 * the Free Software Foundation, either version 3 of the License, or         *
 * (at your option) any later version.                                       *
 *                                                                           *
 * This program is distributed in the hope that it will be useful,           *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of            *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             *
 * GNU General Public License for more details.                              *
 *                                                                           *
 * You should have received a copy of the GNU General Public License         *
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.     *
 *****************************************************************************/

import java.util.Date;
import net.sf.jasperreports.engine.JasperCompileManager;
import net.sf.jasperreports.engine.JRException;
import net.sf.jasperreports.engine.design.JasperDesign;
import net.sf.jasperreports.engine.xml.JRXmlLoader;
import java.io.File;
import java.io.PrintStream;

public class JasperCompiler
{
    public static void main(String args[]) throws Exception
    {
	String RESET_SEQ = "\033[0m";
	String BLUE_COLOR_SEQ = "\033[1;34m";
	String RED_COLOR_SEQ = "\033[1;31m";
	String GREEN_COLOR_SEQ = "\033[1;32m";
	PrintStream devNull = new PrintStream("/dev/null");

	for (String arg : args) {
	    System.out.print("Compiling " + BLUE_COLOR_SEQ + arg + RESET_SEQ
			     + " ...");
	    Date startTime = new Date();
	    boolean isErr = false;
	    String errMsg = null;
	    System.setErr(devNull);
	    try {
		File sourceFile = new File(arg);
		String baseName = sourceFile.getName();
		int trunkLength = baseName.length() - 6; /* len(".jrxml") == 6 */
		String sourceFileNameTrunk = baseName.substring(0, trunkLength);

		JasperDesign jasperDesign = JRXmlLoader.load(arg);

		File destFile = new File(sourceFile.getParent(),
					 sourceFileNameTrunk + ".jasper");
		String destFileName = destFile.toString();

		JasperCompileManager.compileReportToFile(jasperDesign,
							 destFileName);
	    } catch (JRException e) {
		isErr = true;
		errMsg = e.getMessage();
	    }
	    System.setErr(System.err);
	    Date endTime = new Date();
	    long deltaTime = endTime.getTime() - startTime.getTime();
	    System.out.print(" " + GREEN_COLOR_SEQ + (deltaTime / 1000.0) + "s"
			     + RESET_SEQ);
	    if (isErr) {
		System.out.println(": " + RED_COLOR_SEQ + "ERROR: "
				   + (errMsg == null ? "" : errMsg) + RESET_SEQ);
		System.exit(1);
	    }
	    System.out.println("");
	}	
    }
}
