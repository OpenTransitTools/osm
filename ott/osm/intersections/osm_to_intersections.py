"""
    Credit goes to https://stackoverflow.com/users/684592/kotaro
    https://stackoverflow.com/questions/14716497/how-can-i-find-a-list-of-street-intersections-from-openstreetmap-data?rq=1
"""
import os
import sys
import itertools

from ott.utils import file_utils

try:
    from xml.etree import cElementTree as ET
except ImportError, e:
    from xml.etree import ElementTree as ET


tot_proc = 0
num_proc = 0
def get_names_from_way_list(way_list):
    #import pdb; pdb.set_trace()
    global num_proc
    global tot_proc
    ret_val = {}
    try:
        for w in way_list:
            num_proc += 1
            tot_proc += 1
            for c in w:
                if c.tag == 'tag' and 'k' in c.attrib and c.attrib['k'] == 'name':
                    if 'v' in c.attrib and len(c.attrib['v']) > 0:
                        ret_val[c.attrib['v']] = c.attrib['v']
    except Exception as e:
        pass
    return ret_val


def extract_intersections(osm):
    """
    This method reads the passed osm file (xml) and finds intersections (nodes that are shared by two or more roads)
    :param osm: An osm file or a string from get_osm()
    """
    ret_val = {}

    # step 1: parse either XML string or file
    if '<' in osm and '>' in osm:
        tree = ET.fromstring(osm)
        children = tree.getchildren()
    else:
        tree = ET.parse(osm)
        root = tree.getroot()
        children = root.getchildren()

    sys.stderr.write('OSM NODES READ: {}\n'.format(len(children)))

    counter = {}
    road_ways = {}
    for child in children:
        if child.tag == 'way':
            is_road = False

            # TODO: make road types configurable ? , 'service'
            road_types = ('primary', 'secondary', 'residential', 'tertiary')
            for item in child:
                if item.tag == 'tag' and item.attrib['k'] == 'highway' and item.attrib['v'] in road_types:
                    is_road = True
                    break

            if is_road:
                for item in child:
                    if item.tag == 'nd':
                        nd_ref = item.attrib['ref']
                        if nd_ref not in counter:
                            counter[nd_ref] = 0
                        counter[nd_ref] += 1
                        if nd_ref not in road_ways:
                            road_ways[nd_ref] = []
                        road_ways[nd_ref].append(child)

    # Find nodes that are shared with more than one way, which might correspond to intersections
    #intersections = filter(lambda x: counter[x] > 1, counter)
    #sys.stderr.write('INtERSECTIONS READ: {}\n'.format(len(intersections)))

    # import pdb; pdb.set_trace()
    intersection_nodes = []
    for i, child in enumerate(children):
        if child.tag == 'node':
            z = child.attrib['id']
            n = counter.get(z)
            if n and n > 1:
                intersection_nodes.append(child)
        if i % 100000 == 0:
            sys.stderr.write('#')

    sys.stderr.write('\n\nINERSECTION NODES: {}\n'.format(len(intersection_nodes)))

    for i, n in enumerate(intersection_nodes):
        z = n.attrib['id']
        names_d = get_names_from_way_list(road_ways[z])
        names = names_d.values()
        if len(names) < 2:
            # print names
            pass
        else:
            coordinate = n.attrib['lat'] + ',' + n.attrib['lon']
            two_names_list = itertools.combinations(names, 2)
            for t in two_names_list:
                ret_val[t] = coordinate
        if i % 5000 == 0: sys.stderr.write('#')

    """
    print "num raw intersections: {}, num named intersections: {}".format(raw_intersection_count, len(ret_val))
    """
    return ret_val


def get_test_data():
    dir = file_utils.get_file_dir(__file__)
    dir = file_utils.get_parent_dir(dir)
    file = os.path.join(dir, 'tests', 'data', 'portland.osm')
    return file


def main():
    from ott.utils.parse.cmdline import osm_cmdline
    p = osm_cmdline.osm_parser_args(prog_name='bin/osm_intersetions', osm_required=True)
    osm_file = p.osm
    if osm_file is None:
        osm_file = get_test_data()

    intersections = extract_intersections(osm_file)
    for i in intersections:
        print i, intersections[i]


if __name__ == '__main__':
    main()
