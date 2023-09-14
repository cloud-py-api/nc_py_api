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
	@echo "  deploy            deploy example to registered 'docker_dev'"
	@echo "  "
	@echo "  run28             install TalkBotAI for Nextcloud 28"
	@echo "  run27             install TalkBotAI for Nextcloud 27"
	@echo "  "
	@echo "  For development of this example use PyCharm run configurations. Development is always set for last Nextcloud."
	@echo "  First run 'TalkBotAI' and then 'make manual_register', after that you can use/debug/develop it and easy test."
	@echo "  "
	@echo "  manual_register   perform registration of running 'TalkBotAI' into the 'manual_install' deploy daemon."

.PHONY: build-push
build-push:
	docker login ghcr.io
	docker buildx build --push --platform linux/arm64/v8,linux/amd64 --tag ghcr.io/cloud-py-api/talk_bot_ai:latest .

.PHONY: deploy
deploy:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:deploy talk_bot_ai docker_dev \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/talk_bot_ai/appinfo/info.xml

.PHONY: run28
run28:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:unregister talk_bot_ai --silent || true
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:register talk_bot_ai docker_dev -e --force-scopes \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/talk_bot_ai/appinfo/info.xml

.PHONY: run27
run27:
	docker exec master-stable27-1 sudo -u www-data php occ app_api:app:unregister talk_bot_ai --silent || true
	docker exec master-stable27-1 sudo -u www-data php occ app_api:app:register talk_bot_ai docker_dev -e --force-scopes \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/talk_bot_ai/appinfo/info.xml

.PHONY: manual_register
manual_register:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:unregister talk_bot_ai --silent || true
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:register talk_bot_ai manual_install --json-info \
  "{\"appid\":\"talk_bot_ai\",\"name\":\"TalkBotAI\",\"daemon_config_name\":\"manual_install\",\"version\":\"1.0.0\",\"secret\":\"12345\",\"host\":\"host.docker.internal\",\"port\":9034,\"scopes\":{\"required\":[\"TALK\", \"TALK_BOT\"],\"optional\":[]},\"protocol\":\"http\",\"system_app\":0}" \
  -e --force-scopes
