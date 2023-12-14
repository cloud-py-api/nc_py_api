import contextlib
from os import environ, path
from subprocess import run
from time import sleep

import pytest

from nc_py_api import NextcloudException

# These tests should be run only on GitHub and only in special environment.


@pytest.mark.skipif("NC_AUTH_USER" not in environ or "NC_AUTH_PASS" not in environ, reason="Needs login & paasword.")
@pytest.mark.skipif(environ.get("CI", None) is None, reason="run only on GitHub")
def test_password_confirmation(nc_client):
    patch_path, cwd_path = _test_password_confirmation()
    nc_client.update_server_info()
    old_adapter = nc_client._session.adapter
    with contextlib.suppress(NextcloudException):
        nc_client.users.create("test_cover_user_spec", password="ThisIsA54StrongPassword013")
    nc_client.users.delete("test_cover_user_spec")
    assert old_adapter != nc_client._session.adapter
    run(["git", "apply", "-R", patch_path], cwd=cwd_path, check=True)


@pytest.mark.asyncio(scope="session")
@pytest.mark.skipif("NC_AUTH_USER" not in environ or "NC_AUTH_PASS" not in environ, reason="Needs login & paasword.")
@pytest.mark.skipif(environ.get("CI", None) is None, reason="run only on GitHub")
async def test_password_confirmation_async(anc_client):
    patch_path, cwd_path = _test_password_confirmation()
    await anc_client.update_server_info()
    old_adapter = anc_client._session.adapter
    with contextlib.suppress(NextcloudException):
        await anc_client.users.create("test_cover_user_spec", password="ThisIsA54StrongPassword013")
    await anc_client.users.delete("test_cover_user_spec")
    assert old_adapter != anc_client._session.adapter
    run(["git", "apply", "-R", patch_path], cwd=cwd_path, check=True)


def _test_password_confirmation() -> tuple[str, str]:
    # patch "PasswordConfirmationMiddleware.php" decreasing asking before Password Confirmation from 30 min to 5 secs
    patch_path = path.join(path.dirname(path.dirname(path.abspath(__file__))), "data/nc_pass_confirm.patch")
    cwd_path = path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
    run(["patch", "-p", "1", "-i", patch_path], cwd=cwd_path, check=True)
    sleep(6)
    return patch_path, cwd_path
