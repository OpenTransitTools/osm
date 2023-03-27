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
    pbf_name = None
    pbf_path = None

    osm_carto_name = None
    osm_carto_path = None

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
        self.pbf_name = string_utils.safe_append(name, ".osm.pbf")
        self.pbf_path = string_utils.safe_path_join(self.cache_dir, self.pbf_name)

        self.osm_carto_name = string_utils.safe_append(name, "-carto.osm")
        self.osm_carto_path = string_utils.safe_path_join(self.cache_dir, self.osm_carto_name)

        # step 3: pbf tools (for downloading new data from geofabrik, as well as converting the .pbf to our .osm)
        osmosis_path = self.config.get('osmosis_path', def_val=os.path.join(self.this_module_dir, 'osmosis', 'bin', 'osmosis'))
        self.pbf_tools = PbfTools(self.cache_dir, osmosis_path)

    def check_cached_osm(self, force_update=False, force_postprocessing=False):
        """
        if OSM .pbf file is out of date, download a new one.
        convert .pbf to .osm if .pbf file is newer than .osm file
        :return indication if updated
        """
        # import pdb; pdb.set_trace()
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
                self.clip_region_to_bbox(pbf_path, rename=True)
                is_updated = True
            else:
                is_updated = False

        # step 3: .osm file check
        if not file_utils.is_min_sized(self.osm_path, min_size):
            e = "OSM file {} is not big enough".format(self.osm_path)
            raise Exception(e)

        # step 4: other OSM processing steps on a new (fresh) .osm file
        if is_updated or force_postprocessing:
            OsmInfo.cache_stats(self.osm_path)
            self.pbf_tools.osm_to_pbf(self.osm_path)
            self.pbf_tools.osm_to_pbf(self.osm_carto_path)
            # note: cull transit file is used for Pelias (no confusing stop / station overlap)
            osm_cull_transit_path = self.pbf_tools.cull_transit_from_osm(self.osm_path)
            self.pbf_tools.osm_to_pbf(osm_cull_transit_path)
            self.other_exports()
            self.intersections_export()
            self.osm_2_pgsql()

        return is_updated

    def clip_region_to_bbox(self, pbf_path="us-west-latest.osm.pbf", rename=False):
        """
        we clip 2 files out of the source .pbf file
        first, we clip a -carto.osm directly from the .pbf source, and then from that a non-carto osm file.

        the -carto.osm file calls osmosis with --completeRelations=true and --completeWays=true ... without those
        flags, the resulting .osm file will probably lack complete rivers, parks, boundaries and other polygonal data.
        Having those flags can lead to much larger extents (e.g., NW Oregon/SW Wash file will extend to Montana)

        The non-carto file is clipped strictly to the bbox. It's better use is the trip planner, geocoder, etc...
        """
        self.clip_to_bbox(pbf_path, self.osm_carto_path, self.top, self.bottom, self.left, self.right, complete=True)
        if rename:
            OsmRename.rename(self.osm_carto_path, do_bkup=False)
        self.clip_to_bbox(self.osm_carto_path, self.osm_path, self.top, self.bottom, self.left, self.right)

    def clip_to_bbox(self, in_path, out_path, top, bottom, left, right, complete=False):
        """ clip to bbox ... good for cmdline """
        if not file_utils.exists(in_path):
            in_path = os.path.join(self.cache_dir, in_path)

        if complete:
            self.pbf_tools.clip_to_bbox(in_path, out_path, top, bottom, left, right)
        else:
            self.pbf_tools.clip_to_bbox(in_path, out_path, top, bottom, left, right, crel="", cway="")

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
        intersection_file = self.config.get_json('intersection_out_file')
        if intersection_file:
            csv_path = os.path.join(self.cache_dir, intersection_file)
            log.info("exporting intersections to file {}".format(csv_path))
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
    def check_osm_file_against_cache(cls, app_dir, force_update=False, use_pbf=False):
        """
        check the .osm file in this cache against an osm file in another app's directory (e.g., OTP folder)
        """
        ret_val = False
        try:
            osm = OsmCache()
            if use_pbf:
                name = osm.pbf_name
                path = osm.pbf_path
            else:
                name = osm.osm_name
                path = osm.osm_path

            app_osm_path = os.path.join(app_dir, name)
            refresh = file_utils.is_a_newer_than_b(path, app_osm_path, offset_minutes=10)
            if refresh or force_update:
                # step a: copy the .osm file to this foreign cache
                log.info("cp {} to {}".format(name, app_dir))
                osm.cp_cached_file(name, app_dir)

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
        generate intersections .csv from cached .osm file

        :example: bin/osm-intersections -o ott/osm/cache/hillsboro.osm | grep -i cherr
        :see: https://ws-st.trimet.org/pelias/v1/search?sources=osm,oa,transit&text=NE%20Century%20%26%20NE%20Cherry
        """
        OsmCache().intersections_export()

    @classmethod
    def osm_2_pgsql(cls):
        from .osm2pgsql.osm2pgsql import Osm2pgsql
        Osm2pgsql().run()

    @classmethod
    def exports(cls):
        """
        generate other .osm file(s)
        :exmple:  bin/osm_other_exports hills
        """
        import sys
        name = sys.argv[1] if len(sys.argv) > 1 else None
        c = OsmCache()
        c.other_exports(name)


def clip_from_pbf():
    """ for command line clipping of planet (or regional) .osm.pbf into .osm file """
    o = OsmCache()
    o.clip_region_to_bbox()
    return o


def clip_rename():
    """ for command line clipping of planet (or regional) .osm.pbf into custom .osm + rename and stats """
    o = clip_from_pbf()
    OsmRename.rename(o.osm_path, do_bkup=False)
    OsmInfo.cache_stats(o.osm_path)
