###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2013 Vikasa Infinity Anugrah <http://www.infi-nity.com>
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

import re
from util_jrxml import JRXML_NS, JR, tag_name, set_x, set_y, \
    get_width, get_height, insert_element
from lxml import etree
from copy import deepcopy

PROPERTY_KEY = 'via.crosstab.'

def transform_jrxml_make_crosstab_cmd_opts(parser):
    parser.add_option('', '--no-transform-to-crosstab', dest='transform_to_crosstab', action='store_false',
                      default=True, help='Preprocess by transforming "via.crosstab.*" tagged components to crosstab ones')

    def options_parser(options):
        pass
    return options_parser

def _validate_cell_contents(props):
    if len(props) == 0:
        return

    if len(filter(lambda el: tag_name(el.getparent().getparent().tag) != 'frame',
                  props)) != 0:
        raise Exception('unframed cell content')

    if len(set(map(lambda el: el.getparent().get('style', None),
                   props))) != 1:
        raise Exception('ununiform style')

    if len(set(map(lambda el: el.getparent().get('x'),
                   props))) != 1:
        raise Exception('ununiform x')

    if len(set(map(lambda el: el.getparent().get('y'),
                   props))) != 1:
        raise Exception('ununiform y')

    if len(set(map(lambda el: el.getparent().get('width'),
                   props))) != 1:
        raise Exception('ununiform width')

    if len(set(map(lambda el: el.getparent().get('height'),
                   props))) != 1:
        raise Exception('ununiform height')

def _get_cell_contents(props):
    _validate_cell_contents(props)

    style = None
    cell_contents = etree.Element(JR + 'cellContents')
    for prop in props:
        frame = deepcopy(prop.getparent().getparent())
        set_x(frame, 0)
        set_y(frame, 0)

        report_element = frame[0]
        style = report_element.get('style', None)
        if style is not None:
            del report_element.attrib['style']

        cell_contents.append(frame)

    if style is not None:
        cell_contents.set('style', style)

    return cell_contents

def _get_length_name_and_amount(group_name, sample, invert=False):
    if invert:
        if group_name == 'rowGroup':
            group_name = 'columnGroup'
        else:
            group_name = 'rowGroup'

    if group_name == 'rowGroup':
        length_name_1 = 'width'
        get_length_amount_1 = get_width
        length_name_2 = 'height'
        get_length_amount_2 = get_height
    else:
        length_name_1 = 'height'
        get_length_amount_1 = get_height
        length_name_2 = 'width'
        get_length_amount_2 = get_width

    length_amount_1 = '%d' % get_length_amount_1(sample)
    length_amount_2 = '%d' % get_length_amount_2(sample)

    return (length_name_1, length_amount_1,
            length_name_2, length_amount_2)

