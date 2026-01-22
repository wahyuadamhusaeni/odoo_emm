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
from tools.translate import _


class via_prorate_discount(orm.TransientModel):
    _name = "via.prorate.discount"
    _description = 'Prorate global discount to all purchase order line items'
    """
    Prorate a global discount to all line items of the selected purchase order
    """

    def view_init(self, cr, uid, fields_list, context=None):
        _po = self.pool.get('purchase.order').browse(cr, uid, context.get('active_id'), context=context)
        if (len(context.get('active_ids')) != 1) or (_po.state not in ['draft']):
            raise orm.except_orm(_('Error !'), _('You can only Prorate Discount for 1 Request for Quotation.'))
        super(via_prorate_discount, self).view_init(cr, uid, fields_list, context=None)

    def do_apply_discount(self, cr, uid, ids, context=None):
        _po = self.pool.get('purchase.order').browse(cr, uid, context.get('active_id'), context=context)
        if _po:
            datas = self.read(cr, uid, ids, [], context=context)[0]
            _disc_percent = datas['discount_amount']
            if datas['discount_type'] == 'amount':
                # Change the fixed amount discount to percentage by way of
                # dividing it with untaxed total amount of the PO
                _disc_percent = _disc_percent * 100 / _po.amount_untaxed

            _po_line_pool = self.pool.get('purchase.order.line')
            for line in _po.order_line:
                _po_line_pool.write(cr, uid, [line.id], {'price_unit': line.price_unit * (100.0 - _disc_percent) / 100.0}, context=context)

        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'discount_amount': fields.float('Discount', digits=(16, 2), required=True),
        'discount_type': fields.selection([('percent', 'Percentage (%)'), ('amount', 'Fixed Amount')], 'Type', required=True,
                help='Use \'Percentage\' to apply discount in %. \
                    \nUse \'Fixed Amount\' to apply discount in the fixed monetary amount.'),
    }

    _defaults = {
        'discount_amount': lambda *a: 0.0,
        'discount_type': lambda *a: 'percent',
    }

via_prorate_discount()
