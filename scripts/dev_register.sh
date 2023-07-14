#!/bin/bash

echo "creating fake deploy daemon for nextcloud 28 container"
docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:daemon:unregister simulate_docker || true
docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:daemon:register \
  simulate_docker FakeDocker docker-install unix-socket 0 0
echo "registering nc_py_api as an app for nextcloud 28 container"
docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:app:unregister nc_py_api --silent || true
NEXTCLOUD_URL="http://nextcloud.local" APP_PORT=9009 APP_ID="nc_py_api" APP_SECRET="12345" APP_VERSION="1.0.0" \
  python3 tests/_install.py &
echo $! > /tmp/_install.pid
sleep 7
docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:app:register \
  "{\"appid\":\"nc_py_api\",\"name\":\"NC_Py_API\",\"daemon_config_name\":\"simulate_docker\",\"version\":\"1.0.0\",\"secret\":\"12345\",\"host\":\"host.docker.internal\",\"port\":9009,\"system_app\":1}" \
  -e --force-scopes
cat /tmp/_install.pid
kill -15 "$(cat /tmp/_install.pid)"