class CrosstabGroup(object):
    def __init__(self, crosstab_id, group_name, group_id, bucket_name, bucket_expr, root):
        self.crosstab_id = crosstab_id
        self.group_name = group_name
        self.group_id = group_id
        self.bucket_name = bucket_name

        if bucket_expr is None:
            self.bucket_expr = '$F{%s}' % bucket_name
        else:
            if bucket_expr != 'true':
                raise Exception('Cannot handle custom bucket expression of %s%d.%s.%d: %s'
                                % (PROPERTY_KEY, crosstab_id,
                                   group_name, group_id, bucket_expr))
            self.bucket_expr = bucket_expr

        (self.crosstab_group,
         self.crosstab_group_length_1_name,
         self.crosstab_group_length_1,
         self.crosstab_group_length_2_name,
         self.crosstab_group_length_2,
         self.crosstab_cell_length_1_name,
         self.crosstab_cell_length_1,
         self.crosstab_cell_length_2_name) = self._create_crosstab_group(root)

        (self.crosstab_cell,
         crosstab_cell_length_1,
         self.crosstab_cell_length_2) = self._create_crosstab_cell(root)

        if crosstab_cell_length_1 != self.crosstab_cell_length_1:
            raise Exception('The %s of %s%d.cell.%s.%d must be %d'
                            % (self.crosstab_cell_length_1_name,
                               PROPERTY_KEY, self.crosstab_id,
                               self.group_name, self.group_id,
                               self.crosstab_cell_length_1))

    def __repr__(self):
        return repr({
            'crosstab_id': self.crosstab_id,
            'group_name': self.group_name,
            'group_id': self.group_id,
            'bucket_name': self.bucket_name,
            'bucket_expr': self.bucket_expr,
            'crosstab_group': etree.tostring(self.crosstab_group,
                                             pretty_print=True),
            'crosstab_group_length_1_name': self.crosstab_group_length_1_name,
            'crosstab_group_length_1': self.crosstab_group_length_1,
            'crosstab_group_length_2_name': self.crosstab_group_length_2_name,
            'crosstab_group_length_2': self.crosstab_group_length_2,
            'crosstab_cell': (self.crosstab_cell
                              and etree.tostring(self.crosstab_cell,
                                                 pretty_print=True)
                              or None),
            'crosstab_cell_length_1_name': self.crosstab_cell_length_1_name,
            'crosstab_cell_length_1': self.crosstab_cell_length_1,
            'crosstab_cell_length_2_name': self.crosstab_cell_length_2_name,
            'crosstab_cell_length_2': self.crosstab_cell_length_2,
        })

    def _get_cell_contents(self, root, infix='', suffix=''):
        props = root.xpath("//jr:property[@name='%s%d%s.%s.%d%s']"
                           % (PROPERTY_KEY, self.crosstab_id, infix, self.group_name, self.group_id, suffix),
                           namespaces=JRXML_NS)
        try:
            return _get_cell_contents(props)
        except Exception as cause:
            raise Exception('%s%d.%s.%d has %s'
                            % (PROPERTY_KEY, self.crosstab_id,
                               self.group_name, self.group_id,
                               cause))

    def _get_hdr_total_cell_contents(self, root):
        return self._get_cell_contents(root, suffix='.total')

    def _get_total_cell_contents(self, root):
        return self._get_cell_contents(root, infix='.cell')

    def _get_bucket_class(self, root):
        if self.bucket_expr == 'true':
            return 'java.lang.Boolean'
        elif self.bucket_expr.find('$F{') == 0:
            fields = root.xpath(".//jr:field[@name='%s']" % self.bucket_name,
                                namespaces=JRXML_NS)
            if len(fields) > 1:
                if len(set(map(lambda f: f.get('class', None), fields))) != 1:
                    raise Exception('Field %s is more than one but their class do not agree'
                                    % self.bucket_name)
                return fields[0].get('class', None)
            elif len(fields) == 0:
                raise Exception('Field %s does not exist' % self.bucket_name)
            else:
                return fields[0].get('class', None)
        else:
            raise Exception('Cannot determine bucket expression class')

    def _create_crosstab_cell(self, root):
        total_cell_contents = self._get_total_cell_contents(root)
        if len(total_cell_contents) == 0:
            return (None, 0, 0)

        (length_name_1, length_amount_1,
         length_name_2, length_amount_2) = _get_length_name_and_amount(self.group_name,
                                                                       total_cell_contents[0],
                                                                       invert=True)

        cell_element = etree.Element(JR + 'crosstabCell')
        cell_element.set('%sTotalGroup'
                         % (self.group_name == 'rowGroup' and 'row'
                            or 'column'),
                         self.bucket_name)
        cell_element.set(length_name_1, length_amount_1)

        cell_element.append(total_cell_contents)

        return (cell_element, int(length_amount_1), int(length_amount_2))

    def _create_crosstab_group(self, root):
        bucket_class = self._get_bucket_class(root)
        cell_contents = self._get_cell_contents(root)
        total_cell_contents = self._get_hdr_total_cell_contents(root)

        group_element = etree.Element(JR + self.group_name,
                                      name=self.bucket_name)

        if len(total_cell_contents) > 0:
            group_element.set('totalPosition', 'End')

        (group_length_name_1, group_length_amount_1,
         group_length_name_2, group_length_amount_2) = _get_length_name_and_amount(self.group_name,
                                                                                   cell_contents[0])

        group_element.set(group_length_name_1, group_length_amount_1)

        bucket_element = etree.SubElement(group_element, JR + 'bucket')
        bucket_element.set('class', bucket_class)

        bucket_expr_element = etree.SubElement(bucket_element,
                                               JR + 'bucketExpression')
        bucket_expr_element.text = etree.CDATA(self.bucket_expr)

        group_header_element = etree.SubElement(group_element,
                                                JR + ('crosstab%sHeader'
                                                      % (self.group_name == 'rowGroup' and 'Row'
                                                         or 'Column')))
        group_header_element.append(cell_contents)

        group_total_header_element = etree.SubElement(group_element,
                                                      JR + ('crosstabTotal%sHeader'
                                                            % (self.group_name == 'rowGroup' and 'Row'
                                                               or 'Column')))
        group_total_header_element.append(total_cell_contents)

        if len(total_cell_contents) == 0:
            if self.group_name == 'rowGroup':
                cell_length_name_1 = 'height'
                cell_length_name_2 = 'width'
            else:
                cell_length_name_1 = 'width'
                cell_length_name_2 = 'height'
            cell_length_amount_1 = 0
            cell_length_amount_2 = 0
        else:
            (cell_length_name_1, cell_length_amount_1,
             cell_length_name_2, cell_length_amount_2) = _get_length_name_and_amount(self.group_name,
                                                                                     total_cell_contents[0],
                                                                                     invert=True)
        return (group_element,
                group_length_name_1, int(group_length_amount_1),
                group_length_name_2, int(group_length_amount_2),
                cell_length_name_1, int(cell_length_amount_1),
                cell_length_name_2)

