import pytest
from gfixture import NC_TO_TEST

from nc_py_api import Share, SharePermissions, ShareType


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_create_list_delete_shares(nc):
    nc.files.upload("share_test", content="")
    try:
        result = nc.files_sharing.get_list()
        assert isinstance(result, list)
        n_shares = len(result)
        new_share = nc.files_sharing.create("share_test", SharePermissions.PERMISSION_READ, ShareType.TYPE_LINK)
        assert isinstance(new_share, Share)
        assert n_shares + 1 == len(nc.files_sharing.get_list())
        nc.files_sharing.delete(new_share)
        assert n_shares == len(nc.files_sharing.get_list())
    finally:
        nc.files.delete("share_test")
