#!/bin/bash
/srv/apps/odoo/odoo/openerp-server --config=/srv/apps//odoo/Setup/odoo_prod.conf --addons-path=/srv/apps/odoo/odoo/addons,/srv/apps//odoo/emm --logfile=/var/log/odoo/odoo.log --load=web