class CrosstabGroups(object):
    def __init__(self, crosstab_id, group_name, root):
        self.crosstab_id = crosstab_id
        self.group_name = group_name

        self.groups = self._extract_groups(root, crosstab_id, group_name)
        self._validate_groups(self.groups, crosstab_id, group_name)

    def _validate_groups(self, groups, crosstab_id, group_name):
        groups_len = len(groups)

        if groups_len == 0:
            raise Exception('No %s specified for crosstab %d'
                            % (group_name, crosstab_id))

        if len(set(group.group_id for group in groups)) != groups_len:
            raise Exception('Duplicated group ID in crosstab %d'
                            % crosstab_id)

        if len(set(group.bucket_name for group in groups)) != groups_len:
            raise Exception('Duplicated bucket name in crosstab %d'
                            % crosstab_id)

        if group_name == 'rowGroup':
            group_length_name = 'height'
            cell_length_name = 'width'
        else:
            group_length_name = 'width'
            cell_length_name = 'height'

        reversed_groups = list(groups)
        reversed_groups.reverse()
        next_length_1 = 0
        next_length_2 = reversed_groups[0].crosstab_group_length_2
        for group in reversed_groups:
            if group.crosstab_group.xpath("./jr:crosstab%sHeader/jr:cellContents/jr:frame/jr:reportElement[@%s != '%d']"
                                          % (group_name == 'rowGroup' and 'Row' or 'Column',
                                             group_length_name,
                                             next_length_2),
                                          namespaces=JRXML_NS):
                raise Exception('The %s of %s%d.%s.%d must be %d'
                                % (group_length_name,
                                   PROPERTY_KEY, crosstab_id,
                                   group.group_name, group.group_id,
                                   next_length_2))
            next_length_2 += group.crosstab_cell_length_1

            next_length_1 += group.crosstab_group_length_1
            if group.crosstab_group.xpath("./jr:crosstabTotal%sHeader/jr:cellContents/jr:frame/jr:reportElement[@%s != '%d']"
                                          % (group_name == 'rowGroup' and 'Row' or 'Column',
                                             cell_length_name,
                                             next_length_1),
                                          namespaces=JRXML_NS):
                raise Exception('The %s of %s%d.%s.%d.total must be %d'
                                % (cell_length_name,
                                   PROPERTY_KEY, crosstab_id,
                                   group.group_name, group.group_id,
                                   next_length_1))

    def _extract_groups(self, root, crosstab_id, group_name):
        groups = []
        for group_info in root.xpath("./jr:property[starts-with(@name, '%s%d.%s.')]"
                                     % (PROPERTY_KEY, crosstab_id, group_name),
                                     namespaces=JRXML_NS):
            prop_name = group_info.get('name')

            group_id = int(re.sub(r'%s%d.%s.(\d+).+'
                                  % (PROPERTY_KEY, crosstab_id, group_name),
                                  r'\1',
                                  prop_name))
            bucket_name = re.sub(r'%s%d.%s.%d.bucket.(.+)'
                                 % (PROPERTY_KEY, crosstab_id, group_name, group_id),
                                 r'\1',
                                 prop_name)

            groups.append(CrosstabGroup(crosstab_id, group_name, group_id, bucket_name,
                                        group_info.get('value', None) or None, root))

        groups = sorted(groups, key=(lambda x: x.group_id))

        return groups

