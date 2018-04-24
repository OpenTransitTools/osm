from ott.utils import file_utils
from ott.utils import object_utils
from ott.utils import string_utils
from ott.utils.cache_base import CacheBase

from .pbf_tools import PbfTools
from .stats.osm_info import OsmInfo
from .rename.osm_rename import OsmRename

import os
import logging
log = logging.getLogger(__file__)


class OsmCache(CacheBase):
    """ Does a 'smart' cache of a gtfs file
         1. it will look to see if a gtfs.zip file is in the cache, and download it and put it in the cache if not
         2. once cached, it will check to see that the file in the cache is the most up to date data...
    """
    osm_name = None
    osm_path = None

    pbf_tools = None

    top = None
    bottom = None
    left = None
    right = None

    def __init__(self):
        """ check osm cache
        """
        super(OsmCache, self).__init__(section='osm')

        # step 1: cache expire and bbox settings from config
        self.cache_expire = self.config.get_int('cache_expire', def_val=self.cache_expire)
        self.top, self.bottom, self.left, self.right = self.config.get_bbox('bbox')

        # step 2: output .osm file name and full (cache) directory path
        name = self.config.get('name')
        self.osm_name = string_utils.safe_append(name, ".osm")
        self.osm_path = string_utils.safe_path_join(self.cache_dir, self.osm_name)

        # step 3: pbf tools (for downloading new data from geofabrik, as well as converting the .pbf to our .osm)
        pbf_url = self.config.get('pbf_url')
        meta_url = self.config.get('meta_url')
        self.pbf_tools = PbfTools(self.cache_dir, self.this_module_dir, pbf_url, meta_url)

    def check_cached_osm(self, force_update=False, force_postprocessing=False):
        """
        if OSM .pbf file is out of date, download a new one.
        convert .pbf to .osm if .pbf file is newer than .osm file
        :return indication if updated
        """
        assert self.is_configured() is True

        is_updated = force_update

        min_size = self.config.get_int('min_size', def_val=100000)

        # step 1: download new osm pbf file if it's not new
        fresh = self.is_fresh_in_cache(self.pbf_tools.pbf_path)
        sized = file_utils.is_min_sized(self.pbf_tools.pbf_path, min_size)
        if force_update or not fresh or not sized:
            self.pbf_tools.download_pbf()
            is_updated = True

        # step 2: .pbf to .osm
        if not file_utils.is_min_sized(self.pbf_tools.pbf_path, min_size):
            log.warn("OSM PBF file {} is not big enough".format(self.pbf_tools.pbf_path))
        else:
            fresh = self.is_fresh_in_cache(self.osm_path)
            sized = file_utils.is_min_sized(self.osm_path, min_size)
            pbf_newer = file_utils.is_a_newer_than_b(self.pbf_tools.pbf_path, self.osm_path, offset_minutes=10)
            if is_updated or pbf_newer or not fresh or not sized:
                self.pbf_tools.clip_to_bbox(self.pbf_tools.pbf_path, self.osm_path, self.top, self.bottom, self.left, self.right)
                is_updated = True
            else:
                is_updated = False

        # step 3: .osm file check
        if not file_utils.is_min_sized(self.osm_path, min_size):
            e = "OSM file {} is not big enough".format(self.osm_path)
            raise Exception(e)

        # step 4: other OSM processing steps on a new (fresh) .osm file
        if is_updated or force_postprocessing:
            OsmRename.rename(self.osm_path, do_bkup=False)
            OsmInfo.cache_stats(self.osm_path)
            self.pbf_tools.osm_to_pbf(self.osm_path)
            self.other_exports()
        return is_updated

    def other_exports(self):
        """ export other .osm files
        """
        exports = self.config.get_json('other_exports')
        for e in exports:
            in_path = os.path.join(self.cache_dir,  e['in'])
            out_path = os.path.join(self.cache_dir, e['out'])
            top, bottom, left, right = self.config.get_bbox(e['bbox'])
            self.pbf_tools.clip_to_bbox(in_path, out_path, top, bottom, left, right)

    def is_configured(self):
        return len(self.osm_name) > 0 and len(self.osm_path) > 0 and self.pbf_tools.is_configured()

    def get_bbox(self, format='str'):
        """
        bbox = left,bottom,right,top
        bbox = min Longitude , min Latitude , max Longitude , max Latitude
        """
        if format == 'str':
            "left: {}, bottom: {}, right: {}, top: {}".format(self.left, self.bottom, self.right, self.top)
        elif format == 'll':
           "min Lon: {}, min Lat: {}, max Lon: {}, max Lat: {}".format(self.left, self.bottom, self.right, self.top)
        else:
            "[{}, {}, {}, {}]".format(self.left, self.bottom, self.right, self.top)
        return ret_val

    @classmethod
    def check_osm_file_against_cache(cls, app_dir, force_update=False):
        """
        check the .osm file in this cache against an osm file in another app's directory (e.g., OTP folder)
        """
        ret_val = False
        try:
            osm = OsmCache()
            app_osm_path = os.path.join(app_dir, osm.osm_name)
            refresh = file_utils.is_a_newer_than_b(osm.osm_path, app_osm_path, offset_minutes=10)
            if refresh or force_update:
                # step a: copy the .osm file to this foreign cache
                log.info("cp {} to {}".format(osm.osm_name, app_dir))
                osm.cp_cached_file(osm.osm_name, app_dir)

                # step b: copy the stats file to this foreign cache
                cache_file = OsmInfo.get_stats_file_path(osm.osm_name)
                osm.cp_cached_file(cache_file, app_dir)
                ret_val = True
        except Exception, e:
            log.warn(e)
        return ret_val

    @classmethod
    def update(cls, force_update, force_postprocessing=False):
        """ check OSM for freshness
        """
        # import pdb; pdb.set_trace()
        osm = OsmCache()
        ret_val = osm.check_cached_osm(force_update, force_postprocessing)
        return ret_val

    @classmethod
    def load(cls):
        """ run the load routine
        """
        ret_val = cls.update(force_update=object_utils.is_force_update())
        return ret_val
