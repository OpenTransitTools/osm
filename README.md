OSM
===

The osm project 

install:
  1. install python 2.7, along easy_install, zc.buildout ("zc.buildout==1.5.2") and git
  1. git clone https://github.com/OpenTransitTools/osm.git
  1. cd osm
  1. buildout
  1. purpose: cached GTFS .zip files into [gtfsdb](http://gtfsdb.com}
     The [./config/app.ini](../../../config/app.ini) file controls the list of gtfs feeds cached.
  1. run: bin/osm_update (optional: -ini <name>.ini | force_update)
  1. build OSMOSIS:
  1.   cd ott/osm/osmosis
  1.   install.sh
  1.   cd -

  1. git update-index --assume-unchanged .pydevproject
  1. NOTE: system packages necessary for things to work may include pre-built Shapely, or else the following system packages: 
  1. Install these packages
     - `yum install protobuf protobuf-devel tokyocabinet tokyocabinet-devel geos geos-devel  libxml2 libxslt libxml2-devel libxslt-devel
    `
  1. Or Build and install Protobuf and TokyoCabinet from source (MacOSX):
     - git clone https://github.com/google/protobuf 
     - wget http://tokyocabinet.sourceforge.net/tokyocabinet-1.4.25.tar.gz


run:
  - bin/test ... this cmd will run osm's unit tests (see: http://docs.zope.org/zope.testrunner/#some-useful-command-line-options-to-get-you-started)
  - bin/osm_rename --osm ott/osm/tests/data/test_data_2018.osm -out renamed.osm
  - bin/osm_intersections --osm ott/osm/tests/data/test_data_2018.osm -out intersections.osm
