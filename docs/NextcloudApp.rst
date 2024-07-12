Writing a Nextcloud Application
===============================

This chapter assumes that you are already familiar with the `concepts <https://cloud-py-api.github.io/app_api/Concepts.html>`_ of the AppAPI.

As a first step, let's take a look at the structure of a basic Python application.

Skeleton
--------

.. code-block:: python

    from contextlib import asynccontextmanager

    from fastapi import FastAPI
    from nc_py_api import NextcloudApp
    from nc_py_api.ex_app import AppAPIAuthMiddleware, LogLvl, run_app, set_handlers


    @asynccontextmanager
    async def lifespan(app: FastAPI):
        set_handlers(app, enabled_handler)
        yield


    APP = FastAPI(lifespan=lifespan)
    APP.add_middleware(AppAPIAuthMiddleware)  # set global AppAPI authentication middleware


    def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
        # This will be called each time application is `enabled` or `disabled`
        # NOTE: `user` is unavailable on this step, so all NC API calls that require it will fail as unauthorized.
        print(f"enabled={enabled}")
        if enabled:
            nc.log(LogLvl.WARNING, f"Hello from {nc.app_cfg.app_name} :)")
        else:
            nc.log(LogLvl.WARNING, f"Bye bye from {nc.app_cfg.app_name} :(")
        # In case of an error, a non-empty short string should be returned, which will be shown to the NC administrator.
        return ""


    if __name__ == "__main__":
        # Wrapper around `uvicorn.run`.
        # You are free to call it directly, with just using the `APP_HOST` and `APP_PORT` variables from the environment.
        run_app("main:APP", log_level="trace")

What's going on in the skeleton?

In `FastAPI lifespan <https://fastapi.tiangolo.com/advanced/events/?h=lifespan#lifespan>`_ we call the ``set_handlers`` function to further process the application installation logic.

Since this is a simple skeleton application, we only define the ``/enable`` endpoint.

When the application receives a request at the endpoint ``/enable``,
it should register all its functionalities in the cloud and wait for requests from Nextcloud.

So, defining:

.. code-block:: python

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        set_handlers(app, enabled_handler)
        yield

will register an **enabled_handler** that will be called **both when the application is enabled and disabled**.

During the enablement process, you should register all the functionalities that your application offers
in the **enabled_handler** and remove them during the disablement process.

The AppAPI APIs is designed so that you don't have to check whether an endpoint is already registered
(e.g., in case of a malfunction or if the administrator manually altered something in the Nextcloud database).
The AppAPI APIs will not fail, and in such cases, it will simply re-register without error.

If any error prevents your application from functioning, you should provide a brief description in the return instead
of an empty string, and log comprehensive information that will assist the administrator in addressing the issue.

.. code-block:: python

    APP = FastAPI(lifespan=lifespan)
    APP.add_middleware(AppAPIAuthMiddleware)

With help of ``AppAPIAuthMiddleware`` you can add **global** AppAPI authentication for all future endpoints you will define.

.. note:: ``AppAPIAuthMiddleware`` supports **disable_for** optional argument, where you can list all routes for which authentication should be skipped.

Repository with the skeleton sources can be found here: `app-skeleton-python <https://github.com/cloud-py-api/app-skeleton-python>`_

Dockerfile
----------

We decided to keep all the examples and applications in the same format as the usual PHP applications for Nextcloud.

.. code-block::

    ADD cs[s] /app/css
    ADD im[g] /app/img
    ADD j[s] /app/js
    ADD l10[n] /app/l10n
    ADD li[b] /app/lib

This code from dockerfile copies folders of app if they exists to the docker container.

**nc_py_api** will automatically mount ``css``, ``img``, ``js``, ``l10n`` folders to the FastAPI.

.. note:: If you do not want automatic mount happen, pass ``map_app_static=False`` to ``set_handlers``.

Debugging
---------

Debugging an application within Docker and rebuilding it from scratch each time can be cumbersome.
Therefore, a manual deployment option has been specifically designed for this purpose.

First register ``manual_install`` daemon:

.. code-block:: shell

    php occ app_api:daemon:register manual_install "Manual Install" manual-install http host.docker.internal 0

Then, launch your application. Since this is a manual deployment, it's your responsibility to set minimum of the environment variables.
Here they are:

* APP_ID - ID of the application.
* APP_PORT - Port on which application listen for the requests from the Nextcloud.
* APP_HOST - "0.0.0.0"/"127.0.0.1"/other host value.
* APP_SECRET - Shared secret between Nextcloud and Application.
* APP_VERSION - Version of the application.
* AA_VERSION - Version of the AppAPI.
* NEXTCLOUD_URL - URL at which the application can access the Nextcloud API.

You can find values for these environment variables in the **Skeleton** or **ToGif** run configurations.

After launching your application, execute the following command in the Nextcloud container:

.. code-block:: shell

    php occ app_api:app:register YOUR_APP_ID manual_install --json-info \
        "{\"id\":\"YOUR_APP_ID\",\"name\":\"YOUR_APP_DISPLAY_NAME\",\"daemon_config_name\":\"manual_install\",\"version\":\"YOU_APP_VERSION\",\"secret\":\"YOUR_APP_SECRET\",\"scopes\":[\"ALL\"],\"port\":SELECTED_PORT}" \
        --force-scopes --wait-finish

You can see how **nc_py_api** registers in ``scripts/dev_register.sh``.

It's advisable to write these steps as commands in a Makefile for quick use.

