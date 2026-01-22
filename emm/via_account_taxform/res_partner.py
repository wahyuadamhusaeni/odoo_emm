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

from osv import orm, fields
from tools.translate import _


class res_partner(orm.Model):
    _inherit = 'res.partner'

    def _validate_npwp(self, cr, uid, partner_info, context=None):
        _npwp_param = self.pool.get('ir.model.data').get_object(cr, uid, 'via_account_taxform', 'partner_parameter_taxform', context=context)
        _npwp_param = _npwp_param and _npwp_param.code or ''
        _npwp_found = True  # If no validation required make it as if validation passed
        _partinfo_obj = self.pool.get('partner.info')

        assert _npwp_param, _('Partner Parameter for NPWP is not defined!  Contact your administrator.')

        _npwp_found = False
        for _info in partner_info:
            _param = False
            if _info[0] in [0, 1]:
                # Take from the fields
                _param = _info[-1].get('parameter_id', False)

            if _info[0] in [1, 4] and not _param:
                # Take from the browse_object, for 1, it may be that parameter_id is not to be saved
                _param = _info[1] and _partinfo_obj.browse(cr, uid, _info[1], context=context) or False
                _param = _param and _param.parameter_id or ''
            elif _info[0] in [6]:
                # Mass addition
                _params = _info[2] and _partinfo_obj.browse(cr, uid, _info[2], context=context) or []
                _param = False
                for x in _params:
                    if x.code == _npwp_param:
                        _param = _npwp_param
            else:
                # Removals, to be ignored: 2, 3, 5
                # Or 0 without parameter_id, which is erroneous
                pass

            _npwp_found = _npwp_found or (_param == _npwp_param)
            if _npwp_found:
                break

        return _npwp_found

    def onchange_partner_is_company(self, cr, uid, ids, is_company, partner_info, context=None):
        res = self.onchange_type(cr, uid, ids, is_company, context=context)
        _npwp_found = True  # If no validation required make it as if validation passed
        if is_company:
            _npwp_found = self._validate_npwp(cr, uid, partner_info, context=context)

        if not _npwp_found:
            res.update({'warning': {
                'title': _('Warning'),
                'message': _('Partner that Is a Company may require NPWP information to create Taxform.  This Partner has not been provided with such information.'),
            }})
        return res

    def onchange_partner_type(self, cr, uid, ids, type, partner_info, context=None):
        res = {}
        _npwp_found = True  # If no validation required make it as if validation passed
        if (type in ['default', 'invoice']):
            _npwp_found = self._validate_npwp(cr, uid, partner_info, context=context)

        if not _npwp_found:
            res.update({'warning': {
                'title': _('Warning'),
                'message': _('Partner of type Default or Invoice may require NPWP to create Taxform.  This Partner has not been provided with such information.'),
            }})
        return res

res_partner()
