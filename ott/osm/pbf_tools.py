from ott.utils import exe_utils
from ott.utils import file_utils
from ott.utils import web_utils
from ott.utils import string_utils

import os
import re
import logging
log = logging.getLogger(__file__)


class PbfTools(object):
    """ manage .pbf files and converters to .osm (xml) files with external tools like osmosis
    """
    cache_dir = None
    osmosis_exe = None

    pbf_url = None
    pbf_name = None
    pbf_path = None

    meta_url = None
    meta_name = None
    meta_path = None

    def __init__(self, cache_dir, osmosis_exe, pbf_url, meta_url):
        """
        """
        # step 1: basic vars
        self.cache_dir = cache_dir
        self.osmosis_exe = osmosis_exe

        # step 2: .pbf (geofabrik source) urls, file paths and name
        self.pbf_url = pbf_url
        self.pbf_name = web_utils.get_name_from_url(self.pbf_url)
        self.pbf_path = string_utils.safe_path_join(self.cache_dir, self.pbf_name)

        # step 3: meta data (geofabrik has an .html file) urls, file paths and name
        self.meta_url = meta_url
        self.meta_name = web_utils.get_name_from_url(self.meta_url)
        self.meta_path = string_utils.safe_path_join(self.cache_dir, self.meta_name)

    def check_osmosis_exe(self):
        """ get the path osmosis binary
            TODO - we should look for system installed osmosis first
            TODO need to check for .exe, them maybe download & install, finally need to test outputs ... make sure they're properly sized and have some necessary elements
        """
        # step 1: see if osmosis binary path looks like windows (for ux or dos, ala c:\\ in path will get you a .bin extension)
        osmosis_exe = self.osmosis_exe
        if not os.path.exists(osmosis_exe) and ":\\" in osmosis_exe:
            osmosis_exe = osmosis_exe + ".bat"

        # step 2: osmosis installed?
        if not os.path.exists(osmosis_exe):
            e = "OSMOSIS {} doesn't exist...".format(osmosis_exe)
            raise Exception(e)
        return osmosis_exe

    def clip_to_bbox(self, input_path, output_path, top, bottom, left, right):
        """ use osmosis to clip a bbox out of a .pbf, and output .osm file
            (file paths derrived by the cache paths & config)
            outputs: both an .osm file and a .pbf file of the clipped area
        """
        osmosis_exe = self.check_osmosis_exe()
        osmosis = "{} --rb {} --bounding-box top={} bottom={} left={} right={} completeWays=true --wx {}"
        osmosis_cmd = osmosis.format(osmosis_exe, input_path, top, bottom, left, right, output_path)
        log.info(osmosis_cmd)
        exe_utils.run_cmd(osmosis_cmd, shell=True)

    def osm_to_pbf(self, osm_path, pbf_path=None):
        """ use osmosis to convert .osm file to .pbf
        """
        if pbf_path is None:
            pbf_path = re.sub('.osm$', '', osm_path) + ".pbf"
        osmosis_exe = self.check_osmosis_exe()
        osmosis = '{} --read-xml {} --write-pbf {}'
        osmosis_cmd = osmosis.format(osmosis_exe, osm_path, pbf_path)
        exe_utils.run_cmd(osmosis_cmd, shell=True)

    def pbf_to_osm(self, osm_path, pbf_path=None):
        """ use osmosis to convert .pbf to .osm file
        """
        if pbf_path is None:
            pbf_path = re.sub('.osm$', '', osm_path) + ".pbf"
        osmosis_exe = self.check_osmosis_exe()
        osmosis = '{} --read-pbf {} --write-xml {}'
        osmosis_cmd = osmosis.format(osmosis_exe, pbf_path, osm_path)
        exe_utils.run_cmd(osmosis_cmd, shell=True)

    def download_pbf(self):
        log.info("wget {} to {}".format(self.pbf_url, self.pbf_path))
        file_utils.bkup(self.pbf_path)
        web_utils.wget(self.pbf_url, self.pbf_path)
        if self.meta_url:
            web_utils.wget(self.meta_url, self.meta_path)

    def is_configured(self):
        return len(self.pbf_name) > 0 and len(self.pbf_path) > 0
