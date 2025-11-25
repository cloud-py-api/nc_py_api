.. py:currentmodule:: nc_py_api.calendar_api

Calendar API
============

.. note:: To make this API work you should install **nc_py_api** with **calendar** extra dependency.

.. code-block:: python

    principal = nc.cal.principal()
    calendars = principal.calendars()  # get list of calendars

``nc.cal`` is usual ``caldav.DAVClient`` object with the same API.

Documentation for ``caldav`` can be found here: `CalDAV <"https://caldav.readthedocs.io/en/latest">`_

.. class:: _CalendarAPI

    Class that encapsulates ``caldav.DAVClient``. Avalaible as **cal** in the Nextcloud class.

    .. note:: You should not call ``close`` or ``request`` methods of CalendarAPI, they will be removed somewhere
        in the future when ``caldav.DAVClient`` will be rewritten(API compatability will remains).
