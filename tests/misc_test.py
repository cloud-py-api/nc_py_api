import pytest

from nc_py_api import check_error, NextcloudException


@pytest.mark.parametrize("code", (995, 996, 997, 998, 999, 1000))
def test_check_error(code):
    if 996 <= code <= 999:
        with pytest.raises(NextcloudException):
            check_error(code)
    else:
        check_error(code)
