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

from web.controllers.main import Binary
from web import http
openerpweb = http
import os


class Binary(Binary):

    def placeholder(self, req, image='placeholder.png'):
        if image in ['logo.png', 'nologo.png']:
            addons_path = openerpweb.addons_manifest['via_web']['addons_path']
            return open(os.path.join(addons_path, 'via_web', 'static', 'src', 'img', image), 'rb').read()
        else:
            return super(Binary, self).placeholder(req, image=image)
