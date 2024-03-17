#!/bin/bash

echo "creating 'manual_install' deploy daemon for $1 container"
docker exec "$1" sudo -u www-data php occ app_api:daemon:register \
  manual_install "Manual Install" manual-install http host.docker.internal 0
echo "unregistering nc_py_api as an app for $1 container"
docker exec "$1" sudo -u www-data php occ app_api:app:unregister nc_py_api --silent --force || true
echo "registering nc_py_api as an app for $1 container"
docker exec "$1" sudo -u www-data php occ app_api:app:register nc_py_api manual_install --json-info \
  "{\"id\":\"nc_py_api\",\"name\":\"nc_py_api\",\"daemon_config_name\":\"manual_install\",\"version\":\"1.0.0\",\"secret\":\"12345\",\"scopes\":[\"ALL\"],\"port\":9009,\"system\":1}" \
  --force-scopes --wait-finish
echo "nc_py_api for $1 is ready to use"
