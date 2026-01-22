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

from osv import fields, osv


class HeaderHTML(osv.osv):
    _inherit = "ir.header_webkit"

    _format_selection = [
        ('A0' ,'A0  5   841 x 1189 mm'),
        ('A1' ,'A1  6   594 x 841 mm'),
        ('A2' ,'A2  7   420 x 594 mm'),
        ('A3' ,'A3  8   297 x 420 mm'),
        ('A4' ,'A4  0   210 x 297 mm, 8.26 x 11.69 inches'),
        ('A5' ,'A5  9   148 x 210 mm'),
        ('A6' ,'A6  10  105 x 148 mm'),
        ('A7' ,'A7  11  74 x 105 mm'),
        ('A8' ,'A8  12  52 x 74 mm'),
        ('A9' ,'A9  13  37 x 52 mm'),
        ('B0' ,'B0  14  1000 x 1414 mm'),
        ('B1' ,'B1  15  707 x 1000 mm'),
        ('B2' ,'B2  17  500 x 707 mm'),
        ('B3' ,'B3  18  353 x 500 mm'),
        ('B4' ,'B4  19  250 x 353 mm'),
        ('B5' ,'B5  1   176 x 250 mm, 6.93 x 9.84 inches'),
        ('B6' ,'B6  20  125 x 176 mm'),
        ('B7' ,'B7  21  88 x 125 mm'),
        ('B8' ,'B8  22  62 x 88 mm'),
        ('B9' ,'B9  23  33 x 62 mm'),
        ('B10',':B10    16  31 x 44 mm'),
        ('C5E','C5E 24  163 x 229 mm'),
        ('Comm10E','Comm10E 25  105 x 241 mm, U.S. Common 10 Envelope'),
        ('DLE', 'DLE 26 110 x 220 mm'),
        ('Executive','Executive 4   7.5 x 10 inches, 190.5 x 254 mm'),
        ('Folio','Folio 27  210 x 330 mm'),
        ('Ledger', 'Ledger  28  431.8 x 279.4 mm'),
        ('Legal', 'Legal    3   8.5 x 14 inches, 215.9 x 355.6 mm'),
        ('Letter','Letter 2 8.5 x 11 inches, 215.9 x 279.4 mm'),
        ('Tabloid', 'Tabloid 29 279.4 x 431.8 mm'),
        ('Custom', 'Custom - Specified in Paper Height/Width'),
    ]

    _columns = {
        'format': fields.selection(_format_selection, 'Paper size', required=True, help="Select Proper Paper size"),
        'paper_height': fields.integer('Paper Height', help="The height of the paper in mm"),
        'paper_width': fields.integer('Paper Width', help="The width of the paper in mm"),
    }

HeaderHTML()
