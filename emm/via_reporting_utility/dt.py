###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2011 - 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
#
###############################################################################

try:
    import release
    from osv import osv, fields
    import pooler
    import tools
except ImportError:
    import openerp
    from openerp import tools
    from openerp import release
    from openerp.osv import osv, fields
    from openerp import pooler

from datetime import datetime
from datetime import date

try:
    fields.date.context_today # Probing
    DATE_NOW = fields.date.context_today
    DEFAULT_DATE_NOW = DATE_NOW
except AttributeError:
    DATE_NOW = (lambda model, cr, uid, context=None, timestamp=None: str(date.today()))
    DEFAULT_DATE_NOW = DATE_NOW

DEFAULT_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

try:
    fields.datetime.context_timestamp # Probing
    DATETIME_NOW = (lambda cr, uid, timestamp=None, context=None: fields.datetime.context_timestamp(cr,
                                                                                                    uid,
                                                                                                    (timestamp
                                                                                                     and (isinstance(timestamp, basestring)
                                                                                                          and datetime.strptime(timestamp,
                                                                                                                                DEFAULT_DATETIME_FORMAT)
                                                                                                          or timestamp)
                                                                                                     or datetime.now()),
                                                                                                    context=context))
    DEFAULT_DATETIME_NOW = fields.datetime.now
except AttributeError:
    DATETIME_NOW = (lambda cr, uid, timestamp=None, context=None: str(timestamp
                                                                      and (isinstance(timestamp, basestring)
                                                                           and datetime.strptime(timestamp,
                                                                                                 DEFAULT_DATETIME_FORMAT)
                                                                           or timestamp)
                                                                      or datetime.now()))
    DEFAULT_DATETIME_NOW = (lambda *args: str(datetime.now()))
