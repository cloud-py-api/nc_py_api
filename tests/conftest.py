import contextlib
from io import BytesIO
from os import environ, path
from random import randbytes
from typing import Optional, Union

import gfixture_set_env  # noqa
import pytest
from PIL import Image

from nc_py_api import Nextcloud, NextcloudApp, NextcloudException, _session  # noqa

_TEST_FAILED_INCREMENTAL: dict[str, dict[tuple[int, ...], str]] = {}

NC_CLIENT = None if environ.get("SKIP_NC_CLIENT_TESTS", False) else Nextcloud()
if environ.get("SKIP_AE_TESTS", False):
    NC_APP = None
else:
    NC_APP = NextcloudApp(user="admin")
    if "app_ecosystem_v2" not in NC_APP.capabilities:
        NC_APP = None
if NC_CLIENT is None and NC_APP is None:
    raise EnvironmentError("Tests require at least Nextcloud or NextcloudApp.")


@pytest.fixture(scope="session")
def nc_version() -> _session.ServerVersion:
    return NC_APP.srv_version if NC_APP else NC_CLIENT.srv_version


@pytest.fixture(scope="session")
def nc_client() -> Optional[Nextcloud]:
    if NC_CLIENT is None:
        pytest.skip("Need Client mode")
    return NC_CLIENT


@pytest.fixture(scope="session")
def nc_app() -> Optional[NextcloudApp]:
    if NC_APP is None:
        pytest.skip("Need App mode")
    return NC_APP


@pytest.fixture(scope="session")
def nc_any() -> Union[Nextcloud, NextcloudApp]:
    """Marks a test to run once for any of the modes."""
    return NC_APP if NC_APP else NC_CLIENT


@pytest.fixture(scope="session")
def nc(request):
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


def pytest_collection_modifyitems(items):
    for item in items:
        require_nc = [i for i in item.own_markers if i.name == "require_nc"]
        if require_nc:
            min_major = require_nc[0].kwargs["major"]
            min_minor = require_nc[0].kwargs.get("minor", 0)
            srv_ver = NC_APP.srv_version if NC_APP else NC_CLIENT.srv_version
            if srv_ver["major"] < min_major:
                item.add_marker(pytest.mark.skip(reason=f"Need NC>={min_major}"))
            elif srv_ver["major"] == min_major and srv_ver["minor"] < min_minor:
                item.add_marker(pytest.mark.skip(reason=f"Need NC>={min_major}.{min_minor}"))


def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords and call.excinfo is not None:
        # the test has failed
        cls_name = str(item.cls)  # retrieve the class name of the test
        # Retrieve the index of the test (if parametrize is used in combination with incremental)
        parametrize_index = tuple(item.callspec.indices.values()) if hasattr(item, "callspec") else ()
        test_name = item.originalname or item.name  # retrieve the name of the test function
        # store in _test_failed_incremental the original name of the failed test
        _TEST_FAILED_INCREMENTAL.setdefault(cls_name, {}).setdefault(parametrize_index, test_name)


def pytest_runtest_setup(item):
    if "incremental" in item.keywords:
        cls_name = str(item.cls)
        if cls_name in _TEST_FAILED_INCREMENTAL:  # check if a previous test has failed for this class
            # retrieve the index of the test (if parametrize is used in combination with incremental)
            parametrize_index = tuple(item.callspec.indices.values()) if hasattr(item, "callspec") else ()
            # retrieve the name of the first test function to fail for this class name and index
            test_name = _TEST_FAILED_INCREMENTAL[cls_name].get(parametrize_index, None)
            # if name found, test has failed for the combination of class name & test name
            if test_name is not None:
                pytest.xfail("previous test failed ({})".format(test_name))


@pytest.fixture(scope="session")
def rand_bytes() -> bytes:
    """Returns 64 bytes from `test_64_bytes.bin` file."""
    return randbytes(64)


