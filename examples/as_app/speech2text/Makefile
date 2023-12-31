.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Welcome to Speech2TextProvider example. Please use \`make <target>\` where <target> is one of"
	@echo " "
	@echo "  Next commands are only for dev environment with nextcloud-docker-dev!"
	@echo "  They should run from the host you are developing on(with activated venv) and not in the container with Nextcloud!"
	@echo "  "
	@echo "  build-push        build image and upload to ghcr.io"
	@echo "  "
	@echo "  deploy            deploy Speech2TextProvider to registered 'docker_dev' for Nextcloud Last"
	@echo "  "
	@echo "  run               install Speech2TextProvider for Nextcloud Last"
	@echo "  "
	@echo "  For development of this example use PyCharm run configurations. Development is always set for last Nextcloud."
	@echo "  First run 'Speech2TextProvider' and then 'make registerXX', after that you can use/debug/develop it and easy test."
	@echo "  "
	@echo "  register          perform registration of running Speech2TextProvider into the 'manual_install' deploy daemon."

.PHONY: build-push
build-push:
	docker login ghcr.io
	docker buildx build --push --platform linux/arm64/v8,linux/amd64 --tag ghcr.io/cloud-py-api/speech_to_text_example:latest .

.PHONY: deploy
deploy:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:unregister speech2text_example --silent || true
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:deploy speech2text_example docker_dev \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/speech2text_example/appinfo/info.xml

.PHONY: run
run:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:unregister speech2text_example --silent || true
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:register speech2text_example docker_dev --force-scopes \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/speech2text_example/appinfo/info.xml

.PHONY: register
register:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:unregister speech2text_example --silent || true
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:register speech2text_example manual_install --json-info \
  "{\"appid\":\"speech2text_example\",\"name\":\"SpeechToText Provider\",\"daemon_config_name\":\"manual_install\",\"version\":\"1.0.0\",\"secret\":\"12345\",\"host\":\"host.docker.internal\",\"port\":9036,\"scopes\":{\"required\":[\"AI_PROVIDERS\"],\"optional\":[]},\"protocol\":\"http\",\"system_app\":0}" \
  --force-scopes --wait-finish
