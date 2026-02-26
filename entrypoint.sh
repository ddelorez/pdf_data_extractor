#!/bin/bash
set -e

# Fix ownership of bind-mounted directories at runtime
# This is necessary because bind mounts override image-layer permissions
chown -R appuser:appuser /app/uploads /app/outputs /app/logs 2>/dev/null || true

# Drop privileges and exec the CMD
exec gosu appuser "$@"
