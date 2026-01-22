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

MODULE_NAME = 'via_jasper_report_utils'
VIEW_NAME = 'via_jasper_report_main_form_view'

try:
    import release
    import pooler
    from osv import osv, fields, orm
    if release.major_version == '6.1':
        import openerp.modules as addons
    else:
        import addons
    from via_jasper_report_utils import utility
    from tools.translate import _
    from tools import DEFAULT_SERVER_DATE_FORMAT
    # SUPERUSER_ID is only defined from OpenERP 6.1 onwards
    SUPERUSER_ID = 1
except ImportError:
    import openerp
    from openerp import release
    from openerp import pooler
    from openerp.osv import osv, fields, orm
    import openerp.modules as addons
    from openerp.addons.via_jasper_report_utils import utility
    from openerp.tools.translate import _
    from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
    from openerp import SUPERUSER_ID

from functools import wraps
import calendar
from lxml import etree
import os
import glob
from datetime import date
from datetime import datetime
from copy import deepcopy
from via_reporting_utility.pgsql import list_to_pgTable
from via_base_enhancements.tools import prep_dict_for_write

_marshalled_data_registry = {}
_report_wizard_registry = {}
_current_domain_registry = {}


def normalize_rpt_name(rpt_name):
    return ''.join(map(lambda c: c.lower(),
                       filter(lambda c: c.isalpha(),
                              rpt_name)))


def register_report_wizard(rpt_name, wizard_class):
    normalized_rpt_name = normalize_rpt_name(rpt_name)
    if normalized_rpt_name in _report_wizard_registry:
        raise Exception('Report "%s" already registered its wizard'
                        % normalized_rpt_name)
    _report_wizard_registry.update({normalized_rpt_name: wizard_class})


class wizard(object):
    _onchange = {}
    _visibility = []
    _required = ['rpt_output']
    _readonly = []
    _attrs = {}
    _domain = {
        'from_period_id': "[('fiscalyear_id','=',fiscalyear_id)]",
        'to_period_id': "[('fiscalyear_id','=',fiscalyear_id)]",
        'prod_ids': "[('product_tmpl_id.company_id','=',False)]",
        'prod_ids_2': "[('product_tmpl_id.company_id','=',False)]",
        'salesman_ids': "[('company_id','=',False)]",
        'customer_ids': "[('company_id','=',False),('customer','=',True)]",
    }
    if float(release.major_version) < 7.0:
        _domain.update({
            'customer_addr_ids': "[('company_id','=',False),('partner_id.customer','=',True)]",
        })

    _label = {}

    _defaults = {}

    _selections = {}

    _tree_columns = {
        'company_ids': ['name'],
        'prod_ids': ['default_code', 'name_template'],
        'prod_ids_2': ['default_code', 'name_template'],
        'salesman_ids': ['name'],
        'customer_ids': ['name'],
    }
    if float(release.major_version) < 7.0:
        _tree_columns.update({
            'customer_addr_ids': ['partner_id', 'state_id'],
        })

    def __init__(self, cr):
        self.pool = pooler.get_pool(cr.dbname)

    def get_service_name_filter(self, cr, uid, form, context=None):
        return (lambda service_names, ctx: service_names, context)


