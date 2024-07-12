#!/bin/bash

# Parameters:
# APP_ID, VERSION, SECRET, HOST, PORT

php occ app_api:daemon:register manual_install "Manual Install" manual-install http "$4" 0
php occ app_api:app:register "$1" manual_install --json-info \
  "{\"appid\":\"$1\",\"name\":\"$1\",\"daemon_config_name\":\"manual_install\",\"version\":\"$2\",\"secret\":\"$3\",\"scopes\":[\"ALL\"],\"port\":$5}" \
  --force-scopes --wait-finish
