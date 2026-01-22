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

from osv import orm, fields


class res_currency(orm.Model):
    _inherit = 'res.currency'

    _columns = {
        'full_name': fields.char('Full Amount Name', size=64, translate=True, help='Name that can be used in amount said.'),
        'fraction_name': fields.char('Fraction Name', size=64, translate=True, help='Name of fractional values (e.g. cents) that can be used in amount said.'),
        'display_fraction': fields.boolean('Always Display Fraction', help='If checked, fractional values is to be displayed in amount said even if the value is 0.0'),
    }
