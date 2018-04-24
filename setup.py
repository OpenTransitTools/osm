import os
import sys
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'ott.utils',
    'psycopg2',
    'sqlalchemy<1.2',
    'simplejson',
    'osmread',
    'protobuf',
    'pyparsing',
    'imposm',
    'shapely',
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
        osm_update = ott.osm.osm_cache:OsmCache.load
        osm_to_pgsql = ott.osm.osm2pgsql.osm2pgsql:main
        osm_stats_cfg = ott.osm.osm_info:OsmInfo.print_stats_via_config
        osm_stats = ott.osm.osm_info:main
        osm_rename = ott.osm.rename.osm_rename:main
        osm_intersections = ott.osm.intersections.osm_to_intersections:main
        osm_abbr_tester = ott.osm.tests.osm_abbr_tester:main
    """,
)
