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


class res_company(orm.Model):
    _inherit = 'res.company'

    _columns = {
        'hit': fields.integer('No of Matches Shown'),
        'limit': fields.integer('No of Employee Shown'),
        'auto_create_skill_set': fields.boolean('Auto Create Skill Set'),
        'spare_parts_location': fields.many2one('stock.location', 'Spare Parts Warehouse Location', domain=[('usage_type', '=', 'spareparts')]),
        'pickup_location': fields.many2one('stock.location', 'Default Pickup Location', domain=[('usage_type', '=', 'pickup')]),
        'transit_location': fields.many2one('stock.location', 'Spare Parts Transit Location', domain=[('usage_type', '=', 'transit')]),
        'hr_employee_category': fields.many2many('hr.employee.category', 'res_company_hr_employee_category_rel', 'res_company_id', 'hr_employee_category_id', 'HR Employee Tags'),
        'additional_service_fee': fields.many2one('product.product', 'Default Additional Service Fee', domain=[('type', '=', 'service')]),
    }

    _defaults = {
        'hit': 0,
        'limit': 10,
    }

res_company()
