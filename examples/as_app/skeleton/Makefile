.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Welcome to app_python_skeleton example. Please use \`make <target>\` where <target> is one of"
	@echo " "
	@echo "  Next commands are only for dev environment with nextcloud-docker-dev!"
	@echo "  They should run from the host you are developing on(with activated venv) and not in the container with Nextcloud!"
	@echo "  "
	@echo "  build-push        build image and upload to ghcr.io"
	@echo "  "
	@echo "  deploy            deploy example to registered 'docker_dev'"
	@echo "  "
	@echo "  run28             install app_python_skeleton for Nextcloud 28"
	@echo "  run27             install app_python_skeleton for Nextcloud 27"
	@echo "  "
	@echo "  For development of this example use PyCharm run configurations. Development is always set for last Nextcloud."
	@echo "  First run 'app_python_skeleton' and then 'make manual_register', after that you can use/debug/develop it and easy test."
	@echo "  "
	@echo "  manual_register   perform registration of running 'app_python_skeleton' into 'manual_install' deploy daemon."

.PHONY: build-push
build-push:
	docker login ghcr.io
	docker buildx build --push --platform linux/arm64/v8,linux/amd64 --tag ghcr.io/cloud-py-api/py_app_v2-skeleton:latest .

.PHONY: deploy
deploy:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:app:deploy app_python_skeleton docker_dev \
		--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/skeleton/appinfo/info.xml

.PHONY: run28
run28:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:app:unregister app_python_skeleton --silent || true
	docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:app:register app_python_skeleton docker_dev -e --force-scopes

.PHONY: run27
run27:
	docker exec master-stable27-1 sudo -u www-data php occ app_ecosystem_v2:app:unregister app_python_skeleton --silent || true
	docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:app:register app_python_skeleton docker_dev -e --force-scopes

.PHONY: manual_register
manual_register:
	docker exec master-nextcloud-1 sudo -u www-data php occ app_ecosystem_v2:app:register app_python_skeleton manual_install --json-info \
  "{\"appid\":\"app_python_skeleton\",\"name\":\"App Python Skeleton\",\"daemon_config_name\":\"manual_install\",\"version\":\"1.0.0\",\"secret\":\"12345\",\"host\":\"host.docker.internal\",\"port\":9029,\"scopes\":{\"required\":[],\"optional\":[]},\"protocol\":\"http\",\"system_app\":0}" \
  -e --force-scopes
