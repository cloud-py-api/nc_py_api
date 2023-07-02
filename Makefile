build:
	docker build --tag 'to_gif_dev' .

start:
	docker run --net=master_default --name=to_gif -p 9001:9001 to_gif_dev -e "app_name=to_gif"

stop:
	docker container stop to_gif

register_app:
	nextcloud_url=http://nextcloud.local/index.php app_name=nc_py_api app_version=1.0.0 \
	app_secret=tC6vkwPhcppjMykD1r0n9NlI95uJMBYjs5blpIcA1PAdoPDmc5qoAjaBAkyocZ6E\
	X1T8Pi+T5papEolTLxz3fJSPS8ffC4204YmggxPsbJdCkXHWNPHKWS9B+vTj2SIV \
	python3 tests/_install.py

remove:
	docker rm to_gif

all:
	docker rm to_gif
	docker build --tag 'to_gif_dev' .
	docker run --net=master_default --name=to_gif -p 9001:9001 to_gif_dev
