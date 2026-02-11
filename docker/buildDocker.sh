#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-ott-osm:alma9}"

docker build -f docker/Dockerfile -t "${IMAGE_NAME}" .

echo "Built ${IMAGE_NAME}"
echo "Examples:"
echo "  docker run --rm -it ${IMAGE_NAME}"
echo "  docker run --rm -it ${IMAGE_NAME} osm_rename --help"
echo "  docker run --rm -it ${IMAGE_NAME} python -m ott.osm.intersections.osm_to_intersections --help"
