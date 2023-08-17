.. py:currentmodule:: nc_py_api.ex_app

External Application
====================

Constants
---------

.. autoclass:: ApiScope
    :members:

.. autoclass:: LogLvl
    :members:

User Interface(UI)
------------------

UI methods should be accessed with the help of :class:`~nc_py_api.nextcloud.NextcloudApp`

.. code-block:: python

    # this is an example, in most cases you will get `NextcloudApp` class instance as input param.
    nc = NextcloudApp()
    nc.ui.files_dropdown_menu.register(...)

.. autoclass:: nc_py_api.ex_app.ui.ui.UiApi
    :members:

.. automodule:: nc_py_api.ex_app.ui.files
    :members:

.. autoclass:: nc_py_api.ex_app.ui.files._UiFilesActionsAPI
    :members:
