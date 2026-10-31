#!/bin/sh
set -e

envsubst '${API_URL}' \
  < /usr/share/nginx/html/config.template.js \
  > /usr/share/nginx/html/config.js

exec "$@"