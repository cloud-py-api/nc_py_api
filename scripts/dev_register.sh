#!/bin/bash

echo "removing 'manual_install' deploy daemon for nextcloud 28 container"
docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:daemon:unregister manual_install || true
echo "creating 'manual_install' deploy daemon for nextcloud 28 container"
docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:daemon:register \
  manual_install "Manual Install" manual-install 0 0 0
echo "unregistering nc_py_api as an app for nextcloud 28 container"
docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:app:unregister nc_py_api --silent || true
echo "registering nc_py_api as an app for nextcloud 28 container"
NEXTCLOUD_URL="http://nextcloud.local" APP_PORT=9009 APP_ID="nc_py_api" APP_SECRET="12345" APP_VERSION="1.0.0" \
  python3 tests/_install.py > /dev/null 2>&1 &
echo $! > /tmp/_install.pid
sleep 7
docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:app:register nc_py_api manual_install --json-info \
  "{\"appid\":\"nc_py_api\",\"name\":\"NC_Py_API\",\"daemon_config_name\":\"manual_install\",\"version\":\"1.0.0\",\"secret\":\"12345\",\"host\":\"host.docker.internal\",\"port\":9009,\"protocol\":\"http\",\"system_app\":1}" \
  -e --force-scopes
cat /tmp/_install.pid
kill -15 "$(cat /tmp/_install.pid)"
echo "nc_py_api - ready"
