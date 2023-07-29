from os import environ, path
from subprocess import run

import pytest
from gfixture import NC_TO_TEST

from nc_py_api import Nextcloud

# These tests should be run only on GitHub and only in special environment.


@pytest.mark.skipif("NC_AUTH_USER" not in environ or "NC_AUTH_PASS" not in environ, reason="Needs login & paasword.")
@pytest.mark.skipif(not isinstance(NC_TO_TEST[:1][0], Nextcloud), reason="Not available for NextcloudApp.")
@pytest.mark.skipif(environ.get("CI", None) is None, reason="run only on GitHub")
def test_password_confirmation(nc):
    # patch "PasswordConfirmationMiddleware.php" decreasing asking before Password Confirmation from 30 min to 15 secs
    dir_path = path.dirname((path.dirname(path.dirname((path.dirname(path.abspath(__file__)))))))
    assert dir_path == ""
    run(["patch", "-p", "-i", dir_path], cwd=dir_path, check=True)
