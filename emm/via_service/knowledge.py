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


class document_page(orm.Model):
    _inherit = 'document.page'

    _columns = {
        'sr_skill_set': fields.many2many('service.request.skill.set', 'document_page_service_request_skill_set_rel', 'document_page_id', 'service_request_skill_set_id', 'Skill Set'),
        'attachment': fields.many2many('ir.attachment', 'document_page_ir_attachments_rel', 'document_page_id', 'attachment_id', 'Attachments'),
    }

document_page()
