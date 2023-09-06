import contextlib
from io import BytesIO
from os import environ, path
from random import randbytes

import pytest
from PIL import Image

from nc_py_api import Nextcloud, NextcloudApp, NextcloudException, _session  # noqa

from ..conftest import NC_CLIENT

_TEST_FAILED_INCREMENTAL: dict[str, dict[tuple[int, ...], str]] = {}


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
    /test_dir/subdir/test_generated_image.png       **Favorite**
    /test_dir/test_empty_child_dir/
    /test_dir/test_empty_text.txt
    /test_dir/test_64_bytes.bin
    /test_dir/test_12345_text.txt
    /test_dir/test_generated_image.png              **Favorite**
    /test_empty_text.txt
    /test_64_bytes.bin
    /test_12345_text.txt
    /test_generated_image.png                       **Favorite**
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
        nc_any.files.setfav(path.join(folder, "test_generated_image.png"), True)

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
