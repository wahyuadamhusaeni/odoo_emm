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

import netsvc
from osv import fields, orm


class account_taxform_reusable_sequences(orm.Model):
    _name = "account.taxform.reusable.sequences"
    _description = "Tax Form Reusable Sequences"
    logger = netsvc.Logger()
    _rec_name = "taxform_sequence"

    _columns = {
        'legal_id': fields.many2one('res.company', 'Legal Entity', required=True),
        'taxform_sequence': fields.char('Taxform Sequence Number', size=32, required=True, select=True),
        'reusable': fields.boolean('Reusable', readonly=True),
    }

    _defaults = {
        'reusable': lambda *a: True,
    }

account_taxform_reusable_sequences()
