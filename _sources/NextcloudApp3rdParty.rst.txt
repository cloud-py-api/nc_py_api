Packaging 3rd party software as a Nextcloud Application
=======================================================

This chapter explains how you can package any 3rd party software to be compatible with Nextcloud.
You should already be familiar with :doc:`NextcloudApp` before reading this part.

You should also have a bit of knowledge about classic PHP Nextcloud apps and `how to develop them <https://docs.nextcloud.com/server/stable/developer_manual/app_development/index.html>`_.

Architecture
------------

The packaged ExApp will contain two pieces of software:

#. The ExApp itself which is talking to Nextcloud directly and responsible for the whole lifecycle.
#. The 3rd party software you want to package.
#. Frontend code which will be loaded by Nextcloud to display your iframe.

Due to current restrictions of ExApps they can only utilize a single port, which means all requests for the 3rd part software have to be proxied through the ExApp.
This will be improved in future released, by allowing multiple ports, so that no proxying is necessary anymore.

Everything will be packaged into a single Docker image which will be used for deployments.
Therefore it is an advantage if the 3rd party software is already able to run inside a Docker container and has a public Docker image available.

Steps
------------------

Creating the ExApp
^^^^^^^^^^^^^^^^^^

Please follow the instructions in :doc:`NextcloudApp` and then return here.

Adding the frontend
^^^^^^^^^^^^^^^^^^^

To be able to access the 3rd party software via the browser it is necessary to embed an iframe into Nextcloud.
The frontend has to be added in the same way how you add it in a classic PHP app.
The iframe ``src`` needs to point to ``/apps/app_api/proxy/APP_ID``, but it is necessary to use the ``generateUrl`` method to ensure the path will also work with Nextcloud instances hosted at a sub-path.
If you require some features like clipboard read/write you need to allow them for the iframe using the ``allow`` attribute.

To now show the frontend inside Nextcloud add the following to your enabled handler:

.. code-block:: python

    def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
        if enabled:
            nc.ui.resources.set_script("top_menu", "APP_ID", "js/APP_ID-main")
            nc.ui.top_menu.register("APP_ID", "App Name", "img/app.svg")
        else:
            nc.ui.resources.delete_script("top_menu", "APP_ID", "js/APP_ID-main")
            nc.ui.top_menu.unregister("APP_ID")
        return ""

Proxying the requests
^^^^^^^^^^^^^^^^^^^^^

For proxying the requests to the 3rd party software you need to register a new route:

.. code-block:: python

    @APP.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
    async def proxy_requests(request: Request, path: str):
        pass

This route should have the lowest priority of all your routes, as it catches all requests that didn't match any previous route.

In this request handler you need to send a new HTTP request to the 3rd party software and copy all incoming parameters like sub-path, query parameters, body and headers.
When returning the response including body, headers and status code, make sure to add or override the CSP and CORS headers if necessary.

Adjusting the Dockerfile
^^^^^^^^^^^^^^^^^^^^^^^^

The Dockerfile should be based on the 3rd party software you want to package.
In case a Docker image is already available you should use that, otherwise you need to first create your own Docker image (it doesn't have to be a separate image, it can just be a stage in the Dockerfile for your ExApp).

The 3rd party software needs to be adapted to be able to handle the proxied requests and generated correct URLs in the frontend.
Depending on how the software works this might only be a config option you need to set or you need to modify the source code within the Docker image (and potentially rebuild the software afterwards).
The root path of the software will be hosted at ``/index.php/apps/app_api/proxy/APP_ID`` which is the same location that was configured in the iframe ``src``.

After these steps you can just continue with the normal ExApp Dockerfile steps of installing the dependencies and copying the source code.
Be aware that you will need to install Python manually in your image in case the Docker image you used so far doesn't include it.

At the end you will have to add a custom entrypoint script that runs the ExApp and the 3rd party software side-by-side to allow them to live in the same container.
