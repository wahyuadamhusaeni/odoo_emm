# -*- encoding: utf-8 -*-
##############################################################################
#
#    Vikasa Infinity Anugrah, PT
#    Copyright (c) 2011 - 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

from osv import osv, fields
import logging
from via_jasper_report_utils.framework import register_report_wizard, wizard


class qcf(osv.osv_memory):
    _name = 'qcf'
    _description = 'User supplier selection when generating quotation report'
    logger = logging.getLogger('qcf')
    _columns = {
        'user_id': fields.many2one('res.users', 'User',
                                   ondelete='cascade', required=True,
                                   readonly=True),
        'pr_id': fields.many2one('purchase.requisition', 'PR',
                                 ondelete='cascade', required=True,
                                 readonly=True),
        'supplier_id': fields.many2one('res.partner', 'Supplier',
                                       ondelete='cascade', required=True,
                                       readonly=True),
        'po_id': fields.many2one('purchase.order', 'Order Reference',
                                 ondelete='cascade', required=True,
                                 readonly=True),
    }

    def cleanup_list(self, cr, uid, context):
        ids = self.search(cr, uid, [('user_id', '=', uid)], context=context)
        if ids:
            self.unlink(cr, uid, ids, context=context)

    def update_list(self, cr, uid, context):
        _rpt_name = context.get('via_jasper_report_utils.rpt_name', '')
        _active_ids = context.get('active_ids', '')
        if (_rpt_name != 'Quotation Comparison'):  # or isinstance(_active_ids, list)):
            return

        self.cleanup_list(cr, uid, context)

        sql = '''
SELECT DISTINCT
 prl.requisition_id,
 supplier.id,
 po.id,
 supplier.name,
 po.name
FROM
 purchase_requisition_line AS prl
 INNER JOIN product_product AS prod
  ON prl.product_id = prod.id
 INNER JOIN purchase_order_line AS pol
  ON (prl.product_id,
      prl.product_qty,
      -- pol.notes can never be NULL because at the minimum it has: ' - '
      trim(both ' ' from COALESCE(prl.notes, ''))) = (pol.product_id,
                                                      pol.product_qty,
                                                      substring(pol.notes for char_length(trim(both ' ' from COALESCE(prl.notes, '')))))
 INNER JOIN purchase_order AS po
  ON (po.id,
      po.requisition_id) = (pol.order_id,
                            prl.requisition_id)
 INNER JOIN product_template AS prod_template
  ON prod.product_tmpl_id = prod_template.id
 INNER JOIN res_partner AS supplier
  ON po.partner_id = supplier.id
WHERE
 prl.requisition_id IN (%s)
ORDER BY
 prl.requisition_id,
 supplier.name,
 po.name
'''
        cr.execute(sql % ','.join(map(lambda id: str(id), _active_ids)))
        if cr.rowcount >= 1:
            res = cr.fetchall()
        else:
            return

        for record in res:
            _vals = {
                'user_id': uid,
                'pr_id': record[0],
                'supplier_id': record[1],
                'po_id': record[2],
            }
            self.create(cr, uid, _vals, context=context)

qcf()

RPT_NAME = 'Quotation Comparison'

class via_jasper_report(osv.osv_memory):
    _inherit = "via.jasper.report"

    def get_qcf_ids(self, cr, uid, context=None):
        pool = self.pool.get('qcf')
        pool.update_list(cr, uid, context)
        return pool.search(cr, uid, [('user_id', '=', uid)], context=context)

    _columns = {
        'qcf_ids': fields.many2many('qcf', 'via_report_qcf_rel',
                                    'via_report_id', 'qcf_id', 'Suppliers'),
    }

    _defaults = {
        'qcf_ids': get_qcf_ids,
    }

via_jasper_report()


class wizard(wizard):
    _visibility = ['qcf_ids']

    def print_report(self, cr, uid, form, context=None):
        pr_ids = {}
        for record in form.qcf_ids:
            supplier_ids = pr_ids.setdefault(record.pr_id.id, [])
            supplier_ids.append((record.supplier_id.id, record.po_id.id))

        res = ''
        for k, v in pr_ids.iteritems():
            res += str(k) + ': ' + ','.join(map(lambda x: '(%s,%s)' % (str(x[0]), str(x[1])), v)) + '\n'

        self.pool.get('qcf').cleanup_list(cr, uid, context)  # Memory clean-up

        form.add_marshalled_data('QCF_SELECTED_PRS_SUPPLIERS', res)
    
register_report_wizard(RPT_NAME, wizard)
