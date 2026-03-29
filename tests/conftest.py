import asyncio
from os import environ
from typing import Optional, Union

import pytest

from nc_py_api import Nextcloud, NextcloudApp, _session

from . import gfixture_set_env  # noqa

_TEST_FAILED_INCREMENTAL: dict[str, dict[tuple[int, ...], str]] = {}

NC_CLIENT = None if environ.get("SKIP_NC_CLIENT_TESTS", False) else Nextcloud()
NC_CLIENT_ASYNC = NC_CLIENT
if environ.get("SKIP_AA_TESTS", False):
    NC_APP = None
    NC_APP_ASYNC = None
else:
    NC_APP = NextcloudApp(user="admin")
    if "app_api" not in asyncio.get_event_loop().run_until_complete(NC_APP._session.capabilities):
        NC_APP = None
    NC_APP_ASYNC = NC_APP
if NC_CLIENT is None and NC_APP is None:
    raise EnvironmentError("Tests require at least Nextcloud or NextcloudApp.")


@pytest.fixture(scope="session")
async def nc_version() -> _session.ServerVersion:
    return await NC_APP.srv_version if NC_APP else await NC_CLIENT.srv_version


@pytest.fixture(scope="session")
def nc_client() -> Optional[Nextcloud]:
    if NC_CLIENT is None:
        pytest.skip("Need Client mode")
    return NC_CLIENT


@pytest.fixture(scope="session")
def anc_client() -> Optional[Nextcloud]:
    if NC_CLIENT is None:
        pytest.skip("Need Async Client mode")
    return NC_CLIENT


@pytest.fixture(scope="session")
def nc_app() -> Optional[NextcloudApp]:
    if NC_APP is None:
        pytest.skip("Need App mode")
    return NC_APP


@pytest.fixture(scope="session")
def anc_app() -> Optional[NextcloudApp]:
    if NC_APP is None:
        pytest.skip("Need Async App mode")
    return NC_APP


@pytest.fixture(scope="session")
def nc_any() -> Union[Nextcloud, NextcloudApp]:
    """Marks a test to run once for any of the modes."""
    return NC_APP if NC_APP else NC_CLIENT


@pytest.fixture(scope="session")
def anc_any() -> Union[Nextcloud, NextcloudApp]:
    """Marks a test to run once for any of the modes."""
    return NC_APP if NC_APP else NC_CLIENT


@pytest.fixture(scope="session")
def nc(request) -> Union[Nextcloud, NextcloudApp]:
    """Marks a test to run for both modes if possible."""
    return request.param


@pytest.fixture(scope="session")
def anc(request) -> Union[Nextcloud, NextcloudApp]:
    """Marks a test to run for both modes if possible."""
    return request.param


def pytest_generate_tests(metafunc):
    if "nc" in metafunc.fixturenames:
        values_ids = []
        values = []
        if NC_CLIENT is not None:
            values.append(NC_CLIENT)
            values_ids.append("client")
        if NC_APP is not None:
            values.append(NC_APP)
            values_ids.append("app")
        metafunc.parametrize("nc", values, ids=values_ids)
    if "anc" in metafunc.fixturenames:
        values_ids = []
        values = []
        if NC_CLIENT is not None:
            values.append(NC_CLIENT)
            values_ids.append("client")
        if NC_APP is not None:
            values.append(NC_APP)
            values_ids.append("app")
        metafunc.parametrize("anc", values, ids=values_ids)


def pytest_collection_modifyitems(items):
    for item in items:
        require_nc = [i for i in item.own_markers if i.name == "require_nc"]
        if require_nc:
            min_major = require_nc[0].kwargs["major"]
            min_minor = require_nc[0].kwargs.get("minor", 0)
            srv_ver = asyncio.get_event_loop().run_until_complete(
                NC_APP._session.nc_version if NC_APP else NC_CLIENT._session.nc_version
            )
            if srv_ver["major"] < min_major:
                item.add_marker(pytest.mark.skip(reason=f"Need NC>={min_major}"))
            elif srv_ver["major"] == min_major and srv_ver["minor"] < min_minor:
                item.add_marker(pytest.mark.skip(reason=f"Need NC>={min_major}.{min_minor}"))


def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords and call.excinfo is not None:
        cls_name = str(item.cls)
        parametrize_index = tuple(item.callspec.indices.values()) if hasattr(item, "callspec") else ()
        test_name = item.originalname or item.name
        _TEST_FAILED_INCREMENTAL.setdefault(cls_name, {}).setdefault(parametrize_index, test_name)


def pytest_runtest_setup(item):
    if "incremental" in item.keywords:
        cls_name = str(item.cls)
        if cls_name in _TEST_FAILED_INCREMENTAL:
            parametrize_index = tuple(item.callspec.indices.values()) if hasattr(item, "callspec") else ()
            test_name = _TEST_FAILED_INCREMENTAL[cls_name].get(parametrize_index, None)
            if test_name is not None:
                pytest.xfail("previous test failed ({})".format(test_name))
