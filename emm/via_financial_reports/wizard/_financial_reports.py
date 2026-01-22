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

try:
    import release
    import pooler
    from osv import osv, fields
    from tools.translate import _
    from via_jasper_report_utils_account import framework
    from via_jasper_report_utils_account.framework import register_report_wizard, dt  # wizard
except ImportError:
    import openerp
    from openerp import release
    from openerp import pooler
    from openerp.osv import osv, fields
    from openerp.tools.translate import _
    from openerp.addons.via_jasper_report_utils_account import framework
    from openerp.addons.via_jasper_report_utils_account.framework import register_report_wizard, dt  # wizard

from datetime import date
import math


class wizard(framework.wizard):

    @staticmethod
    def default_from_dt(cr, uid, ids, fiscalyear_id, context=None):
        if fiscalyear_id:
            fy_pool = pooler.get_pool(cr.dbname).get('account.fiscalyear')
            fy = fy_pool.browse(cr, uid, fiscalyear_id, context=context)
            return fy.date_start
        else:
            return str(date.today())

    @staticmethod
    def default_to_dt(cr, uid, ids, fiscalyear_id, context=None):
        if fiscalyear_id:
            fy_pool = pooler.get_pool(cr.dbname).get('account.fiscalyear')
            fy = fy_pool.browse(cr, uid, fiscalyear_id, context=context)
            return str(min(dt(fy.date_stop), date.today()))
        else:
            return str(date.today())

    @staticmethod
    def default_from_period_id(cr, uid, ids, fiscalyear_id, context=None):
        if fiscalyear_id:
            fy_pool = pooler.get_pool(cr.dbname).get('account.fiscalyear')
            fy = fy_pool.browse(cr, uid, fiscalyear_id, context=context)
            return fy.period_ids[0].id
        else:
            return False

    @staticmethod
    def default_to_period_id(cr, uid, ids, fiscalyear_id, context=None):
        if fiscalyear_id:
            fy_pool = pooler.get_pool(cr.dbname).get('account.fiscalyear')
            fy = fy_pool.browse(cr, uid, fiscalyear_id, context=context)
            stop_date = min(dt(fy.date_stop), date.today())

            p_pool = pooler.get_pool(cr.dbname).get('account.period')
            p_ids = p_pool.search(cr, uid, [('fiscalyear_id', '=', fiscalyear_id),
                                            ('date_start', '<=', stop_date),
                                            ('date_stop', '>=', stop_date)], context=context)
            return p_ids[0]
        else:
            return False

    def onchange_company_id(cr, uid, ids, com_id, display_comparison, context=None):
        form_pool = pooler.get_pool(cr.dbname).get('via.jasper.report')
        return {
            'value': {
                'fiscalyear_id': (com_id
                                  and form_pool.default_fiscalyear_id(cr, uid,
                                                                      company_id=com_id,
                                                                      context=context)),
                'date_filter': 'filter_no',
                'from_dt': False,
                'to_dt': False,
                'from_period_id': False,
                'to_period_id': False,

                'fiscalyear_id_2': (com_id
                                    and display_comparison
                                    and form_pool.default_fiscalyear_id(cr, uid,
                                                                        company_id=com_id,
                                                                        context=context)),
                'date_filter_2': 'filter_no',
                'from_dt_2': False,
                'to_dt_2': False,
                'from_period_id_2': False,
                'to_period_id_2': False,

                'reporting_tree_id': False,
                'acc_ids': False,
                'journal_ids': False,
            },
        }

    @staticmethod
    def onchange_fiscalyear_id_common(cr, uid, ids, fiscalyear_id, field_suffix='', context=None):
        return {
            'value': {
                'date_filter' + field_suffix: 'filter_no',
                'from_dt' + field_suffix: False,
                'to_dt' + field_suffix: False,
                'from_period_id' + field_suffix: False,
                'to_period_id' + field_suffix: False,
            },
        }

    def onchange_fiscalyear_id(cr, uid, ids, fiscalyear_id, field_suffix='', context=None):
        return wizard.onchange_fiscalyear_id_common(cr, uid, ids, fiscalyear_id, context=context)

    def onchange_fiscalyear_id_2(cr, uid, ids, fiscalyear_id_2, context=None):
        return wizard.onchange_fiscalyear_id_common(cr, uid, ids,
                                                    fiscalyear_id_2, field_suffix='_2',
                                                    context=context)

    @staticmethod
    def onchange_date_filter_common(cr, uid, ids, date_filter, fiscalyear_id, field_suffix='', context=None):
        if date_filter == 'filter_date':
            return {
                'value': {
                    'from_dt' + field_suffix: wizard.default_from_dt(cr, uid, ids, fiscalyear_id, context=context),
                    'to_dt' + field_suffix: wizard.default_to_dt(cr, uid, ids, fiscalyear_id, context=context),
                    'from_period_id' + field_suffix: False,
                    'to_period_id' + field_suffix: False,
                },
            }
        elif date_filter == 'filter_period':
            return {
                'value': {
                    'from_dt' + field_suffix: False,
                    'to_dt' + field_suffix: False,
                    'from_period_id' + field_suffix: wizard.default_from_period_id(cr, uid, ids, fiscalyear_id, context=context),
                    'to_period_id' + field_suffix: wizard.default_to_period_id(cr, uid, ids, fiscalyear_id, context=context),
                },
            }
        else:
            return {
                'value': {
                    'from_dt' + field_suffix: False,
                    'to_dt' + field_suffix: False,
                    'from_period_id' + field_suffix: False,
                    'to_period_id' + field_suffix: False,
                },
            }

    def onchange_date_filter(cr, uid, ids, date_filter, fiscalyear_id, field_suffix='', context=None):
        return wizard.onchange_date_filter_common(cr, uid, ids, date_filter,
                                                  fiscalyear_id, context=context)

    def onchange_date_filter_2(cr, uid, ids, date_filter_2, fiscalyear_id_2, context=None):
        return wizard.onchange_date_filter_common(cr, uid, ids, date_filter_2,
                                                  fiscalyear_id_2, field_suffix='_2',
                                                  context=context)

    def onchange_display_comparison(cr, uid, ids, display_comparison, company_id, context=None):
        if display_comparison:
            form_pool = pooler.get_pool(cr.dbname).get('via.jasper.report')
            return {
                'value': {
                    'fiscalyear_id_2': (company_id
                                        and form_pool.default_fiscalyear_id(cr, uid,
                                                                            company_id=company_id,
                                                                            context=context)),
                    'date_filter_2': 'filter_no',
                },
            }
        else:
            return {
                'value': {
                    'fiscalyear_id_2': False,
                    'date_filter_2': False,
                    'from_dt_2': False,
                    'to_dt_2': False,
                    'from_period_id_2': False,
                    'to_period_id_2': False,
                },
            }

    _onchange = {
        'company_id': (onchange_company_id, 'company_id', 'display_comparison', 'context'),
        'fiscalyear_id': (onchange_fiscalyear_id, 'fiscalyear_id', 'context'),
        'fiscalyear_id_2': (onchange_fiscalyear_id_2, 'fiscalyear_id_2', 'context'),
        'date_filter': (onchange_date_filter, 'date_filter', 'fiscalyear_id', 'context'),
        'date_filter_2': (onchange_date_filter_2, 'date_filter_2', 'fiscalyear_id_2', 'context'),
        'display_comparison': (onchange_display_comparison, 'display_comparison', 'company_id', 'context'),
    }

    _required = [
        'company_id',
        'reporting_tree_id',
        'fiscalyear_id',
        'target_move',
        'date_filter',
        'as_of_dt',
    ]

    _attrs = {
        'first_notebook_3': "{'invisible': [('display_comparison', '=', False)]}",

        'display_large': "{'readonly': [('rpt_output', '!=', 'pdf')]}",

        'date_filter': "{'readonly': [('fiscalyear_id', '=', False)]}",

        'from_dt': ("{'invisible': [('date_filter', '!=', 'filter_date')], "
                    " 'required': [('date_filter', '=', 'filter_date')]}"),
        'to_dt': ("{'invisible': [('date_filter', '!=', 'filter_date')], "
                  " 'required': [('date_filter', '=', 'filter_date')]}"),

        'from_period_id': ("{'invisible': [('date_filter', '!=', 'filter_period')], "
                           " 'required': [('date_filter', '=', 'filter_period')]}"),
        'to_period_id': ("{'invisible': [('date_filter', '!=', 'filter_period')], "
                         " 'required': [('date_filter', '=', 'filter_period')]}"),

        'date_filter_2': ("{'required': [('display_comparison', '=', True)], "
                          " 'readonly': [('fiscalyear_id_2', '=', False)]}"),

        'fiscalyear_id_2': "{'required': [('display_comparison', '=', True)]}",

        'from_period_id_2': ("{'invisible': [('date_filter_2', '!=', 'filter_period')], "
                             " 'required': [('date_filter_2', '=', 'filter_period')]}"),
        'to_period_id_2': ("{'invisible': [('date_filter_2', '!=', 'filter_period')], "
                           " 'required': [('date_filter_2', '=', 'filter_period')]}"),

        'from_dt_2': ("{'invisible': [('date_filter_2', '!=', 'filter_date')], "
                      " 'required': [('date_filter_2', '=', 'filter_date')]}"),
        'to_dt_2': ("{'invisible': [('date_filter_2', '!=', 'filter_date')], "
                    " 'required': [('date_filter_2', '=', 'filter_date')]}"),
    }

    _domain = {
        'reporting_tree_id': "[('company_id', '=', company_id), ('tree_type_name', '=', 'Financial Report')]",
        'acc_ids': "[('company_id', 'child_of', [company_id])]",
        'journal_ids': "[('company_id', 'child_of', [company_id])]",

        'fiscalyear_id': "[('company_id', '=', company_id)]",
        'from_period_id': "[('fiscalyear_id', '=', fiscalyear_id)]",
        'to_period_id': "[('fiscalyear_id', '=', fiscalyear_id)]",

        'fiscalyear_id_2': "[('company_id', '=', company_id)]",
        'from_period_id_2': "[('fiscalyear_id', '=', fiscalyear_id_2)]",
        'to_period_id_2': "[('fiscalyear_id', '=', fiscalyear_id_2)]",
    }

    _label = {
    }

    # The values in the dictionary below must be callables with signature:
    #     lambda self, cr, uid, context
    _defaults = {
        'no_wrap': lambda self, cr, uid, context: True,
        'from_dt': lambda self, cr, uid, context: False,
        'to_dt': lambda self, cr, uid, context: False,
        'from_dt_2': lambda self, cr, uid, context: False,
        'to_dt_2': lambda self, cr, uid, context: False,
        'rpt_output': lambda self, cr, uid, context: 'xls',
        'acc_ids_empty_is_all': lambda self, cr, uid, context: True,
        'journal_ids_empty_is_all': lambda self, cr, uid, context: True,
    }

    # The following is to be used by column state. The entry must be tuple:
    #     (key, value)
    _states = [
    ]

    # The following is used to specify what columns should appear in a
    # one-to-many or many-to-many widget.  The key must be the field name while
    # the value must be a list of column names that should appear.
    _tree_columns = {
    }

    def _populate_form_company_ids(self, cr, uid, form, context=None):
        com_pool = self.pool.get('res.company')
        com_ids = com_pool.search(cr, uid, [('id', 'child_of', [form.company_id.id])],
                                  context=context)
        form.write({
            'company_ids': [(6, 0, com_ids)],
        }, context=context)
        return form.get_form(context=context)

    def _populate_form_dates_from_date_filter(self, cr, uid, form, field_suffix='', context=None):
        exec ('''
if form.date_filter%(field_suffix)s == 'filter_date':
    pass
elif form.date_filter%(field_suffix)s == 'filter_period':
    form.write({
        'from_dt%(field_suffix)s': form.from_period_id%(field_suffix)s.date_start,
        'to_dt%(field_suffix)s': form.to_period_id%(field_suffix)s.date_stop,
    }, context=context)
else:
    form.write({
        'from_dt%(field_suffix)s': form.fiscalyear_id%(field_suffix)s.period_ids[0].date_start,
        'to_dt%(field_suffix)s': form.fiscalyear_id%(field_suffix)s.period_ids[-1].date_stop,
    }, context=context)''' % {'field_suffix': field_suffix})
        return form.get_form(context=context)

    def _marshall_gain_or_loss_acc_id(self, cr, uid, form, context=None):
        if form.company_id.exchange_gain_loss_account:
            gain_or_loss_acc_id = form.company_id.exchange_gain_loss_account.id
        else:
            raise osv.except_osv(_('Caution !'),
                                 _('Cannot print without currency exchange gain/loss account configured in the company !'))

        form.add_marshalled_data('GAIN_OR_LOSS_ACC_ID', gain_or_loss_acc_id)

    def _marshall_journal_simulation_clause(self, cr, uid, form, context=None):
        journal_simulation_clause = ''
        journal_simulation_crit = [('model', '=', 'account.journal'),
                                   ('name', '=', 'state')]
        if self.pool.get('ir.model.fields').search(cr, uid,
                                                   journal_simulation_crit,
                                                   context=context):
            journal_simulation_clause = "AND aj.state = 'valid'"

        form.add_marshalled_data('JOURNAL_SIMULATION_CLAUSE',
                                 journal_simulation_clause)

    def _marshall_company_decimal_rounding(self, cr, uid, form, context=None):
        precision = '0' * int(math.log(1.0 / form.company_id.currency_id.rounding, 10))
        if len(precision) > 0:
            precision = '.' + precision

        format_string = (r'#,##0%(precision)s;-#,##0%(precision)s'
                         % {'precision': precision})
        form.add_marshalled_data('DECIMAL_FORMAT_STRING_AMOUNT', format_string)

    def validate_date_filter_parameters(self, cr, uid, form, field_suffix='', filter_section='', context=None):
        exec ('''
if form.date_filter%(field_suffix)s == 'filter_date':
    active_filter = 'Date'
elif form.date_filter%(field_suffix)s == 'filter_period':
    active_filter = 'Period'
else:
    active_filter = 'Internal'

if dt(form.from_dt%(field_suffix)s) < dt(form.fiscalyear_id%(field_suffix)s.date_start):
    raise osv.except_osv(_('Error !'),
                         _('%(filter_section)s %%s filter "From" is outside the fiscal year !')
                         %% active_filter)
if dt(form.to_dt%(field_suffix)s) > dt(form.fiscalyear_id%(field_suffix)s.date_stop):
    raise osv.except_osv(_('Error !'),
                         _('%(filter_section)s %%s filter "To" is outside the fiscal year !')
                         %% active_filter)''' % {
            'field_suffix': field_suffix,
            'filter_section': filter_section,
        })

    def validate_parameters(self, cr, uid, form, context=None):
        self.validate_date_filter_parameters(cr, uid, form, context=context)
        if form.display_comparison:
            self.validate_date_filter_parameters(cr, uid, form,
                                                 field_suffix='_2',
                                                 filter_section='Comparison',
                                                 context=context)

    def print_report(self, cr, uid, form, context=None):
        form = self._populate_form_company_ids(cr, uid, form, context=context)
        form = self._populate_form_dates_from_date_filter(cr, uid, form,
                                                          context=context)
        if form.display_comparison:
            form = self._populate_form_dates_from_date_filter(cr, uid, form,
                                                              field_suffix='_2',
                                                              context=context)

        self.validate_parameters(cr, uid, form, context=context)

        self._marshall_gain_or_loss_acc_id(cr, uid, form, context=context)

        self._marshall_journal_simulation_clause(cr, uid, form, context=context)

        self._marshall_company_decimal_rounding(cr, uid, form, context=context)

        # As demonstrated by the following snippet code, this method can return
        # another report name to be rendered. For example, three report names
        # are registered with the OERP reporting service: RPT_NAME, RPT_NAME +
        # '(By Value)', and RPT_NAME + ' (By Quantity)'. Only RPT_NAME has no
        # report file registered but the name needs to be registered to create
        # the reporting action. Therefore, a real report name needs to be
        # returned by this method. Usually a report is selected in this way
        # because the logic of an available report is orthogonal to the other
        # available reports. Override method get_service_name_filter below to
        # select a report because of layout differences like paper size and
        # orientation.
        #
        # if form.rpt_type == 'val':
        #    return RPT_NAME + ' (By Value)'
        # else:
        #    return RPT_NAME + ' (By Quantity)'
