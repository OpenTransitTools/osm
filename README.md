OSM
===

OpenTransitTools utilities for downloading, clipping, normalizing, exporting, and loading OpenStreetMap data.

## Docker-First Usage
This project is now intended to be run through Docker.  
Build the image once, then run any API command from the container.

## Requirements
- Docker
- Optional: local bind mounts for persistent cache/output files

## Configuration
Primary runtime config is `config/app.ini`.

Important keys in `[osm]`:
- `pbf_url`: source `.osm.pbf` download URL (usually Geofabrik)
- `meta_url`: metadata URL for freshness checks
- `cache_dir`: output/cache directory
- `name`: base dataset name (for generated files)
- `bbox`: clipping bounds key
- `osmosis_path`: osmosis executable path
- `other_exports`: additional bbox exports
- `intersection_out_file`: intersection CSV filename

## Build The Image
From the repo root:
```bash
docker/buildDocker.sh
```

Default tag from the build script:
```bash
OpenTransitTools/osm:python3.14
```

Override image name/tag:
```bash
FULL_IMAGE_NAME=OpenTransitTools/osm:python3.14 docker/buildDocker.sh
```

## Docker Compose
Use `docker/compose.yml` for repeatable command runs with mounted config, cache, input, and output.

Mounted paths:
- Host `config/app.ini` -> Container `/osm/config/app.ini` (read-only)
- Host `ott/osm/cache` -> Container `/osm/ott/osm/cache`
- Host `data/input` -> Container `/data/input`
- Host `data/output` -> Container `/data/output`

Build and run with Compose:
```bash
docker compose -f docker/compose.yml build
docker compose -f docker/compose.yml run --rm osm osm_update
```

Run specific commands via Compose:
```bash
docker compose -f docker/compose.yml run --rm osm \
  osm_rename --osm /data/input/in.osm --output /data/output/out.osm

docker compose -f docker/compose.yml run --rm osm \
  osm-intersections --osm /data/input/in.osm --csv /data/output/intersections.csv
```

## Run Pattern
General pattern:
```bash
docker run --rm -it OpenTransitTools/osm:python3.14 <command> [args...]
```

Persist cache/output to host:
```bash
docker run --rm -it \
  -v "$PWD/ott/osm/cache:/osm/ott/osm/cache" \
  OpenTransitTools/osm:python3.14 <command> [args...]
```

Use custom config:
```bash
docker run --rm -it \
  -v "$PWD/config/app.ini:/osm/config/app.ini:ro" \
  OpenTransitTools/osm:python3.14 <command> [args...]
```

Open an interactive shell in the image:
```bash
docker run --rm -it OpenTransitTools/osm:python3.14 bash
```

## Command Reference
All commands below are intended to run inside the Docker image.

### `osm_update`
- What it does: full cache/update pipeline. Downloads fresh `.pbf` if needed, clips to bbox, renames streets, builds stats, emits `.pbf` variants, exports configured subregions, generates intersections CSV, and optionally runs `osm2pgsql`.
- Inputs: `config/app.ini` (`[osm]`, `[osm_db]`, bbox sections).
- Output: refreshed files in configured cache directory.
- Example:
```bash
docker run --rm -it OpenTransitTools/osm:python3.14 osm_update
```

### `osm_clip_from_pbf`
- What it does: clip configured region from source `.pbf` into `*-carto.osm` and main `.osm`.
- Inputs: cached/source `.pbf`, bbox config.
- Output: clipped OSM files.
- Example:
```bash
docker run --rm -it OpenTransitTools/osm:python3.14 osm_clip_from_pbf
```

### `osm_clip_rename`
- What it does: clip from `.pbf`, rename street tags, then write stats cache.
- Inputs: same as `osm_clip_from_pbf`.
- Output: renamed `.osm` and `-stats` JSON.
- Example:
```bash
docker run --rm -it OpenTransitTools/osm:python3.14 osm_clip_rename
```

### `osm_make_raw`
- What it does: builds a raw clipped OSM/PBF without street renaming (and can cull transit tags).
- Inputs: configured OSM paths and bbox.
- Output: `*-raw.osm` and `*-raw.osm.pbf`.
- Example:
```bash
docker run --rm -it OpenTransitTools/osm:python3.14 osm_make_raw
```

### `osm_rename`
- What it does: abbreviates common street name prefixes/suffixes in OSM tags.
- Inputs: `--osm` input file, optional output file.
- Output: renamed OSM file (in-place by default).
- Example:
```bash
docker run --rm -it \
  -v "$PWD:/work" -w /work \
  OpenTransitTools/osm:python3.14 osm_rename --osm ./data/region.osm --output ./data/region-renamed.osm
```