class OerpViewArch(object):
    # Currently no row span is handled
    def __init__(self, rows, string=None, name=None):
        self.string = string
        self.name = name
        self._count_col(rows)
        if isinstance(rows[-1], dict):
            self._rows = rows[:-1]
            self._resolve_references(rows[-1])
        else:
            self._rows = rows

    def _resolve_references(self, references):

        def _resolve_notebook(name, val):
            res = []
            for (idx, entry) in enumerate(val):
                res.append(OerpViewArch(entry[1],
                                        string=entry[0],
                                        name='%s_%d' % (name, idx)))
            return res

        reference_keys = [('notebook:', _resolve_notebook)]

        for ref, val in references.iteritems():
            for (ref_key, resolve) in reference_keys:
                if ref.find(ref_key) == 0:
                    res = resolve(ref[len(ref_key):], val)
                    self.__setattr__(ref[len(ref_key):], res)
                    return
            raise Exception('Unknown view references "%s"' % ref)

    def arch(self, parent_element=None):
        if parent_element is None:
            self._arch = etree.Element('form',
                                       col=self._int(self._col_count),
                                       string=(self.string or ''))
        else:
            self._arch = parent_element

        for row in self._rows:
            self._create_row(row, self._col_count)

        return self._arch

    def _count_col(self, rows):
        for row in rows:
            if not isinstance(row, list):
                self._col_count = max(getattr(self, '_col_count', 0), 2)
            else:
                self._count_col_in_a_row(row)

    def _count_col_in_a_row(self, row):
        col_count = 0
        for col in row:
            if not isinstance(col, list):
                col_count += 1
            else:
                pass  # No row span is handled for now
        self._col_count = max(getattr(self, '_col_count', 0), col_count)

    def _create_row(self, row, colspan):
        if not isinstance(row, list):
            self._create_element(row, 1, colspan)
        else:
            self._create_col(row, 1)
            self._create_element('newline', 1, colspan)

    def _create_col(self, row, rowspan):
        for col in row:
            if not isinstance(col, list):
                self._create_element(col, rowspan, 1)
            else:
                pass  # No row span is handled for now

    def _int(self, colspan):
        return '%d' % (colspan * 2)

    def _create_element(self, name, rowspan, colspan):
        if name is None:
            etree.SubElement(self._arch, 'label',
                             colspan=self._int(colspan))
        elif name == 'newline':
            etree.SubElement(self._arch, 'newline')
        elif name.find('notebook:') == 0:
            notebook = etree.SubElement(self._arch, 'notebook',
                                        colspan=self._int(colspan))
            for spec in getattr(self, name[len('notebook:'):]):
                page = etree.SubElement(notebook, 'page',
                                        string=spec.string,
                                        name=spec.name)
                container = etree.SubElement(page, 'group',
                                             col=self._int(spec._col_count))
                spec.arch(container)
        elif name.find('separator:') == 0:
            separator = etree.SubElement(self._arch, 'separator',
                                         colspan=self._int(colspan),
                                         string=name[len('separator:'):])
        else:
            etree.SubElement(self._arch, 'field',
                             name=name,
                             colspan=self._int(colspan))


def dt(date_string):
    return datetime.strptime(date_string, DEFAULT_SERVER_DATE_FORMAT).date()


