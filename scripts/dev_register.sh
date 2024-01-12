#!/bin/bash

echo "removing 'manual_install' deploy daemon for $1 container"
docker exec "$1" sudo -u www-data php occ app_api:daemon:unregister manual_install || true
echo "creating 'manual_install' deploy daemon for $1 container"
docker exec "$1" sudo -u www-data php occ app_api:daemon:register \
  manual_install "Manual Install" manual-install 0 0 0
echo "unregistering nc_py_api as an app for $1 container"
docker exec "$1" sudo -u www-data php occ app_api:app:unregister nc_py_api --silent --force || true
echo "registering nc_py_api as an app for $1 container"
NEXTCLOUD_URL="http://$2" APP_PORT=9009 APP_ID="nc_py_api" APP_SECRET="12345" APP_VERSION="1.0.0" \
  python3 tests/_install.py > /dev/null 2>&1 &
echo $! > /tmp/_install.pid
python3 tests/_install_wait.py "http://localhost:9009/heartbeat" "\"status\":\"ok\"" 15 0.5
docker exec "$1" sudo -u www-data php occ app_api:app:register nc_py_api manual_install --json-info \
  "{\"appid\":\"nc_py_api\",\"name\":\"nc_py_api\",\"daemon_config_name\":\"manual_install\",\"version\":\"1.0.0\",\"secret\":\"12345\",\"host\":\"host.docker.internal\",\"scopes\":{\"required\":[\"ALL\"],\"optional\":[]},\"port\":9009,\"protocol\":\"http\",\"system_app\":1}" \
  --force-scopes --wait-finish
cat /tmp/_install.pid
kill -15 "$(cat /tmp/_install.pid)"
echo "nc_py_api for $1 is ready to use"
