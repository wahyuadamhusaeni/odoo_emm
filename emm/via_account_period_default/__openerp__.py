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

{
    "name": "Account Period Default",
    "version": "1.1",
    "author": "Vikasa Infinity Anugrah, PT",
    "description": """
This module make period_id fields to be invisible in:
* Journal Entry (account.move) and Journal Item (account.move.line) and set when
  a new date is saved
* Invoices (account.invoice) to be invisible (and not set by default.
  The account move created will have period_id set according to the date_invoice)
* Vouchers (account.voucher) to be invisible (by default it has already set when
  the date field is changed)
* Refund wizards (account.invoice.refund) to be invisible (by default it will be set
  during the processing)
* Reconcile wizards (account.automatic.reconcile) to be invisible (by default it will
  be set during the processing)
* Tree Views of account.voucher, account.move, account.move.line, and account.invoice
    """,
    "website": "",
    "license": "GPL-3",
    "category": "Generic Modules/Accounting",
    "data": [
        'account_invoice_refund.xml',
    ],
    "depends": [
        "account_voucher",
    ],
    "init_xml": [],
    "demo_xml": [],
    "active": False,
    "installable": True,
}