Examples for such Makefiles can be found in this repository:
`Skeleton <https://github.com/cloud-py-api/nc_py_api/blob/main/examples/as_app/skeleton/Makefile>`_ ,
`ToGif <https://github.com/cloud-py-api/nc_py_api/blob/main/examples/as_app/to_gif/Makefile>`_ ,
`TalkBot <https://github.com/cloud-py-api/talk_bot_ai_example/blob/main/Makefile>`_ ,
`UiExample <https://github.com/cloud-py-api/ui_example/blob/main/Makefile>`_

During the execution of `php occ app_api:app:register`, the **enabled_handler** will be called

This is likely all you need to start debugging and developing an application for Nextcloud.

Pack & Deploy
-------------

Before reading this chapter, please review the basic information about deployment
and the currently supported types of
`deployments configurations <https://cloud-py-api.github.io/app_api/DeployConfigurations.html>`_ in the AppAPI documentation.

Docker Deploy Daemon
""""""""""""""""""""

Docker images with the application can be deployed both on Docker Hub or on GitHub.
All examples in this repository use GitHub for deployment.

To build the application locally, if you do not have a Mac with Apple Silicon, you will need to install QEMU, to be able
to build image for both **aarch64** and **x64** architectures. Of course it is always your choice and you can support only one type
of CPU and not both, but it is **highly recommended to support both** of them.

First login to preferred docker registry:

.. code-block:: shell

    docker login ghcr.io

After that build and push images to it:

.. code-block:: shell

    docker buildx build --push --platform linux/arm64/v8,linux/amd64 --tag ghcr.io/REPOSITORY_OWNER/APP_ID:N_VERSION .

Where APP_ID can be repository name, and it is up to you to decide.

.. note:: It is not recommended to use only the ``latest`` tag for the application's image, as increasing the version
    of your application will overwrite the previous version, in this case, use several tags to leave the possibility
    of installing previous versions of your application.

From skeleton to ToGif
----------------------

Now it's time to move on to something more complex than just the application skeleton.

Let's consider an example of an application that performs an action with a file when
you click on the drop-down context menu and reports on the work done using notification.

First of all, we modernize info.ixml, add the API groups we need for this to work with **Files** and **Notifications**:

.. code-block:: xml

    <scopes>
        <value>FILES</value>
        <value>NOTIFICATIONS</value>
    </scopes>

.. note:: Full list of avalaible API scopes can be found `here <https://cloud-py-api.github.io/app_api/tech_details/ApiScopes.html>`_.

After that we extend the **enabled** handler and include there registration of the drop-down list element:

.. code-block:: python

    def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
        try:
            if enabled:
                nc.ui.files_dropdown_menu.register_ex("to_gif", "TO GIF", "/video_to_gif", mime="video")
            else:
                nc.ui.files_dropdown_menu.unregister("to_gif")
        except Exception as e:
            return str(e)
        return ""

After that, let's define the **"/video_to_gif"** endpoint that we had registered in previous step:

.. code-block:: python

    @APP.post("/video_to_gif")
    async def video_to_gif(
        files: ActionFileInfoEx,
        nc: Annotated[NextcloudApp, Depends(nc_app)],
        background_tasks: BackgroundTasks,
    ):
        for one_file in files.files:
            background_tasks.add_task(convert_video_to_gif, one_file.to_fs_node(), nc)
        return responses.Response()

We see two parameters ``files`` and ``BackgroundTasks``, let's start with the last one, with **BackgroundTasks**:

FastAPI `BackgroundTasks <https://fastapi.tiangolo.com/tutorial/background-tasks/?h=backgroundtasks#background-tasks>`_ documentation.

Since in most cases, the tasks that the application will perform will depend either on additional network calls or
heavy calculations and we cannot guarantee a fast completion time, it is recommended to always try to return
an empty response (which will be a status of 200) and in the background already slowly perform operations.

The last parameter is a structure describing the action and the file on which it needs to be performed,
which is passed by the AppAPI when clicking on the drop-down context menu of the file.

We use the built-in ``to_fs_node`` method of :py:class:`~nc_py_api.files.ActionFileInfo` to get a standard
:py:class:`~nc_py_api.files.FsNode` class that describes the file and pass the FsNode class instance to the background task.

In the **convert_video_to_gif** function, a standard conversion using ``OpenCV`` from a video file to a GIF image occurs,
and since this is not directly related to working with NextCloud, we will skip this for now.

**ToGif** example `full source <https://github.com/cloud-py-api/nc_py_api/blob/main/examples/as_app/to_gif/lib/main.py>`_ code.

Life wo AppAPIAuthMiddleware
----------------------------

If for some reason you do not want to use global AppAPI authentication **nc_py_api** provides a FastAPI Dependency for authentication your endpoints.

This is a modified endpoint from ``to_gif`` example:

.. code-block:: python

    @APP.post("/video_to_gif")
    async def video_to_gif(
        file: ActionFileInfo,
        nc: Annotated[NextcloudApp, Depends(nc_app)],
        background_tasks: BackgroundTasks,
    ):
        background_tasks.add_task(convert_video_to_gif, file.actionFile.to_fs_node(), nc)
        return Response()


Here we see: **nc: Annotated[NextcloudApp, Depends(nc_app)]**

For those who already know how FastAPI works, everything should be clear by now,
and for those who have not, it is very important to understand that:

    It is a declaration of FastAPI `dependency <https://fastapi.tiangolo.com/tutorial/dependencies/#dependencies>`_ to be executed
    before the code of **video_to_gif** starts execution.

And this required dependency handles authentication and returns an instance of the :py:class:`~nc_py_api.nextcloud.NextcloudApp`
class that allows you to make requests to Nextcloud.

.. note:: NcPyAPI is clever enough to detect whether global authentication handler is enabled, and not perform authentication twice for performance reasons.

This chapter ends here, but the next topics are even more intriguing.
