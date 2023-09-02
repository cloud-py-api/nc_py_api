#!/bin/bash

# Parameters:
# APP_ID, VERSION, SECRET, HOST, PORT

php occ app_ecosystem_v2:daemon:register manual_install "Manual Install" manual-install 0 0 0
php occ app_ecosystem_v2:app:register "$1" manual_install --json-info \
  "{\"appid\":\"$1\",\"name\":\"$1\",\"daemon_config_name\":\"manual_install\",\"version\":\"$2\",\"secret\":\"$3\",\"host\":\"$4\",\"scopes\":{\"required\":[\"SYSTEM\", \"FILES\", \"FILES_SHARING\"],\"optional\":[\"USER_INFO\", \"USER_STATUS\", \"NOTIFICATIONS\", \"WEATHER_STATUS\", \"TALK\", \"TALK_BOT\", \"ACTIVITIES\"]},\"port\":$5,\"protocol\":\"http\",\"system_app\":1}" \
  -e --force-scopes
