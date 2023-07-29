from os import environ, path
from subprocess import run

import pytest
from gfixture import NC_TO_TEST

from nc_py_api import Nextcloud, NextcloudException

# These tests should be run only on GitHub and only in special environment.


@pytest.mark.skipif("NC_AUTH_USER" not in environ or "NC_AUTH_PASS" not in environ, reason="Needs login & paasword.")
@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.skipif(environ.get("CI", None) is None, reason="run only on GitHub")
def test_password_confirmation(nc):
    # patch "PasswordConfirmationMiddleware.php" decreasing asking before Password Confirmation from 30 min to 15 secs
    patch_path = path.join(path.dirname(path.abspath(__file__)), "data/nc_pass_confirm.patch")
    cwd_path = path.dirname((path.dirname(path.dirname(path.dirname(path.abspath(__file__))))))
    print(cwd_path)
    run(["patch", "-p", "-i", patch_path], cwd=cwd_path, check=True)
    try:
        nc.users.create("test_cover_user_spec", password="ThisIsA54StrongPassword013")
    except NextcloudException:
        pass
    nc.users.delete("test_cover_user_spec")
    run(["git", "apply", "-R", patch_path], cwd=cwd_path, check=True)
