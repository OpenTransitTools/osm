OSM
===

OpenTransitTools utilities for downloading, clipping, normalizing, exporting, and loading OpenStreetMap data.

## Docker-First Usage
This project is intended to be run through Docker.
Build the image once, then run API commands from the container.

Build targets:
- `test`: includes test dependencies (`pytest`, `coverage`) for local/CI test runs.
- `prod`: lean runtime image for publish/deploy.

## Requirements
- Docker
- Optional: bind mounts for persistent cache/input/output files

## Configuration
Primary runtime config is `config/app.ini`.

Important keys in `[osm]`:
- `pbf_url`: source `.osm.pbf` download URL
- `meta_url`: metadata URL for freshness checks
- `cache_dir`: output/cache directory
- `name`: base dataset name
- `bbox`: clipping bounds key
- `osmosis_path`: osmosis executable path
- `other_exports`: additional bbox exports
- `intersection_out_file`: intersection CSV filename

## Build The Image
From repo root:
```bash
docker/buildDocker.sh
```

Default behavior from `docker/buildDocker.sh`:
```bash
IMAGE_NAME=ghcr.io/opentransittools/osm
BUILD_TARGET=test
TAG=<auto>
# TAG auto-rules: master -> latest, otherwise sanitized branch name
```

Override image name/tag/target:
```bash
IMAGE_NAME=ghcr.io/opentransittools/osm TAG=feature-x BUILD_TARGET=prod docker/buildDocker.sh
```

## Docker Compose
Use `docker/compose.yml` for repeatable command runs with mounted config, cache, input, and output.

Mounted paths:
- Host `config/app.ini` -> `/osm/config/app.ini` (read-only)
- Host `ott/osm/cache` -> `/osm/ott/osm/cache`
- Host `data/input` -> `/data/input`
- Host `data/output` -> `/data/output`

Build and run with Compose:
```bash
docker compose -f docker/compose.yml build
docker compose -f docker/compose.yml run --rm osm osm_update
```

Compose is configured to build the `test` target.

## Run Pattern
General pattern:
```bash
docker run --rm -it ghcr.io/opentransittools/osm:latest <command> [args...]
```

Use custom config:
```bash
docker run --rm -it \
  -v "$PWD/config/app.ini:/osm/config/app.ini:ro" \
  ghcr.io/opentransittools/osm:latest <command> [args...]
```

## Command Reference
### `osm_update`
Full cache/update pipeline. Example:
```bash
docker run --rm -it ghcr.io/opentransittools/osm:latest osm_update
```

### `osm_clip_from_pbf`
Clip configured region from source `.pbf`. Example:
```bash
docker run --rm -it ghcr.io/opentransittools/osm:latest osm_clip_from_pbf
```

### `osm_clip_rename`
Clip and rename street tags. Example:
```bash
docker run --rm -it ghcr.io/opentransittools/osm:latest osm_clip_rename
```

### `osm_make_raw`
Build raw clipped OSM/PBF without renaming. Example:
```bash
docker run --rm -it ghcr.io/opentransittools/osm:latest osm_make_raw
```

### `osm_rename`
Rename abbreviations in OSM tags. Example:
```bash
docker run --rm -it -v "$PWD:/work" -w /work \
  ghcr.io/opentransittools/osm:latest osm_rename --osm ./data/region.osm --output ./data/region-renamed.osm
```

### `osm_stats`
Compute/read cached stats. Example:
```bash
docker run --rm -it -v "$PWD:/work" -w /work \
  ghcr.io/opentransittools/osm:latest osm_stats --osm ./cache/or-wa.osm
```

### `osm_stats_cfg`
Stats for configured cached OSM. Example:
```bash
docker run --rm -it ghcr.io/opentransittools/osm:latest osm_stats_cfg
```

### `osm_to_pbf`
Convert `.osm` XML to `.pbf` via osmosis. Example:
```bash
docker run --rm -it -v "$PWD:/work" -w /work \
  ghcr.io/opentransittools/osm:latest osm_to_pbf --osm ./cache/or-wa.osm --pbf ./cache/or-wa.osm.pbf
```

### `osm_cull_transit`
Cull transit features via `tagtransform.xml`. Example:
```bash
docker run --rm -it -v "$PWD:/work" -w /work \
  ghcr.io/opentransittools/osm:latest osm_cull_transit --osm ./cache/or-wa.osm
```

### `osm-intersections`
Extract intersections from OSM XML. Example:
```bash
docker run --rm -it -v "$PWD:/work" -w /work \
  ghcr.io/opentransittools/osm:latest osm-intersections --osm ./cache/or-wa.osm --csv ./cache/intersections.csv
```

### `osm-intersections_cache`
Intersection CSV for configured cache. Example:
```bash
docker run --rm -it ghcr.io/opentransittools/osm:latest osm-intersections_cache
```

### `osm_other_exports`
Run configured export list. Examples:
```bash
docker run --rm -it ghcr.io/opentransittools/osm:latest osm_other_exports
docker run --rm -it ghcr.io/opentransittools/osm:latest osm_other_exports hillsboro
```

### `osm_to_pgsql`
Load OSM into PostgreSQL/PostGIS. Example:
```bash
docker run --rm -it ghcr.io/opentransittools/osm:latest osm_to_pgsql
```

### `osm_abbr_tester`
Run abbreviation parser exercise utility. Example:
```bash
docker run --rm -it ghcr.io/opentransittools/osm:latest osm_abbr_tester
```

## Docker Test Scenario
Build the test target image:
```bash
BUILD_TARGET=test docker/buildDocker.sh
```

Run docker API script tests:
```bash
poetry run pytest -v ott/osm/tests/docker/test_project_scripts_docker.py
```

Notes:
- Script smoke tests intentionally mount `fake_osmosis.sh` for deterministic behavior.
- Tests also verify the real osmosis binary exists at `/osm/bin/osmosis`.

## CI Image Targets
- `.github/workflows/ci.yml` runs tests and coverage.
- `.github/workflows/container.yml` publishes the `prod` Docker target.
- Published tags:
  - `master` branch -> `latest`
  - other branches -> sanitized branch name

## Notes
- `docker/install_osmosis.sh` installs osmosis during image build.
- `docker/entrypoint.sh` runs whatever command you pass.
