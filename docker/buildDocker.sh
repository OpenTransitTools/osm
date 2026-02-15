#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-ghcr.io/opentransittools/osm}"
BUILD_TARGET="${BUILD_TARGET:-test}"

if [[ -n "${TAG:-}" ]]; then
  IMAGE_TAG="${TAG}"
else
  BRANCH_NAME="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo local)"
  if [[ "${BRANCH_NAME}" == "master" ]]; then
    IMAGE_TAG="latest"
  else
    IMAGE_TAG="$(echo "${BRANCH_NAME}" | tr '[:upper:]' '[:lower:]' | sed 's#[^a-z0-9._-]#-#g')"
  fi
fi

FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

docker build -f docker/Dockerfile --target "${BUILD_TARGET}" -t "${FULL_IMAGE_NAME}" .

echo "Built ${FULL_IMAGE_NAME} (target=${BUILD_TARGET})"
echo "Examples:"
echo "  docker run --rm -it ${FULL_IMAGE_NAME}"
echo "  docker run --rm -it ${FULL_IMAGE_NAME} osm_rename --help"
echo "  docker run --rm -it ${FULL_IMAGE_NAME} python -m ott.osm.intersections.osm_to_intersections --help"
