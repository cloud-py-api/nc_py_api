build:
	docker build --tag 'to_gif_dev' .

start:
	docker run --net=master_default --name=to_gif -p 9001:9001 to_gif_dev -e "app_name=to_gif"

stop:
	docker container stop to_gif

register_app:
	NEXTCLOUD_URL=http://nextcloud.local/index.php APP_ID=nc_py_api APP_VERSION=1.0.0 \
	APP_SECRET=tC6vkwPhcppjMykD1r0n9NlI95uJMBYjs5blpIcA1PAdoPDmc5qoAjaBAkyocZ6E\
	X1T8Pi+T5papEolTLxz3fJSPS8ffC4204YmggxPsbJdCkXHWNPHKWS9B+vTj2SIV APP_PORT=9002 \
	python3 tests/_install.py

remove:
	docker rm to_gif

all:
	docker rm to_gif
	docker build --tag 'to_gif_dev' .
	docker run --net=master_default --name=to_gif -p 9001:9001 to_gif_dev
