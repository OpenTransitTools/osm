from ott.utils import exe_utils
from ott.utils import file_utils
from ott.utils import web_utils
from ott.utils import string_utils

import os
import re
import logging
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)


class PbfTools(object):
    """ manage .pbf files and converters to .osm (xml) files with external tools like osmosis
    """
    cache_dir = None
    osmosis_exe = None

    def __init__(self, cache_dir=None, osmosis_exe=None):
        this_dir = file_utils.get_module_dir(self.__class__)
        if cache_dir is None:
            cache_dir = os.path.join(this_dir, 'cache')
        if osmosis_exe is None:
            osmosis_exe = os.path.join(this_dir, 'osmosis/bin/osmosis')

        self.filter_transit_tagtransform_file = os.path.join(this_dir, 'osmosis/tagtransform.xml')
        self.cache_dir = cache_dir
        self.osmosis_exe = osmosis_exe

    def check_osmosis_exe(self):
        """
        get the path osmosis binary
        TODO - we should look for system installed osmosis first
        TODO need to check for .exe, them maybe download & install, finally need to test outputs ... make sure they're properly sized and have some necessary elements
        """
        # step 1: see if osmosis binary path looks like windows (for ux or dos, ala c:\\ in path will get you a .bin extension)
        osmosis_exe = self.osmosis_exe
        if not os.path.exists(osmosis_exe) and ":\\" in osmosis_exe:
            osmosis_exe = osmosis_exe + ".bat"

        # step 2: osmosis installed?
        if not os.path.exists(osmosis_exe):
            e = "OSMOSIS {} doesn't exist...maybe set it via a cmdline params (osmos_exe)".format(osmosis_exe)
            raise Exception(e)
        return osmosis_exe

    @classmethod
    def name_path_from_url(cls, url, cache_dir):
        name = web_utils.get_name_from_url(url)
        path = string_utils.safe_path_join(cache_dir, name)
        return name, path

    @classmethod
    def path_from_url(cls, url, cache_dir):
        name, path = cls.name_path_from_url(url, cache_dir)
        return path

    def download_pbf(self, pbf_url, meta_url=None):
        pbf_path = self.path_from_url(pbf_url, self.cache_dir)
        log.info("wget {} to {}".format(pbf_url, pbf_path))
        file_utils.bkup(pbf_path)
        web_utils.wget(pbf_url, pbf_path)
        try:
            if meta_url:
                meta_path = self.path_from_url(meta_url, self.cache_dir)
                web_utils.wget(meta_url, meta_path)
        except Exception as e:
            log.info(e)

    def clip_to_bbox(self, input_path, output_path, top, bottom, left, right, crel="completeRelations=yes", cway="completeWays=yes"):
        """
        use osmosis to clip a bbox out of a .pbf, and output .osm file
        (file paths derrived by the cache paths & config)
        outputs: both an .osm file and a .pbf file of the clipped area
        """
        in_type = "xml" if input_path.endswith(".osm") else "pbf"
        out_type = "xml" if output_path.endswith(".osm") else "pbf"

        osmosis_exe = self.check_osmosis_exe()
        osmosis = "{} --read-{} {} --bounding-box top={} bottom={} left={} right={} {} {} clipIncompleteEntities=yes --write-{} {}"
        osmosis_cmd = osmosis.format(osmosis_exe, in_type, input_path, top, bottom, left, right, crel, cway, out_type, output_path)
        log.info(osmosis_cmd)
        exe_utils.run_cmd(osmosis_cmd, shell=True)

    def pbf_to_osm(self, pbf_path, osm_path=None):
        """ use osmosis to convert .pbf to .osm file
        """
        if osm_path is None:
            osm_path = re.sub('.pbf$', '.osm', osm_path)
        osmosis_exe = self.check_osmosis_exe()
        osmosis = '{} --read-pbf {} --write-xml {}'
        osmosis_cmd = osmosis.format(osmosis_exe, pbf_path, osm_path)
        exe_utils.run_cmd(osmosis_cmd, shell=True)

    def osm_to_pbf(self, osm_path, pbf_path=None):
        """ use osmosis to convert .osm file to .pbf
        """
        if pbf_path is None:
            pbf_path = osm_path + ".pbf"
        osmosis_exe = self.check_osmosis_exe()
        osmosis = '{} --read-xml {} --write-pbf {}'
        osmosis_cmd = osmosis.format(osmosis_exe, osm_path, pbf_path)
        exe_utils.run_cmd(osmosis_cmd, shell=True)

    def cull_transit_from_osm(self, osm_in_path, osm_out_path=None):
        """
        use osmosis and the tag file to remove transit information
        """
        if osm_out_path is None:
            osm_out_path = re.sub('.osm$', '_cull_transit.osm', osm_in_path)
        osmosis_exe = self.check_osmosis_exe()
        osmosis = '{} --read-xml {} --tag-transform {} --tf reject-node todo=delete_me --tf reject-way todo=delete_me --tf reject-relation todo=delete_me --write-xml {}'
        osmosis_cmd = osmosis.format(osmosis_exe, osm_in_path, self.filter_transit_tagtransform_file, osm_out_path)
        exe_utils.run_cmd(osmosis_cmd, shell=True)
        return osm_out_path

    @classmethod
    def osm_to_pbf_cmdline(cls):
        #import pdb; pdb.set_trace()
        from ott.utils.parse.cmdline import osm_cmdline
        p = osm_cmdline.osm_parser_args(prog_name='bin/osm_to_pbf', osm_required=True)
        pbf = PbfTools(osmosis_exe=p.osmosis_exe)
        pbf.osm_to_pbf(p.osm, p.pbf)

    @classmethod
    def cull_transit_cmdline(cls):
        from ott.utils.parse.cmdline import osm_cmdline
        p = osm_cmdline.osm_parser_args(prog_name='bin/osm_cull_transit', osm_required=True)
        pbf = PbfTools(osmosis_exe=p.osmosis_exe)
        pbf.cull_transit_from_osm(p.osm)
