Writing a Nextcloud Application
===============================

This chapter assumes that you are already familiar with the `concepts <https://cloud-py-api.github.io/app_api/Concepts.html>`_ of the AppAPI.

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

    php occ app_api:daemon:register manual_install "Manual Install" manual-install 0 0 0

Then, launch your application. Since this is a manual deployment, it's your responsibility to set minimum of the environment variables.
Here they are:

* APP_ID - ID of the application.
* APP_PORT - Port on which application listen for the requests from the Nextcloud.
* APP_SECRET - Secret for ``hmac`` signature generation.
* APP_VERSION - Version of the application.
* AE_VERSION - Version of the AppAPI.
* NEXTCLOUD_URL - URL at which the application can access the Nextcloud API.

You can find values for these environment variables in the **Skeleton** or **ToGif** run configurations.

After launching your application, execute the following command in the Nextcloud container:

.. code-block:: shell

    php occ app_api:app:register YOUR_APP_ID manual_install --json-info \
        "{\"appid\":\"YOUR_APP_ID\",\"name\":\"YOUR_APP_DISPLAY_NAME\",\"daemon_config_name\":\"manual_install\",\"version\":\"YOU_APP_VERSION\",\"secret\":\"YOUR_APP_SECRET\",\"host\":\"host.docker.internal\",\"scopes\":{\"required\":[2, 10, 11],\"optional\":[30, 31, 32, 33]},\"port\":SELECTED_PORT,\"protocol\":\"http\",\"system_app\":0}" \
        -e --force-scopes

You can see how **nc_py_api** registers in ``scripts/dev_register.sh``.

It's advisable to write these steps as commands in a Makefile for quick use.

Examples for such Makefiles can be found in this repository:
`Skeleton <https://github.com/cloud-py-api/nc_py_api/blob/main/examples/as_app/skeleton/Makefile>`_ ,
`TalkBot <https://github.com/cloud-py-api/nc_py_api/blob/main/examples/as_app/talk_bot/Makefile>`_
`ToGif <https://github.com/cloud-py-api/nc_py_api/blob/main/examples/as_app/to_gif/Makefile>`_ ,
`nc_py_api <https://github.com/cloud-py-api/nc_py_api/blob/main/scripts/dev_register.sh>`_

During the execution of `php occ app_api:app:register`, the **enabled_handler** will be called,
as we pass the flag ``-e``, meaning ``enable after registration``.

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
        <required>
            <value>FILES</value>
            <value>NOTIFICATIONS</value>
        </required>
        <optional>
        </optional>
    </scopes>

.. note:: Full list of avalaible API scopes can be found `here <https://cloud-py-api.github.io/app_api/tech_details/ApiScopes.html>`_.

After that we extend the **enabled** handler and include there registration of the drop-down list element:

.. code-block:: python

    def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
        try:
            if enabled:
                nc.ui.files_dropdown_menu.register("to_gif", "TO GIF", "/video_to_gif", mime="video")
            else:
                nc.ui.files_dropdown_menu.unregister("to_gif")
        except Exception as e:
            return str(e)
        return ""

After that, let's define the **"/video_to_gif"** endpoint that we had registered in previous step:

.. code-block:: python

    @APP.post("/video_to_gif")
    async def video_to_gif(
        file: UiFileActionHandlerInfo,
        nc: Annotated[NextcloudApp, Depends(nc_app)],
        background_tasks: BackgroundTasks,
    ):
        background_tasks.add_task(convert_video_to_gif, file.actionFile.to_fs_node(), nc)
        return Response()

And this step should be discussed in more detail, since it demonstrates most of the process of working External applications.

Here we see: **nc: Annotated[NextcloudApp, Depends(nc_app)]**

For those who already know how FastAPI works, everything should be clear by now,
and for those who have not, it is very important to understand that:

    It is a declaration of FastAPI `dependency <https://fastapi.tiangolo.com/tutorial/dependencies/#dependencies>`_ to be executed
    before the code of **video_to_gif** starts execution.

And this required dependency handles authentication and returns an instance of the :py:class:`~nc_py_api.nextcloud.NextcloudApp`
class that allows you to make requests to Nextcloud.

.. note:: Every endpoint in your application should be protected with such method, this will ensure that only Nextcloud instance
    will be able to perform requests to the application.

Finally, we are left with two much less interesting parameters, let's start with the last one, with **BackgroundTasks**:

FastAPI `BackgroundTasks <https://fastapi.tiangolo.com/tutorial/background-tasks/?h=backgroundtasks#background-tasks>`_ documentation.

Since in most cases, the tasks that the application will perform will depend either on additional network calls or
heavy calculations and we cannot guarantee a fast completion time, it is recommended to always try to return
an empty response (which will be a status of 200) and in the background already slowly perform operations.

The last parameter is a structure describing the action and the file on which it needs to be performed,
which is passed by the AppAPI when clicking on the drop-down context menu of the file.

We use the built method :py:meth:`~nc_py_api.ex_app.ui.files.UiActionFileInfo.to_fs_node` into the structure to convert it
into a standard :py:class:`~nc_py_api.files.FsNode` class that describes the file and pass the FsNode class instance to the background task.

In the **convert_video_to_gif** function, a standard conversion using ``OpenCV`` from a video file to a GIF image occurs,
and since this is not directly related to working with NextCloud, we will skip this for now.

**ToGif** example `full source <https://github.com/cloud-py-api/nc_py_api/blob/main/examples/as_app/to_gif/src/main.py>`_ code.

This chapter ends here, but the next topics are even more intriguing.
