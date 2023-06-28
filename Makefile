build:
	docker build --tag 'to_gif_dev' .

start:
	docker run --net=master_default --name=to_gif -p 9001:9001 to_gif_dev -e "app_name=to_gif"

stop:
	docker container stop to_gif

remove:
	docker rm to_gif

all:
	docker rm to_gif
	docker build --tag 'to_gif_dev' .
	docker run --net=master_default --name=to_gif -p 9001:9001 to_gif_dev
