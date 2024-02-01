.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Welcome to UiExample example. Please use \`make <target>\` where <target> is one of"
	@echo " "
	@echo "  Next commands are only for dev environment with nextcloud-docker-dev!"
	@echo "  They should run from the host you are developing on(with activated venv) and not in the container with Nextcloud!"
	@echo "  "
	@echo "  build-push        build image and upload to ghcr.io"
	@echo "  "
	@echo "  deploy27          deploy UiExample to registered 'docker_dev' for Nextcloud 27"
	@echo "  deploy28          deploy UiExample to registered 'docker_dev' for Nextcloud 28"
	@echo "  deploy            deploy UiExample to registered 'docker_dev' for Nextcloud Last"
	@echo "  "
	@echo "  run27             install UiExample for Nextcloud 27"
	@echo "  run28             install UiExample for Nextcloud 28"
	@echo "  run               install UiExample for Nextcloud Last"
	@echo "  "
	@echo "  For development of this example use PyCharm run configurations. Development is always set for last Nextcloud."
	@echo "  First run 'UiExample' and then 'make registerXX', after that you can use/debug/develop it and easy test."
	@echo "  "
	@echo "  register27        perform registration of running UiExample into the 'manual_install' deploy daemon."
	@echo "  register28        perform registration of running UiExample into the 'manual_install' deploy daemon."
	@echo "  register          perform registration of running UiExample into the 'manual_install' deploy daemon."

.PHONY: build-push
build-push:
	docker login ghcr.io
	docker buildx build --push --platform linux/arm64/v8,linux/amd64 --tag ghcr.io/cloud-py-api/ui_example:latest .

.PHONY: deploy27
deploy27:
	docker exec master-stable27-1 sudo -u www-data php occ app_api:app:unregister ui_example --silent --force || true
	docker exec master-stable27-1 sudo -u www-data php occ app_api:app:deploy ui_example docker_dev \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/ui_example/appinfo/info.xml

.PHONY: deploy28
deploy28:
	docker exec master-stable28-1 sudo -u www-data php occ app_api:app:unregister ui_example --silent --force || true
	docker exec master-stable28-1 sudo -u www-data php occ app_api:app:deploy ui_example docker_dev \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/ui_example/appinfo/info.xml

.PHONY: deploy
deploy:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:unregister ui_example --silent --force || true
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:deploy ui_example docker_dev \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/ui_example/appinfo/info.xml

.PHONY: run27
run27:
	docker exec master-stable27-1 sudo -u www-data php occ app_api:app:unregister ui_example --silent --force || true
	docker exec master-stable27-1 sudo -u www-data php occ app_api:app:register ui_example docker_dev --force-scopes \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/ui_example/appinfo/info.xml

.PHONY: run28
run28:
	docker exec master-stable28-1 sudo -u www-data php occ app_api:app:unregister ui_example --silent --force || true
	docker exec master-stable28-1 sudo -u www-data php occ app_api:app:register ui_example docker_dev --force-scopes \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/ui_example/appinfo/info.xml

.PHONY: run
run:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:unregister ui_example --silent --force || true
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:register ui_example docker_dev --force-scopes \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/ui_example/appinfo/info.xml

.PHONY: register27
register27:
	docker exec master-stable27-1 sudo -u www-data php occ app_api:app:unregister ui_example --silent --force || true
	docker exec master-stable27-1 sudo -u www-data php occ app_api:app:register ui_example manual_install --json-info \
  "{\"appid\":\"ui_example\",\"name\":\"UI Example\",\"daemon_config_name\":\"manual_install\",\"version\":\"1.0.0\",\"secret\":\"12345\",\"port\":9035,\"scopes\":[],\"system_app\":0}" \
  --force-scopes --wait-finish

.PHONY: register28
register28:
	docker exec master-stable28-1 sudo -u www-data php occ app_api:app:unregister ui_example --silent --force || true
	docker exec master-stable28-1 sudo -u www-data php occ app_api:app:register ui_example manual_install --json-info \
  "{\"appid\":\"ui_example\",\"name\":\"UI Example\",\"daemon_config_name\":\"manual_install\",\"version\":\"1.0.0\",\"secret\":\"12345\",\"port\":9035,\"scopes\":[],\"system_app\":0}" \
  --force-scopes --wait-finish

.PHONY: register
register:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:unregister ui_example --silent --force || true
	docker exec master-nextcloud-1 sudo -u www-data php occ app_api:app:register ui_example manual_install --json-info \
  "{\"appid\":\"ui_example\",\"name\":\"UI Example\",\"daemon_config_name\":\"manual_install\",\"version\":\"1.0.0\",\"secret\":\"12345\",\"port\":9035,\"scopes\":[],\"system_app\":0}" \
  --force-scopes --wait-finish
