How To Install
==============

Currently, while AppAPI hasn't been published on the App Store, and App Store support hasn't been added yet,
installation is a little bit tricky.

Steps to Install:

1. [Install AppEcosystem](https://cloud-py-api.github.io/app_api/Installation.html)
2. Create a deployment daemon according to the [instructions](https://cloud-py-api.github.io/app_api/CreationOfDeployDaemon.html#create-deploy-daemon) of the AppPI
3. php occ app_api:app:deploy talk_bot "daemon_deploy_name" \
--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/talk_bot/appinfo/info.xml

    to deploy a docker image with Bot to docker.

4. php occ app_api:app:register talk_bot "daemon_deploy_name" -e --force-scopes \
--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/talk_bot/appinfo/info.xml

    to call its **enable** handler and accept all required API scopes by default.


In a few months
===============

1. Install AppEcosystem from App Store
2. Configure Deploy Daemon with GUI provided by AppEcosystem
3. Go to External Applications page in Nextcloud UI
4. Find this bot in a list and press "Install" and "Enable" buttons, like with usual Applications.
