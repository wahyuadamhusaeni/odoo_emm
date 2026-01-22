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

from util_jrxml import JRXML_NS, JR, get_y, set_y

_GROUP_PAGINATION_ATTRS = ('isStartNewPage', 'isResetPageNumber',
                           'isReprintHeaderOnEachPage',
                           'minHeightToStartNewPage', 'footerPosition',
                           'keepTogether')

def _move_band_to_another_band(from_band, to_band, offset, beginning=False):
    if beginning is True:
        for child in to_band.getchildren():
            component_set_str(child, 'positionType', 'Float')
            set_y(child, get_y(child) + offset)
    for el in from_band.xpath("jr:*", namespaces=JRXML_NS):
        if beginning is False:
            component_set_str(el, 'positionType', 'Float')
            set_y(el, get_y(el) + offset)
        to_band.append(el)

def _move_heading_bands_to_title_band(root):
    page_header_band = root.xpath("jr:pageHeader/jr:band", namespaces=JRXML_NS)
    if len(page_header_band):
        page_header_band = page_header_band[0]
        page_header_band_height = int(page_header_band.get('height'))
    else:
        page_header_band = None
        page_header_band_height = 0

    column_header_band = root.xpath("jr:columnHeader/jr:band", namespaces=JRXML_NS)
    if len(column_header_band):
        column_header_band = column_header_band[0]
        column_header_band_height = int(column_header_band.get('height'))
    else:
        column_header_band = None
        column_header_band_height = 0

    if page_header_band is None and column_header_band is None:
        return

    title_band = root.xpath("jr:title/jr:band", namespaces=JRXML_NS)
    if len(title_band):
        title_band = title_band[0]
        title_band_height = int(title_band.get('height'))
    else:
        title_band = etree.SubElement(etree.SubElement(root, JR + 'title'),
                                      JR + 'band', height='0', splitType='Prevent')
        root.remove(title_band.getparent())
        if page_header_band is not None:
            root.insert(root.index(page_header_band.getparent()),
                         title_band.getparent())
        else:
            root.insert(root.index(column_header_band.getparent()),
                         title_band.getparent())
        title_band_height = 0

    title_band.set('height', '%d' % (title_band_height + page_header_band_height
                                     + column_header_band_height))

    if page_header_band is not None:
        _move_band_to_another_band(page_header_band, title_band,
                                   title_band_height)
        root.remove(page_header_band.getparent())
    if column_header_band is not None:
        _move_band_to_another_band(column_header_band, title_band,
                                   title_band_height + page_header_band_height)
        root.remove(column_header_band.getparent())

def _move_footing_bands_to_summary_band(root):
    column_footer_band = root.xpath("jr:columnFooter/jr:band", namespaces=JRXML_NS)
    if len(column_footer_band):
        column_footer_band = column_footer_band[0]
        column_footer_band_height = int(column_footer_band.get('height'))
    else:
        column_footer_band = None
        column_footer_band_height = 0

    last_page_footer_band = root.xpath("jr:lastPageFooter/jr:band", namespaces=JRXML_NS)
    if len(last_page_footer_band):
        last_page_footer_band = last_page_footer_band[0]
        last_page_footer_band_height = int(last_page_footer_band.get('height'))
    else:
        last_page_footer_band = None
        last_page_footer_band_height = 0

    page_footer_band = root.xpath("jr:pageFooter/jr:band", namespaces=JRXML_NS)
    if len(page_footer_band):
        page_footer_band = page_footer_band[0]
        page_footer_band_height = int(page_footer_band.get('height'))
    else:
        page_footer_band = None
        page_footer_band_height = 0

    if (column_footer_band is None and page_footer_band is None
        and last_page_footer_band is None):
            return

    summary_band = root.xpath("jr:summary/jr:band", namespaces=JRXML_NS)
    if len(summary_band):
        summary_band = summary_band[0]
        summary_band_height = int(summary_band.get('height'))
    else:
        summary_band = etree.SubElement(etree.SubElement(root, JR + 'summary'),
                                        JR + 'band', height='0', splitType='Immediate')
        root.remove(summary_band.getparent())
        if last_page_footer_band is not None:
            root.insert(root.index(last_page_footer_band.getparent()) + 1,
                         summary_band.getparent())
        elif page_footer_band is not None:
            root.insert(root.index(page_footer_band.getparent()) + 1,
                         summary_band.getparent())
        else:
            root.insert(root.index(column_footer_band.getparent()) + 1,
                         summary_band.getparent())
        summary_band_height = 0

    # last_page_footer_band and page_footer_band are mutually exclusive
    if last_page_footer_band is not None and page_footer_band is not None:
        root.remove(page_footer_band.getparent())
        page_footer_band = last_page_footer_band
        page_footer_band_height = last_page_footer_band_height
    elif last_page_footer_band is not None and page_footer_band is None:
        page_footer_band = last_page_footer_band
        page_footer_band_height = last_page_footer_band_height

    summary_band.set('height',
                     '%d' % (summary_band_height + page_footer_band_height
                             + column_footer_band_height))

    if page_footer_band is not None:
        _move_band_to_another_band(page_footer_band, summary_band,
                                   page_footer_band_height, beginning=True)
        root.remove(page_footer_band.getparent())
    if column_footer_band is not None:
        _move_band_to_another_band(column_footer_band, summary_band,
                                   column_footer_band_height, beginning=True)
        root.remove(column_footer_band.getparent())

def gen_jrxml_pageless(suffix, jrxml):
    root = jrxml.getroot()

    for attr in ('leftMargin', 'rightMargin', 'topMargin', 'bottomMargin'):
        root.set(attr, '0')
    root.set('name', '_'.join([root.get('name'), suffix]))
    root.set('isIgnorePagination', 'true')

    # It turns out that isIgnorePagination is sufficient.
    # # Taking care of pagination attributes in groups
    # for group in jrxml.xpath("//jr:group", namespaces=JRXML_NS):
    #     for attr in _GROUP_PAGINATION_ATTRS:
    #         try:
    #             del group.attrib[attr]
    #         except KeyError:
    #             pass
    #
    # # Move page header and column header to title band
    # _move_heading_bands_to_title_band(root)
    #
    # # Move column footer, page footer, and last page footer to summary
    # _move_footing_bands_to_summary_band(root)

    return jrxml
