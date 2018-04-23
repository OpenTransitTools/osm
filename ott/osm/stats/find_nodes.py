from osmread import parse_file, Way

from ott.utils import json_utils
from ott.utils import date_utils
from ott.utils import file_utils

import logging
logging.basicConfig()
log = logging.getLogger(__file__)


class FindNodes(object):
    """
    Utility for finding OSM elements
    """
    def __init__(self):
        self.way_count = 0
        self.highway_count = 0




def main():
    # import pdb; pdb.set_trace()
    from ott.utils.parse.cmdline import osm_cmdline
    p = osm_cmdline.osm_parser_args(prog_name='bin/osm_find', osm_required=True)
    OsmInfo.print_stats(p.osm)


if __name__ == '__main__':
    main()
