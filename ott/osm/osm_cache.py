from ott.utils import file_utils
from ott.utils import object_utils
from ott.utils import string_utils
from ott.utils.cache_base import CacheBase

from .pbf_tools import PbfTools
from .stats.osm_info import OsmInfo
from .rename.osm_rename import OsmRename
from .intersections.osm_to_intersections import osm_to_intersections

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
        osmosis_path = self.config.get('osmosis_path', def_val=os.path.join(self.this_module_dir, 'osmosis', 'bin', 'osmosis'))
        self.pbf_tools = PbfTools(self.cache_dir, osmosis_path)

    def check_cached_osm(self, force_update=False, force_postprocessing=False):
        """
        if OSM .pbf file is out of date, download a new one.
        convert .pbf to .osm if .pbf file is newer than .osm file
        :return indication if updated
        """
        assert self.is_configured() is True

        is_updated = force_update

        min_size = self.config.get_int('min_size', def_val=100000)
        pbf_url = self.config.get('pbf_url')
        pbf_path = self.pbf_tools.path_from_url(pbf_url, self.cache_dir)

        # step 1: download new osm pbf file if it's not new
        fresh = self.is_fresh_in_cache(pbf_path)
        sized = file_utils.is_min_sized(pbf_path, min_size)
        if force_update or not fresh or not sized:
            if not sized: log.info("PBF file {} too small ... UPDATING.".format(pbf_path))
            elif not fresh: log.info("PBF file {} too old ... UPDATING.".format(pbf_path))
            meta_url = self.config.get('meta_url')
            self.pbf_tools.download_pbf(pbf_url, meta_url)
            is_updated = True

        # step 2: .pbf to .osm
        if not file_utils.is_min_sized(pbf_path, min_size):
            log.warn("OSM PBF file {} is not big enough".format(pbf_path))
        else:
            fresh = self.is_fresh_in_cache(self.osm_path)
            sized = file_utils.is_min_sized(self.osm_path, min_size)
            pbf_newer = file_utils.is_a_newer_than_b(pbf_path, self.osm_path, offset_minutes=10)
            if is_updated or pbf_newer or not fresh or not sized:
                self.clip_to_bbox(pbf_path, self.osm_path, self.top, self.bottom, self.left, self.right)
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
            cull_osm = self.pbf_tools.cull_transit_from_osm(self.osm_path)
            self.pbf_tools.osm_to_pbf(cull_osm)
            self.other_exports()
            self.intersections_export()
        return is_updated

    def clip_to_bbox(self, pbf_path="us-west-latest.osm.pbf", osm_path=None, top=None, bottom=None, left=None, right=None):
        """ clip to bbox ... good for cmdline """
        if not file_utils.exists(pbf_path):
            pbf_path = os.path.join(self.cache_dir, pbf_path)

        osm_path = osm_path if osm_path else self.osm_path
        top = top if top else self.top
        bottom = bottom if bottom else self.bottom
        left = left if left else self.left
        right = right if right else self.right
        self.pbf_tools.clip_to_bbox(pbf_path, osm_path, top, bottom, left, right)

    def other_exports(self, name=None):
        """
        export other .osm files
        """
        exports = self.config.get_json('other_exports')
        for e in exports:
            if name and name not in e['out']:
                continue
            in_path = os.path.join(self.cache_dir, e['in'])
            out_path = os.path.join(self.cache_dir, e['out'])
            top, bottom, left, right = self.config.get_bbox(e['bbox'])
            self.clip_to_bbox(in_path, out_path, top, bottom, left, right)

    def intersections_export(self):
        """
        generate intersections .csv from the configured main .osm file (e.g., or-wa.osm)
        """
        intersections = self.config.get_json('intersections')
        if intersections:
            csv_path = os.path.join(self.cache_dir, intersections)
            osm_to_intersections(self.osm_path, csv_path)

    def is_configured(self):
        return len(self.osm_name) > 0 and len(self.osm_path) > 0

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
        except Exception as e:
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

    @classmethod
    def intersections_cache(cls):
        """
        generate .csv from cached .osm file
        """
        c = OsmCache()
        c.intersections_export()

    @classmethod
    def exports(cls):
        """
        generate other .osm file(s)
        :exmple:  bin/osm_other_exports hills
        :example: bin/osm_intersections -o ott/osm/cache/hillsboro.osm | grep -i cherr
        :see: https://ws-st.trimet.org/pelias/v1/search?sources=osm,oa,transit&text=NE%20Century%20%26%20NE%20Cherry
        """
        import sys
        name = sys.argv[1] if len(sys.argv) > 1 else None
        c = OsmCache()
        c.other_exports(name)


def clip_from_pbf():
    """ for command line clipping """
    # todo: cmd line parser
    o = OsmCache()
    o.clip_to_bbox()
