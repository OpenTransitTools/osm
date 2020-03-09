#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from ott.utils import file_utils
from ott.utils import date_utils

from .osm_abbr_parser import OsmAbbrParser

import logging
log = logging.getLogger(__file__)


class OsmRename(object):
    """ Utility for getting stats on an osm file 
    """
    attrib = "streets renamed by OpenTransitTools on {}".format(date_utils.pretty_date())
    bunchsize = 1000000
    rename_cache = {}

    def __init__(self, osm_infile_path, osm_outfile_path, do_bkup=True):
        """ this class will work to rename streets in OSM, abbreviating common street prefix and suffixes
            (e.g., North == N, Southeast == SE, Street == St, Avenue == Ave, etc...)
            
            :note this assumes that each OSM <tag /> falls completely upon a single line of the file 
            and the parser / renamer will break if targeted tags are spread across multiple lines of the file

            @todo look at SAX
            https://gist.github.com/veryhappythings/98604
            :todo ... add unit tests
            TODO: fix up hacky parts...
        """
        self.osm_input_path = osm_infile_path
        if osm_outfile_path is None or len(osm_outfile_path) == 0:
            osm_outfile_path = osm_infile_path
        is_same_input_output = False
        if osm_outfile_path == osm_infile_path:
            self.osm_output_path = osm_outfile_path + "temp"
            is_same_input_output = True
        else:
            self.osm_output_path = osm_outfile_path

        self.abbr_parser = OsmAbbrParser()
        self.process_osm_file()

        if is_same_input_output:
            if do_bkup:
                file_utils.bkup(osm_outfile_path)
            file_utils.mv(self.osm_output_path, osm_outfile_path)

    def process_osm_file(self):
        """ read input xml file line by line.  where we encounter street element tags, look to rename 
            the 'v' attribute (e.g, street name) with 
        """
        bunch = []
        do_rename = False
        is_inside_way = False
        with open(self.osm_input_path, "r") as r, open(self.osm_output_path, "w") as w:
            for line_num, line in enumerate(r):
                # step 1: check to see if this .osm file has already been renamed
                if not do_rename and "<osm " in line:
                    if not self.attrib in line:
                        line = add_xml_attribute_to_osm_tag(line, line_num)
                        do_rename = True

                # step 2: run rename method(s) for this line in the text (xml) file
                if do_rename:
                    if "addr:street" in line:
                        line = self.process_streetname_str(line, line_num, "addr:street")
                    if is_inside_way:
                        if '<tag k="name"' in line or '<tag k="name_' in line:
                            line = self.process_streetname_str(line, line_num, "way:name")
                        elif '<tag k="alt_name' in line:
                            line = self.process_streetname_str(line, line_num, "way:alt_name")
                        elif '<tag k="old_name' in line:
                            line = self.process_streetname_str(line, line_num, "way:old_name")
                        elif '<tag k="bridge:name' in line:
                            line = self.process_streetname_str(line, line_num, "way:bridge:name")
                        elif '<tag k="description' in line:
                            line = self.process_streetname_str(line, line_num, "way:description")
                        elif '<tag k="destination' in line:
                            line = self.process_streetname_str(line, line_num, "way:destination")
                    if '<way ' in line or '<relation ' in line:
                        is_inside_way = True
                    if '</way>' in line or '</relation>' in line:
                        is_inside_way = False

                    # remove ET xml (type html) side effects, so ending tags look trim & proper
                    if line:
                        line = line.replace(" />", "/>").replace("></tag>", "/>")

                # step 3: buffer write the lines of the file to a new file
                bunch.append(line)
                if len(bunch) == self.bunchsize:
                    w.writelines(bunch)
                    bunch = []
            w.writelines(bunch)

    def process_streetname_str(self, line, line_num, type):
        """ parse line of text into XML and look to rename the v attribute in the tag element """
        ret_val = line

        xml = ET.fromstring(line)
        val = xml.get('v')
        if val:
            if len(val) > 0:
                self.rename_xml_value_attirbute(xml, line_num)
                xml_str = ET.tostring(xml, encoding="UTF-8", method="html")
                ret_val = "    {}\n".format(xml_str)
            else:
                log.warning("{} (line {}) xml element {} found an empty street name value".format(type, line_num, xml.attrib))
        else:
            log.warning("{} (line {}) xml element {} is without a value attribute".format(type, line_num, xml.attrib))

        return ret_val

    def rename_xml_value_attirbute(self, xml, line_num):
        """ rename the 'v' value attirbute in this xml element tag """
        street_name = xml.attrib['v']
        if street_name in self.rename_cache:
            xml.attrib['v'] = self.rename_cache[street_name]
            if line_num % 111 == 0:
                sys.stdout.write(":")
                sys.stdout.flush()
        else:
            rename = self.abbr_parser.to_str(street_name)
            xml.set('v', rename)
            self.rename_cache[street_name] = rename
            if line_num % 111 == 0:
                sys.stdout.write(".")
                sys.stdout.flush()

    @classmethod
    def rename(cls, osm_infile_path, osm_outfile_path=None, do_bkup=True):
        """ 
        """
        ret_val = None
        if osm_outfile_path is None:
            osm_outfile_path = osm_infile_path
        ret_val = OsmRename(osm_infile_path, osm_outfile_path, do_bkup=do_bkup)
        return ret_val


def add_xml_attribute_to_osm_tag(line, line_num, attribute_name="generator", attribute_val=OsmRename.attrib, append=True):
    """ a bit hacky <osm> element editing """
    ret_val = line
    try:
        # import pdb; pdb.set_trace()
        xml = ET.fromstring(line + "</osm>")  # need to fake close elem for ET, since real close is 1000s of lines away
        curr_val = xml.get(attribute_name)
        if append:
            attribute_val = "{}; {}".format(curr_val, attribute_val)
        xml.set(attribute_name, attribute_val)
        ret_val = ET.tostring(xml, encoding="unicode")
        ret_val = ret_val.replace("</osm>", "").replace("/>", ">")
    except Exception as e:
        log.warning("couldn't add attribute {} to xml element on line number {}".format(attribute_name, line_num))
        log.warning(e)
    return ret_val


def main():
    """ cmd line processor """
    from ott.utils.parse.cmdline import osm_cmdline
    p = osm_cmdline.osm_parser_args(prog_name="bin/osm_rename", osm_required=True, out_required=False)
    OsmRename(p.osm, p.output)
