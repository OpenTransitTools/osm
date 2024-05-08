"""
    Credit goes to https://stackoverflow.com/users/684592/kotaro
    https://stackoverflow.com/questions/14716497/how-can-i-find-a-list-of-street-intersections-from-openstreetmap-data?rq=1
"""
import os
import sys
import csv
import itertools

from ott.utils import file_utils

try:
    from xml.etree import cElementTree as ET
except ImportError as e:
    from xml.etree import ElementTree as ET

import logging
log = logging.getLogger(__file__)


tot_proc = 0
num_proc = 0


def extract_intersections(osm):
    """
    This method reads the passed osm file (xml) and finds intersections (nodes that are shared by two or more roads)
    :param osm: An osm file or a string from get_osm()
    """
    ret_val = {}

    def get_names_from_way_list(way_list):
        # import pdb; pdb.set_trace()
        global num_proc
        global tot_proc
        ret_val = {}
        try:
            sys.stderr.write('.')
            for w in way_list:
                num_proc += 1
                tot_proc += 1
                for c in w:
                    if c.tag == 'tag' and 'k' in c.attrib and (c.attrib['k'] == 'name' or c.attrib['k'] == 'alt_name'):
                        if 'v' in c.attrib and len(c.attrib['v']) > 0:
                            ret_val[c.attrib['v']] = c.attrib['v']
            sys.stderr.write('.')
        except Exception as e:
            log.warning(e)
        return ret_val

    # step 1: parse either XML string or file
    if '<' in osm and '>' in osm:
        tree = ET.fromstring(osm)
        children = tree.getchildren()
    else:
        tree = ET.parse(osm)
        root = tree.getroot()
        children = root.getchildren()

    log.info("number of osm nodes read in: {}".format(len(children)))

    counter = {}
    road_ways = {}
    for i, child in enumerate(children):
        if child.tag == 'way':
            is_road = False

            # NOTE: updated 5/2024 ... missing 'trunk' ala MLK Blvd, and also added busway, ped and road
            road_types = ('trunk', 'primary', 'secondary', 'residential', 'tertiary', 'busway', 'pedestrian', 'road', 'unclassified')
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

                if i % 100000 == 0:
                    sys.stderr.write('.')

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
                if i % 5000 == 0:
                    sys.stderr.write('.')

    log.info("Number of RAW nodes: {}".format(len(intersection_nodes)))
    for i, n in enumerate(intersection_nodes):
        z = n.attrib['id']
        names_d = get_names_from_way_list(road_ways[z])
        names = names_d.values()
        if len(names) < 2:
            # print(names)
            continue

        coordinate = n.attrib['lat'] + ',' + n.attrib['lon']
        two_names_list = itertools.combinations(names, 2)
        for t in two_names_list:
            ret_val[t] = coordinate
        if i % 5000 == 0:
            sys.stderr.write('.')

    log.info("Number of NAMED (output) intersection nodes: {}".format(len(ret_val)))
    return ret_val


def intersection_tuple_to_record(names_tuple, coord_string, separator='&', def_val={}):
    """
    turns an intersection record created above in extract_intersections() into a dict

    names_tuple = ('SW Tyrol St', 'SW 18th Pl')  --- this is the i from looping intersections
    coord_string = '45.487563,-122.6989328' --- this is the intersections[i]
    """
    ret_val = def_val
    try:
        ret_val['name'] = "{} {} {}".format(names_tuple[0], separator, names_tuple[1])
        ret_val['street'] = names_tuple[0]
        ret_val['cross_street'] = names_tuple[1]
        ll = coord_string.split(',')
        ret_val['lon'] = float(ll[1])
        ret_val['lat'] = float(ll[0])
        valid = True
    except Exception as e:
        valid = False
    return ret_val, valid


def to_csv(intersections, csv_file_path, source='transit'):
    """
    turn list returned by extract_intersections() into a .csv file
    note: the output format follows pelias transit .csv format (Oct 2018)
          format may change for generic pelias .csv reader
    """
    with open(csv_file_path, mode='w') as csv_file:
        fieldnames = ['id', 'name', 'street', 'cross_street', 'address', 'zipcode', 'lon', 'lat', 'layer_id', 'source']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for i, names in enumerate(intersections):
            rec = {'id': i+1, 'layer_id': 'intersection', 'source': source}
            rec, is_valid = intersection_tuple_to_record(names, intersections[names], def_val=rec)
            if is_valid:
                writer.writerow(rec)


def osm_to_intersections(osm_file, csv_output_path):
    """ the 'main' routine to collect intersection from input .osm file and output to a csv file """
    intersections = extract_intersections(osm_file)
    if csv_output_path:
        to_csv(intersections, csv_output_path)
    return intersections


def main():
    def get_test_data():
        dir = file_utils.get_file_dir(__file__)
        dir = file_utils.get_parent_dir(dir)
        file = os.path.join(dir, 'tests', 'data', 'portland.osm')
        return file

    def cmd_parser(name='bin/osm-intersetions'):
        from ott.utils.parse.cmdline import osm_cmdline
        parser = osm_cmdline.osm_parser(prog_name=name, osm_required=False)
        parser.add_argument(
            '--pelias',
            '--csv',
            '-c',
            required=False,
            help=".csv file output (Pelias format)"
        )
        return parser.parse_args()

    p = cmd_parser()
    osm_file = p.osm
    if osm_file is None:
        osm_file = get_test_data()

    intersections = osm_to_intersections(osm_file, p.pelias)
    if p.pelias is None:
        for i in intersections:
            #import pdb; pdb.set_trace()
            print(i, intersections[i])


if __name__ == '__main__':
    main()
