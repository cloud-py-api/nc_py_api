.. _first-steps:

First steps
===========

For this part, you will need an environment with **nc_py_api** installed and Nextcloud version 26 or higher.

Full support is only available from version ``27.1`` of Nextcloud.


.. note:: In many cases, even if you want to develop an application,
    it's a good idea to first debug and develop part of it as a client.

Basics
^^^^^^

Creating Nextcloud client class
"""""""""""""""""""""""""""""""

.. code-block:: python

    from nc_py_api import Nextcloud


    nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

Where ``nc_auth_pass`` can be usual Nextcloud application password.

To test if this works, let's print the capabilities of the Nextcloud instance:

.. code-block:: python

    from json import dumps

    from nc_py_api import Nextcloud


    nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")
    pretty_capabilities = dumps(nc.capabilities, indent=4, sort_keys=True)
    print(pretty_capabilities)

Checking Nextcloud capabilities
"""""""""""""""""""""""""""""""

In most cases, APIs perform capability checks before invoking them and raise a :class:`~nc_py_api._exceptions.NextcloudMissingCapabilities`
exception if the Nextcloud instance lacks the requisite capability.
However, there are situations where this approach might not be the most convenient,
and you may wish to earlier whether a certain capability is available and active.

To address this need, the ``check_capabilities`` method is provided.
This method offers a straightforward way to proactively check for the existence and status of a particular capability.

Using this method is quite simple:

.. code-block:: python

    import nc_py_api


    nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")
    if nc.check_capabilities("files_sharing"):  # check one capability
        print("Sharing API is not present.")

    # check child values in the same call
    if nc.check_capabilities("files_sharing.api_enabled"):
        print("Sharing API is present, but is not enabled.")

    # check multiply capabilities at one
    missing_cap = nc.check_capabilities(["files_sharing.api_enabled", "user_status.enabled"])
    if missing_cap:
        print(f"Missing capabilities: {missing_cap}")

Files
^^^^^

Getting list of files of User
"""""""""""""""""""""""""""""

This is a hard way to get list of all files recursively:

.. literalinclude:: ../examples/as_client/files/listing.py

This code do the same in one DAV call, but prints **directories** in addition to files:

.. code-block:: python

    from nc_py_api import Nextcloud


    nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")
    print("Files & folders on the instance for the selected user:")
    all_files_folders = nc.files.listdir(depth=-1)
    for obj in all_files_folders:
        print(obj.user_path)

To print only files, you can use list comprehension:

.. code-block:: python

    print("Files on the instance for the selected user:")
    all_files = [i for i in nc.files.listdir(depth=-1) if not i.is_dir]
    for obj in all_files:
        print(obj.user_path)

Uploading a single file
"""""""""""""""""""""""

It is always better to use ``upload_stream`` instead of ``upload`` as it works
with chunks and ``in future`` will support **multi threaded** upload.

.. literalinclude:: ../examples/as_client/files/upload.py

Downloading a single file
"""""""""""""""""""""""""

A very simple example of downloading an image as one piece of data to memory and displaying it.

.. note:: For big files, it is always better to use ``download2stream`` method, as it uses chunks.

.. literalinclude:: ../examples/as_client/files/download.py

Searching for a file
""""""""""""""""""""

Example of using ``file.find()`` to search for file objects.

.. note:: We welcome the idea of how to make the definition of search queries more friendly.

.. literalinclude:: ../examples/as_client/files/find.py

Conclusion
^^^^^^^^^^

Once you have a good understanding of working with files, you can move on to more APIs.

You don't have to learn them all at the same time, but it's good to at least have a general idea, so let's go with
:ref:`more-apis`!
