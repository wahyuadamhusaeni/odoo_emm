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

from openerp.tools.translate import _
from osv import orm


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    def print_service_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()

        for invoice in self.browse(cr, uid, ids, context=context):
            try:
                _template = self.pool.get('ir.model.data').get_object(cr, uid, 'client_forms', 'client_form_faktur_id', context=context)

                _template = _template and _template.act_report_id and self.pool.get('ir.actions.report.xml').copy_data(cr, uid, _template.act_report_id.id, context=context) or False

                _datas = {
                    'ids': [invoice.id],
                }
                _template.update({'datas': _datas, 'context': ctx})
                return _template
            except:
                raise orm.except_orm(_('Error !'), _('Cannot load form. Please contact your administrator'))

account_invoice()
