FROM python:3.14-slim AS base

ARG POETRY_VERSION=2.3.2

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Base toolchain and native deps used by project packages (shapely/lxml/psycopg2/protobuf).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      bash \
      build-essential \
      default-jre-headless \
      git \
      wget \
      libxml2-dev \
      libxslt1-dev \
      libpq-dev \
      libgeos-dev \
      libprotobuf-dev \
      protobuf-compiler && \
    rm -rf /var/lib/apt/lists/*

RUN python --version && \
    pip --version && \
    pip install --upgrade pip setuptools wheel && \
    pip install "poetry==${POETRY_VERSION}"

WORKDIR /osm

# Install dependencies first for better layer caching.
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main

# Install project.
COPY . .
RUN poetry install --only main

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY docker/install_osmosis.sh /tmp/install_osmosis.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && chmod +x /tmp/install_osmosis.sh && /tmp/install_osmosis.sh && rm /tmp/install_osmosis.sh

FROM base AS prod
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]

FROM base AS test
# Adds test-only deps without impacting the production image layers.
RUN poetry install --with test --no-interaction
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
