How To Install
==============

1. [Install AppAPI](https://apps.nextcloud.com/apps/app_api)
2. Create a deployment daemon according to the [instructions](https://cloud-py-api.github.io/app_api/CreationOfDeployDaemon.html#create-deploy-daemon) of the AppPI
3. php occ app_api:app:register talk_bot --force-scopes \
--info-xml https://raw.githubusercontent.com/cloud-py-api/nc_py_api/main/examples/as_app/talk_bot/appinfo/info.xml

    to deploy and install this ExApp.
