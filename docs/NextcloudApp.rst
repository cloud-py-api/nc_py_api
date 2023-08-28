Writing a Nextcloud Application
===============================

This chapter assumes that you are already familiar with the `concepts <https://cloud-py-api.github.io/app_ecosystem_v2/Concepts.html>`_ of the AppEcosystem.

As a first step, let's take a look at the structure of a basic Python application.

Skeleton
--------

.. literalinclude:: ../examples/as_app/skeleton/src/main.py

What's going on in the skeleton?

First, it's important to understand that an external application acts more like a microservice, with its endpoints being called by Nextcloud.

Therefore, when the application receives a request at the endpoint ``/enable``,
it should register all its functionalities in the cloud and wait for requests from Nextcloud.

.. note:: This doesn't apply to system applications, which will be covered in the next chapter.

So, calling:

.. code-block:: python

    set_handlers(APP, enabled_handler)

will register an **enabled_handler** that will be called **both when the application is enabled and disabled**.

During the enablement process, you should register all the functionalities that your application offers
in the **enabled_handler** and remove them during the disablement process.

The API is designed so that you don't have to check whether an endpoint is already registered
(e.g., in case of a malfunction or if the administrator manually altered something in the Nextcloud database).
The API will not fail, and in such cases, it will simply re-register without error.

If any error prevents your application from functioning, you should provide a brief description in the return instead
of an empty string, and log comprehensive information that will assist the administrator in addressing the issue.

Debugging
---------

Debugging an application within Docker and rebuilding it from scratch each time can be cumbersome.
Therefore, a manual deployment option has been specifically designed for this purpose.

First register ``manual_install`` daemon:

.. code-block:: shell

    php occ app_ecosystem_v2:daemon:register manual_install "Manual Install" manual-install 0 0 0

Then, launch your application. Since this is a manual deployment, it's your responsibility to set minimum of the environment variables.
Here they are:

* APP_ID - ID of the application.
* APP_PORT - Port on which application listen for the requests from the Nextcloud.
* APP_SECRET - Secret for ``hmac`` signature generation.
* APP_VERSION - Version of the application.
* AE_VERSION - Version of the AppEcosystem.
* NEXTCLOUD_URL - URL at which the application can access the Nextcloud API.

You can find values for these environment variables in the **Skeleton** or **ToGif** run configurations.

After launching your application, execute the following command in the Nextcloud container:

.. code-block:: shell

    php occ app_ecosystem_v2:app:register YOUR_APP_ID manual_install --json-info \
        "{\"appid\":\"YOUR_APP_ID\",\"name\":\"YOUR_APP_DISPLAY_NAME\",\"daemon_config_name\":\"manual_install\",\"version\":\"YOU_APP_VERSION\",\"secret\":\"YOUR_APP_SECRET\",\"host\":\"host.docker.internal\",\"scopes\":{\"required\":[2, 10, 11],\"optional\":[30, 31, 32, 33]},\"port\":SELECTED_PORT,\"protocol\":\"http\",\"system_app\":0}" \
        -e --force-scopes

You can see how **nc_py_api** registers in ``scripts/dev_register.sh``.

It's advisable to write these steps as commands in a Makefile for quick use.

Examples for such Makefiles can be found in this repository:
`Skeleton <https://github.com/cloud-py-api/nc_py_api/blob/main/examples/as_app/skeleton/Makefile>`_ ,
`TalkBot <https://github.com/cloud-py-api/nc_py_api/blob/main/examples/as_app/talk_bot/Makefile>`_
`ToGif <https://github.com/cloud-py-api/nc_py_api/blob/main/examples/as_app/to_gif/Makefile>`_ ,
`nc_py_api <https://github.com/cloud-py-api/nc_py_api/blob/main/scripts/dev_register.sh>`_

During the execution of `php occ app_ecosystem_v2:app:register`, the **enabled_handler** will be called,
as we pass the flag ``-e``, meaning ``enable after registration``.

This is likely all you need to start debugging and developing an application for Nextcloud.

Pack & Deploy
-------------

Before reading this chapter, please review the basic information about deployment
and the currently supported types of
`deployments configurations <https://cloud-py-api.github.io/app_ecosystem_v2/DeployConfigurations.html>`_ in the AppEcosystem documentation.

to-do

From skeleton to ToGif
----------------------

to-do
