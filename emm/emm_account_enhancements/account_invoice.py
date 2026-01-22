# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
#    Copyright (c) 2011 - 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

from lxml import etree

from osv import orm, fields
from tools.translate import _


class account_invoice(orm.Model):
    _inherit = "account.invoice"

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(account_invoice, self).fields_view_get(cr, user, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        _arch = res.get('arch', '')

        doc = etree.XML(_arch)
        nodes = doc.xpath("//field[@name='partner_id']")
        for node in nodes:
            _orig_domain = node.get('domain', '[]').strip()
            if _orig_domain[-1] == ']':
                _orig_domain = _orig_domain[:-1]
                if _orig_domain[-1] == ')':
                    _orig_domain += ", "
                _orig_domain += "'|', ('is_company', '=', True), ('type', 'in', ['default', 'invoice'])]"

                node.set('domain', _orig_domain)
        res['arch'] = etree.tostring(doc)
        return res
