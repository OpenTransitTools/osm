from osmread import parse_file, Way

from ott.utils import json_utils
from ott.utils import date_utils
from ott.utils import file_utils

import logging
logging.basicConfig()
log = logging.getLogger(__file__)


class OsmInfo(object):
    """
    Utility for getting stats on an osm file
    """
    def __init__(self):
        """
        TODO think about rewriting this to simply read file line by line and find latest stamps and count tags...
        will be much faster than osmread on big files...
        """
        self.way_count = 0
        self.highway_count = 0
        self.osm_file = None

        class Last(object):
            timestamp = 0
            changeset = 0
        self.last = Last()

    def __str__(self):
        return json_utils.json_repr(self, pretty_print=True)

    def to_json(self):
        return json_utils.obj_to_dict(self)

    def write_json_file(self, file_path, pretty_print=False):
        json_utils.object_to_json_file(file_path, self, pretty_print)

    def calculate_osm_stats(self, osm_path):
        """ reads the .osm file and captures certain stats like last update and number of ways, etc... 
        """
        log.info("calculating stats for {}".format(osm_path))
        self.osm_file = osm_path

        # import pdb; pdb.set_trace()
        for entity in parse_file(osm_path):
            if isinstance(entity, Way):
                self.way_count += 1
                if 'highway' in entity.tags:
                    self.highway_count += 1
                if entity.timestamp > self.last.timestamp:
                    self.last.timestamp = entity.timestamp
                    if entity.changeset > 0:
                        self.last.changeset = entity.changeset

        self.last.edit_date = date_utils.pretty_date_from_ms(self.last.timestamp * 1000, fmt="%B %d, %Y")
        self.last.file_date = file_utils.file_pretty_date(osm_path, fmt="%B %d, %Y")

        # if available, add the changeset url
        if self.last.changeset > 0:
            self.last.changeset_url = "http://openstreetmap.org/changeset/{}".format(self.last.changeset)

    @classmethod
    def find_osm_files(cls, dir_path):
        ret_val = []
        osm = file_utils.find_files(dir_path, ".osm")
        if osm:
            ret_val.extend(osm)
        pbf = file_utils.find_files(dir_path, ".pbf")
        if pbf:
            ret_val.extend(pbf)
        return ret_val

    @classmethod
    def get_stats_file_path(cls, osm_file, stats_file=None):
        if stats_file is None:
            stats_file = osm_file + "-stats"
        return stats_file

    @classmethod
    def cache_stats(cls, osm_path, stats_file=None, pretty_print=True):
        """ return OSM .osm-stats info json
            will either read the .osm-stats file or create a new stats file calculated via the .osm file
        """
        stats_path = cls.get_stats_file_path(osm_path, stats_file)
        is_stats_good = False

        # step 1: read the .osm-stats cache file (if exists and stats are newer than osm)
        if not file_utils.is_a_newer_than_b(osm_path, stats_path):
            j = json_utils.get_json(stats_path)
            if j.get('way_count') and j.get('highway_count') and j.get('last'):
                is_stats_good = True
                ret_val = j

        # step 2: if .osm-stats don't exists or are out of date, cache them
        if not is_stats_good:
            stats = OsmInfo()
            stats.calculate_osm_stats(osm_path)
            stats_file = cls.get_stats_file_path(osm_path, stats_file)
            stats.write_json_file(stats_file, pretty_print)
            ret_val = stats.to_json()

        return ret_val

    @classmethod
    def get_stats(cls, osm_file, stats_file=None, pretty_print=True):
        """ will either read a cache'd -stats file into memory, or calculate the stats, cache them and then return
            :return dict representing the json stats object
        """
        ret_val = None

        # step 1: validate stats file path
        stats_file = cls.get_stats_file_path(osm_file, stats_file)

        # step 2: if the stats file exists and is newere than the .osm file, try to read it in
        if file_utils.exists(stats_file) and file_utils.is_a_newer_than_b(stats_file, osm_file):
            ret_val = json_utils.get_json(stats_file)

        # step 3: if we don't have stats from a cache'd file, calculate new stats and write them out
        if ret_val is None or len(ret_val) < 2:
            ret_val = cls.cache_stats(osm_file, stats_file, pretty_print)

        # step 4: return the stats as a string
        return ret_val

    @classmethod
    def get_osm_feed_msg(cls, file_path, prefix=" ", suffix="\n", detailed=False):
        """ get osm feed details msg string for the .v log file
        """
        # step 1: get stats and .osm file name
        file_name = file_utils.get_file_name_from_path(file_path)
        stats = OsmInfo.get_stats(file_path)

        # step 2: make up base message with file name and file / last edit dates
        msg = "{}{} : file date = {} -- last OSM update = {}".format(prefix, file_name, stats['last'].get('file_date'), stats['last'].get('edit_date'))

        # step 3: add details like changesets, etc...
        if detailed:
            cs = stats['last'].get('changeset', 0)
            if cs > 111:
                msg = "{}, changeset: {}".format(msg, cs)
                url = stats['last'].get('changeset_url')
                if url:
                    msg = "{} @ {}".format(msg, url)
            else:
                msg = "{} (NOTE: there is no 'changeset' info -- probably Geofabrik data)".format(msg)

        # step 4: end the message and return it
        msg = msg + suffix
        return msg

    @classmethod
    def get_cache_msgs(cls, cache_path='.', def_msg="", detailed=False):
        """
        return message for all OSM feeds in the cache directory
        NOTE: this method could take hours to process, depending upon number & size of .osm files in a directory
        """
        osm_msg = def_msg
        try:
            osm_files = OsmInfo.find_osm_files(cache_path)
            for f in osm_files:
                osm_msg += OsmInfo.get_osm_feed_msg(file_path=f, detailed=detailed)
        except Exception as e:
            log.info(e)
        return osm_msg

    @classmethod
    def print_stats(cls, osm_path):
        """ print stats from input file
        """
        try:
            s = OsmInfo.get_stats(osm_path)
            print json_utils.dict_to_json_str(s, pretty_print=True)
        except Exception as e:
            log.error(e)
            if osm_path.endswith(('.osm', '.xml', '.osm.bz2', '.xml.bz2')) is False:
                log.error("NOTE: your file should end with .osm or .xml")

    @classmethod
    def print_stats_via_config(cls):
        """
        print stats from the .osm file that is config'd in the cache
        """
        from ott.osm.osm_cache import OsmCache
        c = OsmCache()
        cls.print_stats(c.osm_path)

    @classmethod
    def print_stats_via_cmdline(cls):
        # import pdb; pdb.set_trace()
        from ott.utils.parse.cmdline import osm_cmdline
        p = osm_cmdline.osm_parser_args(prog_name='bin/osm_info', osm_required=True)
        OsmInfo.print_stats(p.osm)
        print OsmInfo.get_cache_msgs(p.osm, detailed=True)


def main():
    OsmInfo.print_stats_via_cmdline()

if __name__ == '__main__':
    main()
