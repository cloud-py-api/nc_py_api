Setting up dev environment
==========================

We highly recommend to use `Julius Haertl docker setup <https://github.com/juliushaertl/nextcloud-docker-dev>`_ for Nextcloud dev setup.

Development of `nc-py-api` can be done on any OS as it is a **pure** Python package.

Suggested IDE: **PyCharm**, but of course you can use any IDE you like for this like **VS Code** or **Vim**.

Steps to setup up the development environment:

#. Setup Nextcloud locally or remotely.
#. Install `AppEcosystem <https://github.com/cloud-py-api/app_ecosystem_v2>`_, follow it's steps to register ``deploy daemon`` if needed.
#. Clone the `nc_py_api <https://github.com/cloud-py-api/nc_py_api>`_ with :command:`shell`::

    git clone https://github.com/cloud-py-api/nc_py_api.git

#. Set current working dir to the root folder of cloned **nc_py_api** with :command:`shell`::

    cd nc_py_api

#. Create and activate Virtual Environment with :command:`shell`::

    python3 -m venv env

#. Activate Python Virtual Environment with :command:`shell`::

    source ./env/bin/activate

#. Update ``pip`` to the last version with :command:`pip`::

    python3 -m pip install --upgrade pip

#. Install dev-dependencies with :command:`pip`::

    pip install ".[dev]"

#. Install `pre-commit` hooks with :command:`shell`::

    pre-commit install

#. If ``deploy daemon`` is registered for AppEcosystem, register **nc_py_api** as an application with :command:`shell`::

    make register28

#. In ``tests/gfixture.py`` edit ``NC_AUTH_USER`` and ``NC_AUTH_PASS``, if they are different in your setup.
#. Run tests to check that everything works with :command:`shell`::

    python3 -m pytest

#. Install documentation dependencies if needed with :command:`pip`::

    pip install ".[docs]"

#. You can easy build documentation with :command:`shell`::

    make docs

#. **Your setup is ready for the developing nc_py_api and Applications based on it. Best of Luck!**
