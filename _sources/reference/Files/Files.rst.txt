File System
===========

The Files API is universal for both modes and provides all the necessary methods for working with the Nextcloud file system.
Refer to the `Files examples <https://github.com/cloud-py-api/nc_py_api/tree/main/examples/as_client/files>`_ to see how to use them nicely.

All File APIs are designed to work relative to the current user.

.. autoclass:: nc_py_api.files.files.FilesAPI
    :members:

.. autoclass:: nc_py_api.files.FsNodeInfo
    :members:

.. autoclass:: nc_py_api.files.FsNode
    :members:

.. autoclass:: nc_py_api.files.FilePermissions
    :members:

.. autoclass:: nc_py_api.files.SystemTag
    :members:

.. autoclass:: nc_py_api.files.LockType
    :members:

.. autoclass:: nc_py_api.files.FsNodeLockInfo
    :members:

.. autoclass:: nc_py_api.files.ActionFileInfo
    :members: fileId, name, directory, etag, mime, fileType, size, favorite, permissions, mtime, userId, instanceId, to_fs_node

.. autoclass:: nc_py_api.files.ActionFileInfoEx
    :members: files
