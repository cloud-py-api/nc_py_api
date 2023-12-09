Writing Nextcloud App with UI
=============================

.. note:: It is advisable to have experience writing PHP applications for Nextcloud,
    since the UI of applications not written in PHP is exactly the same.

One of the most interesting features is the ability to register a page in the Nextcloud Top Menu.

Full source of UI example can be found here:
`UiExample <https://github.com/cloud-py-api/nc_py_api/blob/main/examples/as_app/ui_example/lib/main.py>`_

Here we will simply describe in detail what happens in the example.

.. code-block:: python

    if enabled:
        nc.ui.resources.set_initial_state(
            "top_menu", "first_menu", "ui_example_state", {"initial_value": "test init value"}
        )
        nc.ui.resources.set_script("top_menu", "first_menu", "js/ui_example-main")
        nc.ui.top_menu.register("first_menu", "UI example", "img/icon.svg")

**set_initial_state** is analogue of PHP ``OCP\AppFramework\Services\IInitialState::provideInitialState``

**set_script** is analogue of PHP ``Util::addScript``

There is also **set_style** (``Util::addStyle``) that can be used for CSS files and works the same way as **set_script**.

Backend
-------

.. code-block:: python

    class Button1Format(BaseModel):
        initial_value: str


    @APP.post("/verify_initial_value")
    async def verify_initial_value(
        _nc: typing.Annotated[NextcloudApp, Depends(nc_app)],
        input1: Button1Format,
    ):
        print("Old value: ", input1.initial_value)
        return responses.JSONResponse(content={"initial_value": str(random.randint(0, 100))}, status_code=200)


    class FileInfo(BaseModel):
        getlastmodified: str
        getetag: str
        getcontenttype: str
        fileid: int
        permissions: str
        size: int
        getcontentlength: int
        favorite: int


    @APP.post("/nextcloud_file")
    async def nextcloud_file(
        _nc: typing.Annotated[NextcloudApp, Depends(nc_app)],
        args: dict,
    ):
        print(args["file_info"])
        return responses.Response()

Here is defining two endpoints for test purposes.

The first is to get the current initial state of the page when the button is clicked.

Second one is receiving a default information about file in the Nextcloud.

Frontend
--------

The frontend part is the same as the default Nextcloud apps, with slightly different URL generation since all requests are sent through the AppAPI.

JS Frontend part is covered by AppAPI documentation: ``to_do``

Important notes
---------------

We do not call ``top_menu.unregister`` or ``resources.delete_script`` as during uninstalling of application **AppAPI** will automatically remove this.

.. note:: Recommended way is to manually clean all stuff and probably if it was not an example, we would call all unregister and cleanup stuff during ``disabling``.


All resources of ExApp should be avalaible and mounted to webserver(**FastAPI** + **uvicorn** are used by default for this).

.. note:: This is in case you have custom folders that Nextcloud instance should have access.


*P.S.: If you are missing some required stuff for the UI part, please inform us, and we will consider adding it.*