def init_filesystem_for_user(nc_any, rand_bytes):
    """
    /test_empty_dir
    /test_empty_dir_in_dir/test_empty_child_dir
    /test_dir
    /test_dir/subdir/
    /test_dir/subdir/test_empty_text.txt
    /test_dir/subdir/test_64_bytes.bin
    /test_dir/subdir/test_12345_text.txt
    /test_dir/subdir/test_generated_image.png
    /test_dir/test_empty_child_dir/
    /test_dir/test_empty_text.txt
    /test_dir/test_64_bytes.bin
    /test_dir/test_12345_text.txt
    /test_dir/test_generated_image.png
    /test_empty_text.txt
    /test_64_bytes.bin
    /test_12345_text.txt
    /test_generated_image.png
    /test_dir_tmp
    """
    clean_filesystem_for_user(nc_any)
    im = BytesIO()
    Image.linear_gradient("L").resize((768, 768)).save(im, format="PNG")
    nc_any.files.mkdir("/test_empty_dir")
    nc_any.files.makedirs("/test_empty_dir_in_dir/test_empty_child_dir")
    nc_any.files.makedirs("/test_dir/subdir")
    nc_any.files.mkdir("/test_dir/test_empty_child_dir/")
    nc_any.files.mkdir("/test_dir_tmp")

    def init_folder(folder: str = ""):
        nc_any.files.upload(path.join(folder, "test_empty_text.txt"), content=b"")
        nc_any.files.upload(path.join(folder, "test_64_bytes.bin"), content=rand_bytes)
        nc_any.files.upload(path.join(folder, "test_12345_text.txt"), content="12345")
        im.seek(0)
        nc_any.files.upload(path.join(folder, "test_generated_image.png"), content=im.read())

    init_folder()
    init_folder("test_dir")
    init_folder("test_dir/subdir")


def clean_filesystem_for_user(nc_any):
    clean_up_list = [
        "test_empty_dir",
        "test_empty_dir_in_dir",
        "test_dir",
        "test_dir_tmp",
        "test_empty_text.txt",
        "test_64_bytes.bin",
        "test_12345_text.txt",
        "test_generated_image.png",
    ]
    for i in clean_up_list:
        nc_any.files.delete(i, not_fail=True)


@pytest.fixture(autouse=True, scope="session")
def tear_up_down(nc_any, rand_bytes):
    if NC_CLIENT:
        # create two additional groups
        environ["TEST_GROUP_BOTH"] = "test_nc_py_api_group_both"
        environ["TEST_GROUP_USER"] = "test_nc_py_api_group_user"
        with contextlib.suppress(NextcloudException):
            NC_CLIENT.users_groups.delete(environ["TEST_GROUP_BOTH"])
        with contextlib.suppress(NextcloudException):
            NC_CLIENT.users_groups.delete(environ["TEST_GROUP_USER"])
        NC_CLIENT.users_groups.create(group_id=environ["TEST_GROUP_BOTH"])
        NC_CLIENT.users_groups.create(group_id=environ["TEST_GROUP_USER"])
        # create two additional users
        environ["TEST_ADMIN_ID"] = "test_nc_py_api_admin"
        environ["TEST_ADMIN_PASS"] = "az1dcaNG4c42"
        environ["TEST_USER_ID"] = "test_nc_py_api_user"
        environ["TEST_USER_PASS"] = "DC89GvaR42lk"
        with contextlib.suppress(NextcloudException):
            NC_CLIENT.users.delete(environ["TEST_ADMIN_ID"])
        with contextlib.suppress(NextcloudException):
            NC_CLIENT.users.delete(environ["TEST_USER_ID"])
        NC_CLIENT.users.create(
            environ["TEST_ADMIN_ID"], password=environ["TEST_ADMIN_PASS"], groups=["admin", environ["TEST_GROUP_BOTH"]]
        )
        NC_CLIENT.users.create(
            environ["TEST_USER_ID"],
            password=environ["TEST_USER_PASS"],
            groups=[environ["TEST_GROUP_BOTH"], environ["TEST_GROUP_USER"]],
        )
    init_filesystem_for_user(nc_any, rand_bytes)  # currently we initialize filesystem only for admin

    yield

    clean_filesystem_for_user(nc_any)
    if NC_CLIENT:
        NC_CLIENT.users.delete(environ["TEST_ADMIN_ID"])
        NC_CLIENT.users.delete(environ["TEST_USER_ID"])
        NC_CLIENT.users_groups.delete(environ["TEST_GROUP_BOTH"])
        NC_CLIENT.users_groups.delete(environ["TEST_GROUP_USER"])
