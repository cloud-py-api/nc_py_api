.. py:currentmodule:: nc_py_api.ex_app

External Application
====================

Constants
---------

.. autoclass:: LogLvl
    :members:

Special functions
-----------------

.. autofunction:: persistent_storage

.. autofunction:: verify_version

User Interface(UI)
------------------

UI methods should be accessed with the help of :class:`~nc_py_api.nextcloud.NextcloudApp`

.. code-block:: python

    # this is an example, in most cases you will get `NextcloudApp` class instance as input param.
    nc = NextcloudApp()
    nc.ex_app.ui.files_dropdown_menu.register(...)

.. autoclass:: nc_py_api.ex_app.ui.ui.UiApi
    :members:

.. automodule:: nc_py_api.ex_app.ui.files_actions
    :members:

.. autoclass:: nc_py_api.ex_app.ui.files_actions._UiFilesActionsAPI
    :members:

.. automodule:: nc_py_api.ex_app.ui.top_menu
    :members:

.. autoclass:: nc_py_api.ex_app.ui.top_menu._UiTopMenuAPI
    :members:

.. autoclass:: nc_py_api.ex_app.ui.resources._UiResources
    :members:

.. autoclass:: nc_py_api.ex_app.ui.resources.UiInitState
    :members:

.. autoclass:: nc_py_api.ex_app.ui.resources.UiScript
    :members:

.. autoclass:: nc_py_api.ex_app.ui.resources.UiStyle
    :members:

.. autoclass:: nc_py_api.ex_app.ui.settings.SettingsField
    :members:

.. autoclass:: nc_py_api.ex_app.ui.settings.SettingsForm
    :members:

.. autoclass:: nc_py_api.ex_app.ui.settings.SettingsFieldType
    :members:

.. autoclass:: nc_py_api.ex_app.ui.settings._DeclarativeSettingsAPI
    :members:

.. autoclass:: nc_py_api.ex_app.providers.providers.ProvidersApi
    :members:

.. autoclass:: nc_py_api.ex_app.providers.task_processing.ShapeType
    :members:

.. autoclass:: nc_py_api.ex_app.providers.task_processing.ShapeEnumValue
    :members:

.. autoclass:: nc_py_api.ex_app.providers.task_processing.ShapeDescriptor
    :members:

.. autoclass:: nc_py_api.ex_app.providers.task_processing.TaskType
    :members:

.. autoclass:: nc_py_api.ex_app.providers.task_processing.TaskProcessingProvider
    :members:

.. autoclass:: nc_py_api.ex_app.providers.task_processing._TaskProcessingProviderAPI
    :members:

.. autoclass:: nc_py_api.ex_app.occ_commands.OccCommand
    :members:

.. autoclass:: nc_py_api.ex_app.occ_commands.OccCommandsAPI
    :members:
