Installation
============

First it is always a good idea to update ``pip`` to the latest version with :command:`pip`::

    python -m pip install --upgrade pip

To use it as a simple Nextcloud client install it without any additional dependencies with :command:`pip`::

    python -m pip install --upgrade nc_py_api

To use in the Nextcloud Application mode install it with additional ``app`` dependencies with :command:`pip`::

    python -m pip install --upgrade "nc_py_api[app]"

To join the development of **nc_py_api** api install development dependencies with :command:`pip`::

    python -m pip install --upgrade "nc_py_api[dev]"

Or install last dev-version from GitHub with :command:`pip`::

    python -m pip install --upgrade "nc_py_api[dev] @ git+https://github.com/cloud-py-api/nc_py_api"

Congratulations, the next chapter :ref:`first-steps` awaits.

.. note::
    If you have any installation or building questions, you can ask them in the discussions or create a issue
    and we will do our best to help you.
