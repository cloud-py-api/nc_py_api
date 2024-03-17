.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Welcome to TalkBotAI example. Please use \`make <target>\` where <target> is one of"
	@echo " "
	@echo "  Next commands are only for dev environment with nextcloud-docker-dev!"
	@echo "  They should run from the host you are developing on(with activated venv) and not in the container with Nextcloud!"
	@echo "  "
	@echo "  build-push        build image and upload to ghcr.io"
	@echo "  "
	@echo "  run               install TalkBotAI for Nextcloud Last"
	@echo "  run27             install TalkBotAI for Nextcloud 27"
	@echo "  "
	@echo "  For development of this example use PyCharm run configurations. Development is always set for last Nextcloud."
	@echo "  First run 'TalkBotAI' and then 'make registerXX', after that you can use/debug/develop it and easy test."
	@echo "  "
	@echo "  register          perform registration of running 'TalkBotAI' into the 'manual_install' deploy daemon."
	@echo "  register27        perform registration of running 'TalkBotAI' into the 'manual_install' deploy daemon."

.PHONY: build-push
build-push:
	docker login ghcr.io
	docker buildx build --push --platform linux/arm64/v8,linux/amd64 --tag ghcr.io/cloud-py-api/talk_bot_ai:latest .

.PHONY: run
run:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:unregister talk_bot_ai --silent --force || true
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:register talk_bot_ai --force-scopes \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/talk_bot_ai/appinfo/info.xml

.PHONY: run27
run27:
	docker exec master-stable27-1 sudo -u www-data php occ app_api:app:unregister talk_bot_ai --silent --force || true
	docker exec master-stable27-1 sudo -u www-data php occ app_api:app:register talk_bot_ai --force-scopes \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/talk_bot_ai/appinfo/info.xml

.PHONY: register
register:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:unregister talk_bot_ai --silent --force || true
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:register talk_bot_ai manual_install --json-info \
  "{\"id\":\"talk_bot_ai\",\"name\":\"TalkBotAI\",\"daemon_config_name\":\"manual_install\",\"version\":\"1.0.0\",\"secret\":\"12345\",\"port\":9034,\"scopes\":[\"TALK\", \"TALK_BOT\"],\"system\":0}" \
  --force-scopes --wait-finish

.PHONY: register27
register27:
	docker exec master-stable27-1 sudo -u www-data php occ app_api:app:unregister talk_bot_ai --silent --force || true
	docker exec master-stable27-1 sudo -u www-data php occ app_api:app:register talk_bot_ai manual_install --json-info \
  "{\"id\":\"talk_bot_ai\",\"name\":\"TalkBotAI\",\"daemon_config_name\":\"manual_install\",\"version\":\"1.0.0\",\"secret\":\"12345\",\"port\":9034,\"scopes\":[\"TALK\", \"TALK_BOT\"],\"system\":0}" \
  --force-scopes --wait-finish
