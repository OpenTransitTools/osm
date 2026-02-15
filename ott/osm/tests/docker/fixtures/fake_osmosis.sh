#!/usr/bin/env bash
set -euo pipefail

in_path=""
out_path=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --read-xml|--read-pbf)
      in_path="${2:-}"
      shift 2
      ;;
    --write-xml|--write-pbf)
      out_path="${2:-}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [[ -z "${out_path}" ]]; then
  exit 0
fi

mkdir -p "$(dirname "${out_path}")"

if [[ -n "${in_path}" && -f "${in_path}" ]]; then
  cp "${in_path}" "${out_path}"
  exit 0
fi

cat > "${out_path}" <<'EOF'
<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6" generator="fake-osmosis">
  <node id="1" lat="45.5100" lon="-122.6900" version="1" timestamp="2024-01-01T00:00:00Z" changeset="1"/>
</osm>
EOF