### `osm_stats`
- What it does: computes or reads cached stats for an OSM file (way count, highway count, latest edit metadata).
- Inputs: `--osm` file path.
- Output: printed JSON stats and cache message lines.
- Example:
```bash
docker run --rm -it \
  -v "$PWD:/work" -w /work \
  OpenTransitTools/osm:python3.14 osm_stats --osm ./cache/or-wa.osm
```

### `osm_stats_cfg`
- What it does: prints stats for the configured cached OSM file from `app.ini`.
- Inputs: config only.
- Output: printed JSON stats.
- Example:
```bash
docker run --rm -it OpenTransitTools/osm:python3.14 osm_stats_cfg
```

### `osm_to_pbf`
- What it does: converts `.osm` XML to `.pbf` via osmosis.
- Inputs: `--osm`, optional output `--pbf`, optional `--osmosis_exe`.
- Output: `.pbf` file.
- Example:
```bash
docker run --rm -it \
  -v "$PWD:/work" -w /work \
  OpenTransitTools/osm:python3.14 osm_to_pbf --osm ./cache/or-wa.osm --pbf ./cache/or-wa.osm.pbf
```

### `osm_cull_transit`
- What it does: removes transit features from OSM using `tagtransform.xml` and writes a culled OSM.
- Inputs: `--osm`, optional `--osmosis_exe`.
- Output: `<input>_cull_transit.osm` unless overridden internally.
- Example:
```bash
docker run --rm -it \
  -v "$PWD:/work" -w /work \
  OpenTransitTools/osm:python3.14 osm_cull_transit --osm ./cache/or-wa.osm
```

### `osm-intersections`
- What it does: finds named street intersections from an OSM XML file.
- Inputs: `--osm` and optional `--pelias`/`--csv` output.
- Output: prints intersection pairs to stdout, or writes Pelias-formatted CSV.
- Example:
```bash
docker run --rm -it \
  -v "$PWD:/work" -w /work \
  OpenTransitTools/osm:python3.14 osm-intersections --osm ./cache/or-wa.osm --csv ./cache/intersections.csv
```

### `osm-intersections_cache`
- What it does: generates intersection CSV for the configured cached OSM using `intersection_out_file`.
- Inputs: config only.
- Output: intersection CSV in cache directory.
- Example:
```bash
docker run --rm -it OpenTransitTools/osm:python3.14 osm-intersections_cache
```

### `osm_other_exports`
- What it does: creates additional configured bbox exports listed in `other_exports`.
- Inputs: config only, optional name filter argument.
- Output: one or more exported `.osm` + `.pbf` files.
- Examples:
```bash
docker run --rm -it OpenTransitTools/osm:python3.14 osm_other_exports
docker run --rm -it OpenTransitTools/osm:python3.14 osm_other_exports hillsboro
```

### `osm_to_pgsql`
- What it does: imports OSM into PostgreSQL/PostGIS with `osm2pgsql`, then optionally runs post-processing SQL.
- Inputs: configured database URL and style/sql files in config.
- Output: loaded OSM database tables.
- Example:
```bash
docker run --rm -it OpenTransitTools/osm:python3.14 osm_to_pgsql
```

### `osm_abbr_tester`
- What it does: abbreviation parser test utility (entry point exists in package metadata).
- Note: test module is not currently present in this checkout.

## Typical Workflows
### 1) Refresh cached regional dataset
```bash
docker run --rm -it \
  -v "$PWD/ott/osm/cache:/osm/ott/osm/cache" \
  OpenTransitTools/osm:python3.14 osm_update
```

### 2) Rename and inspect a custom OSM file
```bash
docker run --rm -it -v "$PWD:/work" -w /work OpenTransitTools/osm:python3.14 \
  osm_rename --osm ./input.osm --output ./renamed.osm
docker run --rm -it -v "$PWD:/work" -w /work OpenTransitTools/osm:python3.14 \
  osm_stats --osm ./renamed.osm
```

### 3) Generate Pelias intersections CSV
```bash
docker run --rm -it -v "$PWD:/work" -w /work OpenTransitTools/osm:python3.14 \
  osm-intersections --osm ./cache/or-wa.osm --csv ./cache/intersections.csv
```

### 4) Convert OSM XML to PBF
```bash
docker run --rm -it -v "$PWD:/work" -w /work OpenTransitTools/osm:python3.14 \
  osm_to_pbf --osm ./cache/or-wa.osm --pbf ./cache/or-wa.osm.pbf
```

## Notes
- `docker/install_osmosis.sh` installs osmosis during image build.
- Container entrypoint (`docker/entrypoint.sh`) runs whatever command you pass, so the image can execute the full API command set directly.
