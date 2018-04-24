from osmread import parse_file, Way

from ott.utils import json_utils
from ott.utils import date_utils
from ott.utils import file_utils

import logging
logging.basicConfig()
log = logging.getLogger(__file__)

class NodeInfo(object):
    node = None
    node_id = None
    tag_name = None
    tag_value = None


class FindNodes(object):
    """
    Utility for finding OSM elements
    """
    def __init__(self, osm_file):
        self.osm_file = osm_file
        self.osm_path = osm_file # TODO

    @classmethod
    def find(cls, osm_file, tag_name, value_value=('yes', 'true')):
        """ will find nodes with """
        pass


def main():
    # import pdb; pdb.set_trace()
    from ott.utils.parse.cmdline import osm_cmdline
    p = osm_cmdline.osm_parser_args(prog_name='bin/osm_find', osm_required=True)
    n = FindNodes.find(p.osm, p.tag_name)
    print n


if __name__ == '__main__':
    main()
