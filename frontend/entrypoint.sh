#!/bin/sh
# Substitutes runtime env vars into the nginx template, then starts nginx.
# Defaults match the docker-compose setup (backend service on the compose net).
# Set BACKEND_HOST/BACKEND_PORT to point elsewhere (e.g. a Render service URL).
set -e

: "${BACKEND_HOST:=backend}"
: "${BACKEND_PORT:=8000}"
export BACKEND_HOST BACKEND_PORT

export > /etc/nginx/conf.d/nginx.env
templater() {
  awk '{
    while (match($0, /\$\{[A-Z_]+\}/)) {
      var = substr($0, RSTART + 2, RLENGTH - 3)
      val = ENVIRON[var]
      sub(/\$\{[A-Z_]+\}/, val, $0)
    }
    print
  }' /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
}
templater

exec nginx -g 'daemon off;'