class Crosstab(object):
    def __init__(self, crosstab_id, root):
        self.crosstab_id = crosstab_id

        self.crosstab_print_when_expr = self._get_crosstab_print_when_expr(root)

        self.crosstab_style = self._get_crosstab_style(root)

        self.crosstab_dataset = self._create_crosstab_dataset(root)

        self.row_groups = CrosstabGroups(crosstab_id, 'rowGroup', root)
        self.col_groups = CrosstabGroups(crosstab_id, 'columnGroup', root)
        self._validate_groups(self.row_groups.groups, self.col_groups.groups)

        (self.crosstab_header_width,
         self.crosstab_header_height,
         self.crosstab_cell_width,
         self.crosstab_cell_height) = self._get_crosstab_lengths(self.row_groups.groups,
                                                                 self.col_groups.groups)

        self.crosstab_parameters = self._create_crosstab_parameters(root)
        self.crosstab_dataset_run = self._create_crosstab_dataset_run(root)
        self.crosstab_header = self._create_crosstab_header(root)
        self.crosstab_measures = self._create_crosstab_measures(root)
        self.crosstab_cell = self._create_crosstab_cell(root)
        self.crosstab_total_cells = self._create_crosstab_total_cells(root,
                                                                      self.row_groups.groups,
                                                                      self.col_groups.groups)
        self.crosstab_when_no_data_cell = self._create_crosstab_when_no_data_cell(root)

        self.crosstab = self._create(root)

    def _get_crosstab_print_when_expr(self, root):
        expr = root.xpath("./jr:property[@name='%s%d.printWhenExpression']"
                          % (PROPERTY_KEY, self.crosstab_id),
                          namespaces=JRXML_NS)
        if len(expr):
            return expr[0].get('value')
        return ''

    def _get_crosstab_style(self, root):
        crosstab_style = root.xpath("./jr:property[@name='%s%d.style']"
                                    % (PROPERTY_KEY, self.crosstab_id),
                                    namespaces=JRXML_NS)
        if len(crosstab_style):
            return crosstab_style[0].get('value')
        return ''

    def _create_crosstab_parameters(self, root):
        crosstab_parameters = []
        for param in root.xpath("./jr:parameter", namespaces=JRXML_NS):
            expr = r'$P{%s}' % param.get('name')
            crosstab_parameter = etree.Element(JR + 'crosstabParameter')
            crosstab_parameter.set('name', param.get('name'))
            crosstab_parameter.set('class', param.get('class'))
            etree.SubElement(crosstab_parameter,
                             JR + 'parameterValueExpression').text = etree.CDATA(expr)
            crosstab_parameters.append(crosstab_parameter)
        return crosstab_parameters

    def _get_dataset_name(self):
        return '%s%d' % (PROPERTY_KEY, self.crosstab_id)

    def _create_crosstab_dataset(self, root):
        dataset = etree.Element(JR + 'subDataset',
                                name=self._get_dataset_name())
        for param in root.xpath("./jr:parameter", namespaces=JRXML_NS):
            dataset_parameter = etree.SubElement(dataset, JR + 'parameter')
            dataset_parameter.set('name', param.get('name'))
            dataset_parameter.set('class', param.get('class'))
        query_string = root.xpath("./jr:queryString", namespaces=JRXML_NS)[0]
        etree.SubElement(dataset, JR + 'queryString').text = etree.CDATA(query_string.text)
        for field in root.xpath("./jr:field", namespaces=JRXML_NS):
            dataset.append(deepcopy(field))
        return dataset

    def _create_crosstab_dataset_run(self, root):
        dataset_run = etree.SubElement(etree.SubElement(etree.Element(JR + 'crosstabDataset'),
                                                        JR + 'dataset'),
                                       JR + 'datasetRun',
                                       subDataset=self._get_dataset_name())
        for param in root.xpath("./jr:parameter", namespaces=JRXML_NS):
            expr = '$P{%s}' % param.get('name')
            etree.SubElement(etree.SubElement(dataset_run, JR + 'datasetParameter',
                                              name=param.get('name')),
                             JR + 'datasetParameterExpression').text = etree.CDATA(expr)
        etree.SubElement(dataset_run,
                         JR + 'connectionExpression').text = etree.CDATA('$P{REPORT_CONNECTION}')
        return dataset_run.getparent().getparent()

    def _validate_groups(self, row_groups, col_groups):

        for (checked_groups, ref_groups) in [(row_groups, col_groups), (col_groups, row_groups)]:
            crosstab_cell_length_2 = ref_groups[-1].crosstab_group_length_2
            for group in checked_groups:
                if group.crosstab_cell is None:
                    continue
                if group.crosstab_cell_length_2 != crosstab_cell_length_2:
                    raise Exception('The %s of %s%d.cell.%s.%d must be %d'
                                    % (group.crosstab_cell_length_2_name,
                                       PROPERTY_KEY, self.crosstab_id,
                                       group.group_name, group.group_id,
                                       crosstab_cell_length_2))

    def _get_crosstab_lengths(self, row_groups, col_groups):
        crosstab_header_width = sum(group.crosstab_group_length_1
                                    for group in row_groups)
        crosstab_header_height = sum(group.crosstab_group_length_1
                                     for group in col_groups)
        crosstab_cell_width = col_groups[-1].crosstab_group_length_2
        crosstab_cell_height = row_groups[-1].crosstab_group_length_2

        return (crosstab_header_width, crosstab_header_height,
                crosstab_cell_width, crosstab_cell_height)

    def _create_row_col_crosstab_cells(self, root, row_groups, col_groups):
        result = []

        row_groups_reversed = list(row_groups)
        row_groups_reversed.reverse()
        col_groups_reversed = list(col_groups)
        col_groups_reversed.reverse()
        for row_group in row_groups_reversed:
            for col_group in col_groups_reversed:
                props = root.xpath("//jr:property[@name='%s%d.cell.%s.%d.%s.%d']"
                                   % (PROPERTY_KEY, self.crosstab_id,
                                      row_group.group_name, row_group.group_id,
                                      col_group.group_name, col_group.group_id),
                                   namespaces=JRXML_NS)
                try:
                    cell_contents = _get_cell_contents(props)
                except Exception as cause:
                    raise Exception('%s%d.cell.%s.%d.%s.%d has %s'
                                    % (PROPERTY_KEY, self.crosstab_id,
                                       row_group.group_name, row_group.group_id,
                                       col_group.group_name, col_group.group_id,
                                       cause))
                if len(cell_contents) == 0:
                    continue

                (length_name_1, length_amount_1,
                 length_name_2, length_amount_2) = _get_length_name_and_amount('rowGroup',
                                                                               cell_contents[0])
                if int(length_amount_1) != col_group.crosstab_cell_length_1:
                    raise Exception('The %s of %s%d.cell.%s.%d.%s.%d must be %d'
                                    % (length_name_1,
                                       PROPERTY_KEY, self.crosstab_id,
                                       row_group.group_name, row_group.group_id,
                                       col_group.group_name, col_group.group_id,
                                       col_group.crosstab_cell_length_1))
                if int(length_amount_2) != row_group.crosstab_cell_length_1:
                    raise Exception('The %s of %s%d.cell.%s.%d.%s.%d must be %d'
                                    % (length_name_2,
                                       PROPERTY_KEY, self.crosstab_id,
                                       row_group.group_name, row_group.group_id,
                                       col_group.group_name, col_group.group_id,
                                       row_group.crosstab_cell_length_1))

                crosstab_cell = etree.Element(JR + 'crosstabCell',
                                              width=length_amount_1,
                                              height=length_amount_2,
                                              rowTotalGroup=row_group.bucket_name,
                                              columnTotalGroup=col_group.bucket_name)
                crosstab_cell.append(cell_contents)

                result.append(crosstab_cell)
        return result

    def _create_crosstab_header(self, root):
        props = root.xpath("//jr:property[@name='%s%d.header']"
                           % (PROPERTY_KEY, self.crosstab_id),
                           namespaces=JRXML_NS)
        try:
            hdr_cell_contents =  _get_cell_contents(props)
        except Exception as cause:
            raise Exception('%s%d.header has %s'
                            % (PROPERTY_KEY, self.crosstab_id, cause))

        if hdr_cell_contents.xpath("./jr:frame/jr:reportElement[@width != '%d' or @height != '%d']"
                                   % (self.crosstab_header_width,
                                      self.crosstab_header_height),
                                   namespaces=JRXML_NS):
            raise Exception('%s%d.header height or width does not match the total of the column or row groups'
                            % (PROPERTY_KEY, self.crosstab_id))

        crosstab_hdr_cell = etree.Element(JR + 'crosstabHeaderCell')
        crosstab_hdr_cell.append(hdr_cell_contents)
        return crosstab_hdr_cell

    def _create_crosstab_when_no_data_cell(self, root):
        crosstab_hdr_cell = self._create_crosstab_header(root)
        crosstab_hdr_cell.tag = JR + 'whenNoDataCell'
        return crosstab_hdr_cell

    def _create_crosstab_measures(self, root):
        already_used_fields = set(group.bucket_name for group in (self.row_groups.groups
                                                                  + self.col_groups.groups))
        measures = []
        for field in root.xpath("./jr:field", namespaces=JRXML_NS):
            if field.get('name') in already_used_fields:
                continue
            measure = etree.Element(JR + 'measure')
            measure.set('name', field.get('name'))
            measure.set('class', field.get('class'))

            measure_calculation = field.xpath("./jr:property[starts-with(@name, '%s%d.measure.calculation.')]"
                                              % (PROPERTY_KEY, self.crosstab_id),
                                              namespaces=JRXML_NS)
            if len(measure_calculation):
                measure_calculation = measure_calculation[0]
                calculation = measure_calculation.get('name').split('.')[-1]
                measure.set('calculation', calculation.capitalize())

            measure_expr = etree.SubElement(measure, JR + 'measureExpression')
            measure_expr.text = etree.CDATA(r'$F{%s}' % field.get('name'))

            measures.append(measure)
        return measures

    def _create_crosstab_cell(self, root):
        props = root.xpath("//jr:property[@name='%s%d.cell']"
                           % (PROPERTY_KEY, self.crosstab_id),
                           namespaces=JRXML_NS)
        try:
            cell_contents = _get_cell_contents(props)
        except Exception as cause:
            raise Exception('%s%d.cell has %s'
                            % (PROPERTY_KEY, self.crosstab_id, cause))

        (length_name_1, length_amount_1,
         length_name_2, length_amount_2) = _get_length_name_and_amount('rowGroup',
                                                                       cell_contents[0])
        if int(length_amount_1) != self.crosstab_cell_width:
            raise Exception('%s%d.cell width must be %d'
                            % (PROPERTY_KEY, self.crosstab_id, self.crosstab_cell_width))
        if int(length_amount_2) != self.crosstab_cell_height:
            raise Exception('%s%d.cell height must be %d'
                            % (PROPERTY_KEY, self.crosstab_id, self.crosstab_cell_height))

        crosstab_cell = etree.Element(JR + 'crosstabCell',
                                      width=length_amount_1,
                                      height=length_amount_2)
        crosstab_cell.append(cell_contents)

        return crosstab_cell

    def _create_crosstab_total_cells(self, root, row_groups, col_groups):
        total_cells = []

        row_groups_reversed = list(row_groups)
        row_groups_reversed.reverse()
        for row_group in row_groups_reversed:
            if row_group.crosstab_cell is None:
                continue
            total_cells.append(row_group.crosstab_cell)

        col_groups_reversed = list(col_groups)
        col_groups_reversed.reverse()
        for col_group in col_groups_reversed:
            if col_group.crosstab_cell is None:
                continue
            total_cells.append(col_group.crosstab_cell)

        total_cells.extend(self._create_row_col_crosstab_cells(root,
                                                               row_groups,
                                                               col_groups))

        return total_cells

    def _create(self, root):
        crosstab = etree.Element(JR + 'crosstab', columnBreakOffset='999999999')
        report_element = etree.SubElement(crosstab, JR + 'reportElement',
                                          x='0', y='0', width=root.get('columnWidth'),
                                          height=('%d' % self.crosstab_header_height))
        if self.crosstab_style:
            report_element.set('style', self.crosstab_style)

        crosstab.extend(self.crosstab_parameters)
        crosstab.append(self.crosstab_dataset_run)
        crosstab.append(self.crosstab_header)
        for group in self.row_groups.groups:
            crosstab.append(group.crosstab_group)
        for group in self.col_groups.groups:
            crosstab.append(group.crosstab_group)
        crosstab.extend(self.crosstab_measures)
        crosstab.append(self.crosstab_cell)
        crosstab.extend(self.crosstab_total_cells)
        crosstab.append(self.crosstab_when_no_data_cell)

        field_list = [field.get('name')
                      for field in root.xpath("./jr:field", namespaces=JRXML_NS)]
        self._adjust_field_reference(root, crosstab, field_list)

        return crosstab

    def _adjust_field_reference(self, root, crosstab, field_list):
        # Get expressions
        exprs = crosstab.xpath(".//jr:cellContents//jr:textFieldExpression"
                               "|.//jr:cellContents//jr:printWhenExpression",
                               namespaces=JRXML_NS)

        # Get style expressions
        target_styles = set()
        for style in crosstab.xpath(".//jr:cellContents[@style]"
                                   "|.//jr:cellContents//jr:reportElement[@style]",
                                   namespaces=JRXML_NS):
            target_styles.add(style.get('style'))

        unrolled_target_styles = set()
        for target_style in target_styles:
            inheritance_path = target_style.split('.')
            for idx in range(1, len(inheritance_path) + 1):
                unrolled_target_styles.add('.'.join(inheritance_path[:idx]))

        exprs.extend(root.xpath('|'.join("./jr:style[@name='%s']//jr:conditionExpression"
                                         % target_style
                                         for target_style in unrolled_target_styles),
                                namespaces=JRXML_NS))

        # Adjust
        for expr in exprs:
            for field in field_list:
                expr.text = etree.CDATA(expr.text.replace('$F{%s}' % field,
                                                          '$V{%s}' % field))