class via_jasper_report(osv.osv_memory):
    _name = "via.jasper.report"
    _description = 'Standard VIA wizard for generating Jasper Reports'

    _jasper_report_indicator = 'jasper_report = True'
    _report_table = 'ir_act_report_xml'

    @staticmethod
    def wizard_onchange(f):
        @wraps(f)
        def wrapper(cr, uid, ids, *args, **kwargs):
            res = f(cr, uid, ids, *args, **kwargs)
            dom_dict = res.get('domain', {})
            _rptobj = pooler.get_pool(cr.dbname).get('via.jasper.report')
            _rptobj.set_current_domain(cr, uid, ids, dom_dict, **kwargs)
            return res

        return wrapper

    def __getattribute__(self, name):
        if name.find('onchange_') == 0:
            normalized_rpt_name, field_name = name.split('_', 2)[1:]
            return _report_wizard_registry[normalized_rpt_name]._onchange[field_name][0]
        return super(via_jasper_report, self).__getattribute__(name)

    def tree_columns_create_view(self, cr, uid, field, rpt_name, tree_columns):
        uid = SUPERUSER_ID  # Creating a tree view is an internal logic that should work for everyone
        xml_id = self.tree_column_xml_id(field, rpt_name)
        model = self._columns[field]._obj

        self.tree_columns_delete_view(cr, uid, field, rpt_name)

        imd_pool = self.pool.get('ir.model.data')

        model_pool = self.pool.get(model)
        model_tree_view = model_pool.fields_view_get(cr, uid,
                                                     view_type='tree')
        view_pool = self.pool.get('ir.ui.view')
        if len(view_pool.search(cr, uid, [('model', '=', model),
                                          ('type', '=', 'tree')])) == 0:
            # The model has no tree view yet, so create it to have a default fall
            # back view for any subsequent modification
            default_xml_id = xml_id + '_default'
            imd_pool._update(cr, uid, 'ir.ui.view', MODULE_NAME, {
                'name': default_xml_id,
                'model': model,
                'type': 'tree',
                'arch': model_tree_view['arch'],
            }, xml_id=default_xml_id, mode='update')

        if isinstance(tree_columns, basestring):
            tree_str = tree_columns
            custom_tree_columns = False
            tree_columns = []
        elif isinstance(tree_columns, tuple):
            tree_str = tree_columns[0]
            custom_tree_columns = True
            tree_columns = tree_columns[1]
        else:
            tree_str = etree.XML(model_tree_view['arch']).get('string', '')
            custom_tree_columns = True

        tree_field_names = {}
        for tree_field in etree.XML(model_tree_view['arch']).xpath('//field'):
            if 'modifiers' in tree_field.attrib:
                del tree_field.attrib['modifiers']
            tree_field_names[tree_field.get('name')] = tree_field

        tree_el = etree.Element('tree', string=tree_str)
        for col_name in tree_columns:
            etree.SubElement(tree_el, 'field', name=col_name)
            try:
                del tree_field_names[col_name]
            except KeyError:
                pass
        for tree_field_name, tree_field in tree_field_names.iteritems():
            if custom_tree_columns:
                etree.SubElement(tree_el, 'field', name=tree_field_name,
                                 invisible='1')
            else:
                tree_el.append(deepcopy(tree_field))

        arch = etree.tostring(tree_el, pretty_print=True)

        res_id = imd_pool._update(cr, uid, 'ir.ui.view', MODULE_NAME, {
            'name': xml_id,
            'model': model,
            'type': 'tree',
            'arch': arch,
        }, xml_id=xml_id, mode='update')

        return MODULE_NAME + '.' + xml_id

    def tree_column_xml_id(self, field, rpt_name):
        report_dir_name = ''.join(map(lambda c: c == ' ' and '_' or c.lower(),
                                      ' '.join(filter(lambda w: len(w) > 0,
                                                      filter(lambda c: c.isalnum() or c == ' ',
                                                             ''.join(map(lambda c: c.isalnum() and c or ' ',
                                                                         rpt_name))).split(' ')))))
        return (''.join(part[0] for part in report_dir_name.split('_'))
                + '_' + field + '_tree_columns')

    def tree_columns_delete_view(self, cr, uid, field, rpt_name):
        uid = SUPERUSER_ID  # Deleting a tree view is an internal logic that should work for everyone
        xml_id = self.tree_column_xml_id(field, rpt_name)

        imd_pool = self.pool.get('ir.model.data')
        imd_ids = imd_pool.search(cr, uid, [('name', '=', xml_id),
                                            ('module', '=', MODULE_NAME)])
        if len(imd_ids):
            imd_pool.unlink(cr, uid, imd_ids)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):

        if context is None:
            context = {}

        result = super(via_jasper_report, self).fields_view_get(cr, uid, view_id,
                                                                view_type, context=context,
                                                                toolbar=toolbar,
                                                                submenu=submenu)

        _report_name = context.get('via_jasper_report_utils.rpt_name', '')
        if not _report_name:
            return result

        normalized_rpt_name = normalize_rpt_name(_report_name)
        wizard_class = _report_wizard_registry[normalized_rpt_name]

        _arch = OerpViewArch(wizard_class._visibility,
                             string='VIA Jasper Report Wizard').arch()
        if not _arch.xpath('//field[@name="rpt_output"]'):
            etree.SubElement(_arch, 'field',
                             name='rpt_output', colspan=_arch.get('col'))

        if not _arch.xpath('//field[@name="id"]'):
            _field = etree.SubElement(_arch, 'field',
                             name='id', colspan=_arch.get('col'))
            _field.set('invisible', '1')

        _buttons = etree.SubElement(_arch, 'footer', name='wizard_buttons')

        kwargs = {
            'name': 'print_report',
            'type': 'object',
            'string': 'Print',
            'class': 'oe_highlight'
        }
        _button = etree.SubElement(_buttons, 'button', **kwargs)
        _button.tail = ' or '
        kwargs = {
            'special': 'cancel',
            'string': 'Cancel',
            'class': 'oe_link',
        }
        etree.SubElement(_buttons, 'button', **kwargs)

        for _field in _arch.xpath('//field'):
            field_name = _field.get('name')
            if field_name in (wizard._required + wizard_class._required):
                _field.set('required', '1')
            if field_name in wizard_class._readonly:
                _field.set('readonly', '1')
            if field_name in wizard_class._onchange:
                args = wizard_class._onchange[field_name][1:]
                _field.set('on_change',
                           'onchange_%s_%s(%s)'
                           % (normalized_rpt_name,
                              field_name,
                              ', '.join(args)))
            if field_name in wizard_class._attrs:
                _field.set('attrs', wizard_class._attrs[field_name])
            _domain = wizard._domain
            _domain.update(wizard_class._domain)
            if field_name in _domain:
                _field.set('domain', _domain[field_name])
            if field_name in wizard_class._label:
                _field.set('string', wizard_class._label[field_name])
            _tree_columns = wizard._tree_columns
            _tree_columns.update(wizard_class._tree_columns)
            if field_name in _tree_columns:
                tree_view_ref = self.tree_columns_create_view(cr, uid, field_name,
                                                              _report_name,
                                                              _tree_columns[field_name])
                _field.set('context', str({'tree_view_ref': tree_view_ref}))
            else:
                self.tree_columns_delete_view(cr, uid, field_name, _report_name)

        for _page in _arch.xpath('//page'):
            page_name = _page.get('name')

            if page_name in wizard_class._attrs:
                _page.set('attrs', wizard_class._attrs[page_name])

        if float(release.major_version) >= 6.1:
            for element in _arch.xpath('//*'):
                orm.setup_modifiers(element, context=context)

        result['arch'] = etree.tostring(_arch)
        return result

    def _get_year(self, cr, uid, context=None):
        return tuple([(year, year) for year in range(1970,
                                                     date.today().year + 1)])

    def _get_states(self, cr, uid, context=None):
        if context is None:
            context = {}
        rpt_name = context.get('via_jasper_report_utils.rpt_name', False)
        return rpt_name and getattr(_report_wizard_registry[normalize_rpt_name(rpt_name)],
                                    '_selections', {}).get('state', []) or []

    def _get_filter_selection(self, cr, uid, context=None):
        if context is None:
            context = {}
        rpt_name = context.get('via_jasper_report_utils.rpt_name', False)
        return rpt_name and getattr(_report_wizard_registry[normalize_rpt_name(rpt_name)],
                                    '_selections', {}).get('filter_selection', []) or []

    def _get_filter_selection_2(self, cr, uid, context=None):
        if context is None:
            context = {}
        rpt_name = context.get('via_jasper_report_utils.rpt_name', False)
        return rpt_name and getattr(_report_wizard_registry[normalize_rpt_name(rpt_name)],
                                    '_selections', {}).get('filter_selection_2', []) or []

    _months = [(1, 'January'), (2, 'February'), (3, 'March'),
               (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'),
               (8, 'August'), (9, 'September'), (10, 'October'),
               (11, 'November'), (12, 'December')]

    def orderby_get_ids(self, cr, uid, context=None):
        rpt_name = context.get('via_jasper_report_utils.rpt_name', '')
        return rpt_name and self.pool.get('via.report.orderby').orderby_get_ids(cr, uid, normalize_rpt_name(rpt_name), context=context) or []

    _columns = {
        'id': fields.integer("Instance", readonly=True),
        'rpt_name': fields.text("Report Name", readonly=True),
        'company_ids': fields.many2many('res.company', 'via_report_company_rel',
                                        'via_report_id', 'company_id', 'Companies'),
        'company_id': fields.many2one('res.company', 'Company'),
        'from_mo': fields.selection(_months, 'From'),
        'from_yr': fields.selection(_get_year, ''),
        'to_mo': fields.selection(_months, 'To'),
        'to_yr': fields.selection(_get_year, ''),
        'from_dt': fields.date('From'),
        'to_dt': fields.date('To'),
        'from_dt_2': fields.date('From'),
        'to_dt_2': fields.date('To'),
        'as_of_dt': fields.date('As of'),
        'as_of_yr': fields.selection(_get_year, 'As of Year'),
        'rpt_output': fields.selection(utility.get_outputs_selection, 'Output Format',
                                       required=True),
        'orderby_ids': fields.many2many('via.report.orderby', 'via_report_orderby_rel',
                                        'via_report_id', 'orderby_id', 'Order By'),
        'state': fields.selection(_get_states, 'State'),
        'prod_ids': fields.many2many('product.product',
                                     'via_report_product_rel',
                                     'via_report_id',
                                     'product_id',
                                     string='Products'),
        'prod_ids_empty_is_none': fields.boolean('Products When Empty Means None'),
        'prod_group_level': fields.integer('Product Grouping Level'),
        'prod_ids_2': fields.many2many('product.product',
                                       'via_report_product_rel_2',
                                       'via_report_id',
                                       'product_id',
                                       string='Products'),
        'prod_ids_2_empty_is_none': fields.boolean('Products When Empty Means None'),
        'no_zero': fields.boolean('No Zero'),
        'use_indentation': fields.boolean('Use Indentation'),
        'no_wrap': fields.boolean('No Wrap'),
        'display_large': fields.boolean('Large Format'),
        'reference_label': fields.char('Reference Label', size=128),
        'comparison_label': fields.char('Comparison Label', size=128),
        'display_comparison': fields.boolean('Enable Comparison'),
        'date_filter': fields.selection([('filter_no', 'No Filters'),
                                         ('filter_date', 'Date'),
                                         ('filter_period', 'Periods')], 'Filter By'),
        'date_filter_2': fields.selection([('filter_no', 'No Filters'),
                                           ('filter_date', 'Date'),
                                           ('filter_period', 'Periods')], 'Filter By'),
        'salesman_ids': fields.many2many('res.users',
                                         'via_report_salesman_rel',
                                         'via_report_id',
                                         'salesman_id',
                                         string='Salesman'),
        'customer_ids': fields.many2many('res.partner',
                                         'via_report_customer_rel',
                                         'via_report_id',
                                         'customer_id',
                                         string='Customers'),
        'filter_selection': fields.selection(_get_filter_selection,
                                             string='Filter By'),
        'filter_selection_2': fields.selection(_get_filter_selection_2,
                                               string='Filter By'),
        'customer_addr_ids': (float(release.major_version) < 7.0
                              and fields.many2many('res.partner.address',
                                                   'via_report_customer_addr_rel',
                                                   'via_report_id',
                                                   'customer_addr_id',
                                                   string='Customer Addresses')
                              or fields.function(lambda self, cr, uid, ids, field_names, args, context=None: dict.fromkeys(isinstance(ids, (int, long))
                                                                                                                           and [ids]
                                                                                                                           or ids, False),
                                                 type='boolean',
                                                 string='Customer Addresses')),
    }

    _defaults = {
        'rpt_name': lambda self, cr, uid, ctx: ctx.get('via_jasper_report_utils.rpt_name', None),
        'from_mo': lambda *a: date.today().month,
        'from_yr': lambda *a: date.today().year,
        'to_mo': lambda *a: date.today().month,
        'to_yr': lambda *a: date.today().year,
        'from_dt': fields.date.context_today,
        'to_dt': fields.date.context_today,
        'from_dt_2': fields.date.context_today,
        'to_dt_2': fields.date.context_today,
        'as_of_dt': fields.date.context_today,
        'as_of_yr': lambda *a: date.today().year,
        'rpt_output': 'pdf',
        'orderby_ids': orderby_get_ids,
        'company_id': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, uid, context=ctx).company_id.id,
        'company_ids': lambda self, cr, uid, ctx: [(6, False, [self.pool.get('res.users').browse(cr, uid, uid, context=ctx).company_id.id])],
        'prod_group_level': 1,
        'date_filter': 'filter_no',
    }

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(via_jasper_report, self).default_get(cr, uid, fields_list, context=context)

        rpt_name = context.get('via_jasper_report_utils.rpt_name', False)
        if rpt_name:
            rpt_defaults = getattr(_report_wizard_registry[normalize_rpt_name(rpt_name)], '_defaults', {})
            for field_name, field_default in rpt_defaults.iteritems():
                res[field_name] = field_default(self, cr, uid, context)

        return res

    # Related to prod_ids and prod_group_level
    def get_group_level_clause(self, cr, uid, ids, join_type='INNER', context=None):
        form = self.get_form(cr, uid, ids, context=context)
        level = form.prod_group_level
        res = (' %s JOIN product_category pc1\n'
               '  ON pc1.id = pt.categ_id\n' % join_type)
        for lvl in range(2, level + 1):
            res += (' %s JOIN product_category pc%d\n'
                    '  ON pc%d.id = pc%d.parent_id\n' % (join_type, lvl, lvl, lvl - 1))
        return res

    def get_prod_cat_ids(self, cr, uid, ids, level, prod_ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        prod_cat_pool = self.pool.get('product.category')
        sql_get_level_nodes = (' SELECT DISTINCT pp.name_template'
                               ' FROM product_product pp'
                               '  INNER JOIN product_template pt'
                               '   ON pp.product_tmpl_id = pt.id'
                               '  %s'
                               ' WHERE pp.id IN (%s)'
                               '  AND pc%d.id IS NULL')
        cr.execute(sql_get_level_nodes
                   % (form.get_group_level_clause(join_type='LEFT', context=context),
                      ','.join(str(prod_id)
                               for prod_id in prod_ids),
                      level))
        return [record[0] for record in cr.fetchall()]

    def get_prod_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.prod_ids) == 0:
            if form.prod_ids_empty_is_none:
                return []
            _default_domain = form.get_current_domain('prod_ids')
            crit = _default_domain or [('product_tmpl_id.company_id', 'in', [com_id.id for com_id in form.company_ids])]
            return self.pool.get('product.product').search(cr, uid,
                                                           crit,
                                                           context=context)
        else:
            return [prod_id.id for prod_id in form.prod_ids]

    def validate_prod_level(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if form.prod_group_level < 1:
            raise osv.except_osv(_('Error !'),
                                 _('Product Grouping Level must be at least 1 !'))

        prod_wrong_level = form.get_prod_cat_ids(form.prod_group_level,
                                                 form.get_prod_ids(context=context),
                                                 context=context)
        for prod_name in prod_wrong_level:
            raise osv.except_osv(_('Error !'),
                                 _('Product "%s" is not at Product Grouping Level !')
                                 % prod_name)
    # Related to prod_ids and prod_group_level [END]

    # Related to prod_ids_2
    def get_prod_ids_2(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.prod_ids_2) == 0:
            if form.prod_ids_2_empty_is_none:
                return []
            _default_domain = form.get_current_domain('prod_ids_2')
            crit = _default_domain or [('product_tmpl_id.company_id', 'in', [com_id.id for com_id in form.company_ids])]
            return self.pool.get('product.product').search(cr, uid,
                                                           crit,
                                                           context=context)
        else:
            return [prod_id_2.id for prod_id_2 in form.prod_ids_2]
    # Related to prod_ids_2 [END]

    # Related to salesman_ids
    def get_salesman_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.salesman_ids) == 0:
            _default_domain = form.get_current_domain('salesman_ids')
            crit = _default_domain or [('company_id', 'in', [com_id.id for com_id in form.company_ids])]
            return self.pool.get('res.users').search(cr, uid, crit,
                                                     context=context)
        else:
            return [salesman_id.id for salesman_id in form.salesman_ids]
    # Related to salesman_ids [END]

    # Related to customer_ids
    def get_customer_ids(self, cr, uid, ids, context=None):
        form = self.get_form(cr, uid, ids, context=context)

        if len(form.customer_ids) == 0:
            _default_domain = form.get_current_domain('customer_ids')
            crit = _default_domain or [('company_id', 'in', [com_id.id for com_id in form.company_ids]),
                    ('customer', '=', True)]
            return self.pool.get('res.partner').search(cr, uid,
                                                       crit,
                                                       context=context)
        else:
            return [customer_id.id for customer_id in form.customer_ids]
    # Related to customer_ids [END]

    if float(release.major_version) < 7.0:
        # Related to customer_addr_ids
        def get_customer_addr_ids(self, cr, uid, ids, context=None):
            form = self.get_form(cr, uid, ids, context=context)

            if len(form.customer_addr_ids) == 0:
                _default_domain = form.get_current_domain('customer_addr_ids')
                crit = _default_domain or [('company_id', 'in', [com_id.id for com_id in form.company_ids]),
                        ('partner_id.customer', '=', True)]
                return self.pool.get('res.partner.address').search(cr, uid,
                                                                   crit,
                                                                   context=context)
            else:
                return [customer_addr_id.id for customer_addr_id in form.customer_addr_ids]
        # Related to customer_addr_ids [END]

    _date_format = '%Y-%m-%d'

    def print_report(self, cr, uid, ids, context=None, data=None):
        if context is None:
            context = {}

        form = self.get_form(cr, uid, ids, context=context)
        report_wizard = _report_wizard_registry[normalize_rpt_name(form.rpt_name)](cr)
        rpt_name = report_wizard.print_report(cr, uid, form, context=context) or form.rpt_name

        # Refresh form data that might have been altered by report_wizard
        form = self.get_form(cr, uid, ids, context=context)

        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'via.jasper.report')
        data['form'] = {'id': form.id}

        (_service_name_filter,
         _service_name_filter_ctx) = report_wizard.get_service_name_filter(cr,
                                                                           uid,
                                                                           form,
                                                                           context=context)

        service_name = utility.get_service_name(cr, uid,
            rpt_name,
            form.rpt_output,
            _service_name_filter,
            _service_name_filter_ctx)

        # Redirect to reporting service
        return {'type': 'ir.actions.report.xml',
                'report_name': service_name,
                'datas': data}

    def get_form(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        return self.pool.get('via.jasper.report').browse(cr, uid, ids[0], context=context)

    def add_marshalled_data(self, cr, uid, _id, key, value, context=None):
        if isinstance(_id, list):
            _id = _id[0]
        entry = _marshalled_data_registry.setdefault(_id, {})
        entry.update({key: value})

    def set_current_domain(self, cr, uid, _id, dom_dict, context=None):
        _idkey = _id and _id[0] or id(self)
        entry = _current_domain_registry.setdefault(_idkey, {})
        entry.update(dom_dict)

    def get_current_domain(self, cr, uid, _id, field, context=None):
        _idkey = _id and _id[0] or id(self)
        entry = _current_domain_registry.get(_idkey, {})
        entry = entry.get(field, [])
        if not entry:
            _wizard = _report_wizard_registry[normalize_rpt_name(context.get('via_jasper_report_utils.rpt_name', ''))](cr)
            if _id:
                _locals = self.read(cr, uid, _id, context=context)
                _locals = _locals and prep_dict_for_write(cr, uid, _locals[0], context=context) or {}

                entry = eval(_wizard._domain.get(field, "[]"), _locals)
        return entry

    def _auto_init(self, cr, context=None):
        super(via_jasper_report, self)._auto_init(cr, context=context)
        # Create symbolic links to the specified generic classes to the jasper_server's custom_report directory
        _my_path = os.path.abspath(os.path.dirname(__file__))
        _my_classes = glob.glob(os.path.join(_my_path, 'report', '*.class'))

        _jr_path = addons.get_module_path('jasper_reports')
        if not _jr_path:
            raise Exception('Cannot find  "jasper_reports" module in the addon paths')

        _link_dir = os.path.join(_jr_path, 'custom_reports')
        for _class in _my_classes:
            _filename = os.path.basename(_class)
            _new_link = os.path.join(_link_dir, _filename)
            if os.path.lexists(_new_link):
                os.unlink(_new_link)
            os.symlink(_class, _new_link)

via_jasper_report()


# The following is for marshalling report parameters without going through the
# data passing activity to the OERP client that can cause a lot of troubles.
class ir_actions_report_xml(osv.osv):
    _inherit = 'ir.actions.report.xml'

    def _read_flat(self, cr, user, ids, fields_to_read, context=None, load='_classic_read'):
        res = super(ir_actions_report_xml, self)._read_flat(cr, user, ids, fields_to_read, context=context, load=load)
        for _data in res:
            if 'report_type' in _data:
                cr.execute("SELECT jasper_report FROM %s WHERE id = %s" % (self._table, str(_data.get('id', 0))))
                _is_jasper = cr.fetchone()
                if _is_jasper[0]:
                    _data.update({'report_type': 'jaspser'})

        return res

    def register_all(self, cr):
        res = super(ir_actions_report_xml, self).register_all(cr)
        cr.execute("SELECT *"
                   " FROM ir_act_report_xml"
                   " WHERE report_rml ilike '%.jrxml'"
                   " ORDER BY id")
        records = cr.dictfetchall()

        class via_report_parser(object):
            def __init__(self, cr, uid, ids, data, context):
                try:
                    import release
                    import pooler
                except ImportError:
                    from openerp import release
                    from openerp import pooler

                self.cr = cr
                self.uid = uid
                self.ids = ids
                self.data = data
                self.model = self.data.get('model', False) or context.get('active_model', False)
                self.context = context or {}
                self.pool = pooler.get_pool(self.cr.dbname)
                self.parameters = {}

                # Set OERP_USER
                res_users_pool = self.pool.get('res.users')
                oerp_user = res_users_pool.browse(cr, uid, uid, context=context)
                self.parameters['OERP_USER'] = oerp_user.name

                if 'form' not in data:
                    # The user does not print through the wizard (this usually
                    # happens when the user click the print button on the RHS of
                    # the form or tree view). So, do not perform the wizard
                    # marshalling process. Performing such a process may cause
                    # a problem due to unexpected name clash over the use of
                    # OERP_ACTIVE_IDS (e.g., QCF report).
                    self.parameters['OERP_ACTIVE_IDS'] = ','.join([str(_id)
                                                                   for _id in ids])
                    return

                pool = self.pool.get('via.jasper.report')
                o = pool.browse(cr, uid, data['form']['id'], context)

                # Companies
                company_ids = ','.join(str(com_id.id)
                                       for com_id in o.company_ids)
                selected_companies = ''
                if len(company_ids) == 0:
                    company_ids = 'NULL'
                else:
                    selected_companies = ', '.join(com_id.name
                                                   for com_id in o.company_ids)

                allowed_company_ids = []

                def _get_company_ids(cr, uid, company, res):
                    res.append(company.id)
                    for com_child in company.child_ids:
                        _get_company_ids(cr, uid, com_child, res)
                _get_company_ids(cr, uid, o.company_id, allowed_company_ids)
                allowed_company_ids = ','.join(str(_id)
                                               for _id in allowed_company_ids)

                timezone = oerp_user.partner_id and oerp_user.partner_id.tz
                # Timezone
                self.parameters.update({
                    'TIMEZONE': timezone or 'Asia/Jakarta',
                })

                self.parameters.update({
                    'COMPANY_ID': o.company_id.id,
                    'COMPANY_NAME': o.company_id.name or '',
                    'COMPANY_CURRENCY_NAME': o.company_id.currency_id.name or '',
                    'COMPANY_IDS': company_ids,
                    'SELECTED_COMPANIES': selected_companies,
                    'ALLOWED_COMPANY_IDS': allowed_company_ids,
                })

                # State
                self.parameters.update({
                    'SELECTED_STATE': o.state or '',
                })

                # Filter selection
                self.parameters.update({
                    'SELECTED_FILTER_SELECTION': o.filter_selection or '',
                    'SELECTED_FILTER_SELECTION_2': o.filter_selection_2 or '',
                })

                # Order-by columns
                if len(o.orderby_ids):
                    self.parameters.update({
                        'ORDERBY_CLAUSE': ','.join([obj.column_name + ' ' + obj.order_dir
                                                    for obj in o.orderby_ids]),
                        'ORDERBY_CLAUSE_STR': ', '.join(obj.column_display_name + ' (' + obj.order_dir.capitalize() + ')'
                                                        for obj in o.orderby_ids),
                    })

                default_date = date.today()

                # Date type 1: granularity month
                self.parameters.update({
                    'FROM_DATE_1_YR': (o.from_yr or default_date.year),
                    'FROM_DATE_1_MO': (o.from_mo or default_date.month),
                    'FROM_DATE_1_DY': 1,
                })

                to_yr = (o.to_yr or default_date.year)
                to_mo = (o.to_mo or default_date.month)
                self.parameters.update({
                    'TO_DATE_1_YR': to_yr,
                    'TO_DATE_1_MO': to_mo,
                    'TO_DATE_1_DY': calendar.monthrange(int(to_yr),
                                                        int(to_mo))[1],
                })

                # Date type 2: granularity day
                self.parameters.update({
                    'FROM_DATE_2_YR': o.from_dt and dt(o.from_dt).year or default_date.year,
                    'FROM_DATE_2_MO': o.from_dt and dt(o.from_dt).month or default_date.month,
                    'FROM_DATE_2_DY': o.from_dt and dt(o.from_dt).day or default_date.day,
                    'TO_DATE_2_YR': o.to_dt and dt(o.to_dt).year or default_date.year,
                    'TO_DATE_2_MO': o.to_dt and dt(o.to_dt).month or default_date.month,
                    'TO_DATE_2_DY': o.to_dt and dt(o.to_dt).day or default_date.day,
                    'AS_OF_DATE_2_YR': o.as_of_dt and dt(o.as_of_dt).year or default_date.year,
                    'AS_OF_DATE_2_MO': o.as_of_dt and dt(o.as_of_dt).month or default_date.month,
                    'AS_OF_DATE_2_DY': o.as_of_dt and dt(o.as_of_dt).day or default_date.day,
                    'FROM_DATE_2_YR_2': o.from_dt_2 and dt(o.from_dt_2).year or default_date.year,
                    'FROM_DATE_2_MO_2': o.from_dt_2 and dt(o.from_dt_2).month or default_date.month,
                    'FROM_DATE_2_DY_2': o.from_dt_2 and dt(o.from_dt_2).day or default_date.day,
                    'TO_DATE_2_YR_2': o.to_dt_2 and dt(o.to_dt_2).year or default_date.year,
                    'TO_DATE_2_MO_2': o.to_dt_2 and dt(o.to_dt_2).month or default_date.month,
                    'TO_DATE_2_DY_2': o.to_dt_2 and dt(o.to_dt_2).day or default_date.day,
                })

                # Date type 3: granularity year
                self.parameters.update({
                    'AS_OF_DATE_3_YR': (o.as_of_yr or default_date.year),
                })

                # Related to prod_ids and prod_group_level
                self.parameters.update({
                    'PROD_GROUP_LEVEL': o.prod_group_level,
                    'PROD_CAT_CLAUSE': o.get_group_level_clause(context=context),
                    'PROD_IDS': ','.join('%d' % prod_id
                                         for prod_id in o.get_prod_ids(context=context)),
                    'PROD_IDS_EMPTY_IS_NONE': o.prod_ids_empty_is_none,
                })

                # Related to prod_ids_2
                self.parameters.update({
                    'PROD_IDS_2': ','.join('%d' % prod_id_2
                                           for prod_id_2 in o.get_prod_ids_2(context=context)),
                    'PROD_IDS_2_EMPTY_IS_NONE': o.prod_ids_2_empty_is_none,
                })

                # Related to salesman_ids
                self.parameters.update({
                    'SALESMAN_IDS': ','.join('%d' % salesman_id
                                             for salesman_id in o.get_salesman_ids(context=context)),
                })

                # Related to customer_ids
                self.parameters.update({
                    'CUSTOMER_IDS': ','.join('%d' % customer_id
                                             for customer_id in o.get_customer_ids(context=context))
                })

                if float(release.major_version) < 7.0:
                    # Related to customer_addr_ids
                    self.parameters.update({
                        'CUSTOMER_ADDR_IDS': ','.join('%d' % customer_addr_id
                                                      for customer_addr_id in o.get_customer_addr_ids(context=context))
                    })

                self.parameters.update({
                    'NO_ZERO': o.no_zero,
                    'USE_INDENTATION': o.use_indentation,
                    'NO_WRAP': o.no_wrap,
                    'DISPLAY_LARGE': o.display_large,
                    'REFERENCE_LABEL': o.reference_label or '',
                    'COMPARISON_LABEL': o.comparison_label or '',
                    'DISPLAY_COMPARISON': o.display_comparison,
                })

                # Other marshalled data
                if o.id in _marshalled_data_registry:
                    self.parameters.update(_marshalled_data_registry[o.id])
                    del _marshalled_data_registry[o.id]

            def get(self, key, default):
                return (key == 'parameters') and self.parameters or default

        from jasper_reports.jasper_report import report_jasper

        for record in records:
            name = 'report.%s' % record['report_name']
            report_jasper(name, record['model'], via_report_parser)

        return res

ir_actions_report_xml()
