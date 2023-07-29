from os import environ, path
from subprocess import run
from time import sleep

import pytest
from gfixture import NC

from nc_py_api import NextcloudException

# These tests should be run only on GitHub and only in special environment.


@pytest.mark.skipif("NC_AUTH_USER" not in environ or "NC_AUTH_PASS" not in environ, reason="Needs login & paasword.")
@pytest.mark.skipif(NC is None, reason="Not available for NextcloudApp.")
@pytest.mark.skipif(environ.get("CI", None) is None, reason="run only on GitHub")
def test_password_confirmation():
    # patch "PasswordConfirmationMiddleware.php" decreasing asking before Password Confirmation from 30 min to 15 secs
    patch_path = path.join(path.dirname(path.abspath(__file__)), "data/nc_pass_confirm.patch")
    cwd_path = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
    run(["patch", "-p", "1", "-i", patch_path], cwd=cwd_path, check=True)
    sleep(6)
    NC.update_server_info()
    old_adapter = NC._session.adapter
    try:
        NC.users.create("test_cover_user_spec", password="ThisIsA54StrongPassword013")
    except NextcloudException:
        pass
    NC.users.delete("test_cover_user_spec")
    assert old_adapter != NC._session.adapter
    run(["git", "apply", "-R", patch_path], cwd=cwd_path, check=True)