def transform_jrxml_make_crosstab(jrxml, jrxml_opts):
    if not jrxml_opts.transform_to_crosstab:
        return

    root = jrxml.getroot()

    crosstab_ids = set(map(lambda prop_el: int(re.sub(PROPERTY_KEY + r'(\d+).+',
                                                      r'\1',
                                                      prop_el.get('name'))),
                           root.xpath("./jr:property[starts-with(@name, '"
                                      + PROPERTY_KEY
                                      + "')]",
                                      namespaces=JRXML_NS)))
    if len(crosstab_ids) == 0:
        return

    crosstabs = []
    for crosstab_id in crosstab_ids:
        crosstabs.append(Crosstab(crosstab_id, root))

    # Set the stage
    for query_string in root.xpath("./jr:queryString", namespaces=JRXML_NS):
        root.remove(query_string)
    for field in root.xpath("./jr:field", namespaces=JRXML_NS):
        root.remove(field)
    for column_header in root.xpath("./jr:columnHeader", namespaces=JRXML_NS):
        root.remove(column_header)
    for detail in root.xpath("./jr:detail", namespaces=JRXML_NS):
        root.remove(detail)

    query_string = etree.Element(JR + 'queryString')
    query_string.text = etree.CDATA('SELECT * FROM UNNEST(ARRAY[0]) database_connection_opener')
    insert_element(root, query_string)

    detail = etree.Element(JR + 'detail')
    insert_element(root, detail)

    # Insert the crosstabs
    for crosstab in crosstabs:
        insert_element(root, crosstab.crosstab_dataset)
        band = etree.SubElement(detail, JR + 'band',
                                height=('%d' % crosstab.crosstab_header_height),
                                splitType='Immediate')
        if crosstab.crosstab_print_when_expr:
            print_when_expr = etree.SubElement(band,
                                               JR + 'printWhenExpression')
            print_when_expr.text = etree.CDATA(crosstab.crosstab_print_when_expr)
        band.append(crosstab.crosstab)
