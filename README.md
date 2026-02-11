OSM
===

OpenTransitTools OSM tools.

## Requirements
- Python 3.12+
- Poetry

## Local Install
1. Clone and install:
   - `git clone https://github.com/OpenTransitTools/osm.git`
   - `cd osm`
   - `poetry install`
2. Optional: install local OSMOSIS binary for `.osm/.pbf` conversions:
   - `cd ott/osm/osmosis`
   - `bash install.sh`
   - `cd -`

## Common Commands
- `poetry run osm_update`
- `poetry run osm_rename --osm ott/osm/tests/data/test_data_2018.osm -out renamed.osm`
- `poetry run osm-intersections --osm ott/osm/tests/data/test_data_2018.osm -out intersections.osm`
- `poetry run osm_stats --help`

## Config
- Main app config: `config/app.ini`
- OSMOSIS default path in config points to: `ott/osm/osmosis/bin/osmosis`

## Docker
1. Build image:
   - `docker/buildDocker.sh`
2. Open shell:
   - `docker run --rm -it ott-osm:alma9 bash`
3. Run tools:
   - `docker run --rm -it ott-osm:alma9 osm_rename --help`
   - `docker run --rm -it ott-osm:alma9 osm-intersections --help`

Note: OSMOSIS is installed during image build via `docker/install_osmosis.sh`.
