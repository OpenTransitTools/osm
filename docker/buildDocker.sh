#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=open-transit-tools/osm
TAG=python3.14
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"


docker build -f docker/Dockerfile -t "${FULL_IMAGE_NAME}" .

echo "Built ${IMAGE_NAME}"
echo "Examples:"
echo "  docker run --rm -it ${IMAGE_NAME}"
echo "  docker run --rm -it ${IMAGE_NAME} osm_rename --help"
echo "  docker run --rm -it ${IMAGE_NAME} python -m ott.osm.intersections.osm_to_intersections --help"
