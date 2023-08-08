.. _options:

Options
-------

.. automodule:: nc_py_api.options
   :members:

Usage examples
^^^^^^^^^^^^^^

Using kwargs
""""""""""""

.. note:: The names of the options if you wish to specify it in ``kwargs`` is **lowercase**.

.. code-block:: python

    nc_client = Nextcloud(xdebug_session="PHPSTORM", npa_nc_cert=False)

Will set `XDEBUG_SESSION` to ``"PHPSTORM"`` and `NPA_NC_CERT` to ``False``.

With .env
"""""""""

Place **.env** file in your project's directory, and it will be automatically loaded using `dotenv <https://github.com/theskumar/python-dotenv>`_

Modifying at module level
"""""""""""""""""""""""""

Import **nc_py_api** and modify options by setting values you need directly in **nc_py_api.options**,
and all newly created classes will respect that.

.. code-block:: python

    import nc_py_api

    nc_py_api.options.NPA_TIMEOUT = None
    nc_py_api.options.NPA_TIMEOUT_DAV = None

.. note:: In case you debugging PHP code it is always a good idea to set **Timeouts** to ``None``.
