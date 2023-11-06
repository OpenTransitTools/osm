import os
import sys
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'ott.utils',
    'simplejson',
    'shapely',
    'pyparsing',
    'sqlalchemy == 1.4.49',
    'psycopg2-binary',
    'protobuf',
    'osmread',
]

extras_require = dict(
    dev=[],
)

setup(
    name='ott.osm',
    version='0.1.0',
    description='Open Transit Tools - OTT Osm',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
    ],
    author="Open Transit Tools",
    author_email="info@opentransittools.org",
    dependency_links=[
        'git+https://github.com/dezhin/osmread.git#egg=osmread-0.3',
        'git+https://github.com/OpenTransitTools/utils.git#egg=ott.utils-0.1.0',
    ],
    license="Mozilla-derived (http://opentransittools.com)",
    url='http://opentransittools.com',
    keywords='ott, osm, otp, gtfs, gtfsdb, data, database, services, transit',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    extras_require=extras_require,
    tests_require=requires,
    test_suite="ott.osm.tests",
    # find ott | grep py$ | xargs grep "def.main"
    entry_points="""
        [console_scripts]
        osm_clip_from_pbf = ott.osm.osm_cache:clip_from_pbf
        osm_clip_rename = ott.osm.osm_cache:clip_rename
        osm_update = ott.osm.osm_cache:OsmCache.load
        osm_to_pgsql = ott.osm.osm2pgsql.osm2pgsql:main
        osm_to_pbf = ott.osm.pbf_tools:PbfTools.osm_to_pbf_cmdline
        osm_cull_transit = ott.osm.pbf_tools:PbfTools.cull_transit_cmdline
        osm_stats = ott.osm.stats.osm_info:OsmInfo.print_stats_via_cmdline
        osm_stats_cfg = ott.osm.stats.osm_info:OsmInfo.print_stats_via_config
        osm_rename = ott.osm.rename.osm_rename:main
        osm_make_raw = ott.osm.osm_cache:make_raw_osm
        osm_other_exports = ott.osm.osm_cache:OsmCache.exports
        osm_abbr_tester = ott.osm.tests.osm_abbr_tester:main
        osm-intersections = ott.osm.intersections.osm_to_intersections:main
        osm-intersections_cache = ott.osm.osm_cache:OsmCache.intersections_cache
    """,
)
