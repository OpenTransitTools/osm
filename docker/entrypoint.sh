#!/usr/bin/env sh
set -eu

# If no command is provided, open an interactive shell.
if [ "$#" -eq 0 ]; then
  exec bash
fi

exec "$@"
