import pytest
from gfixture import NC_TO_TEST

from nc_py_api import Share, SharePermissions, ShareType


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_available(nc):
    assert nc.files_sharing.available


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_create_list_delete_shares(nc):
    nc.files.upload("share_test.txt", content="")
    try:
        result = nc.files_sharing.get_list()
        assert isinstance(result, list)
        n_shares = len(result)
        new_share = nc.files_sharing.create("share_test.txt", SharePermissions.PERMISSION_READ, ShareType.TYPE_LINK)
        assert isinstance(new_share, Share)
        assert new_share.type == ShareType.TYPE_LINK
        assert not new_share.label
        assert not new_share.note
        assert new_share.mimetype.find("text") != -1
        assert new_share.permissions & SharePermissions.PERMISSION_READ
        assert new_share.url
        assert new_share.path  # to-do: when `upload` will be able to return FsNode object check this too
        assert n_shares + 1 == len(nc.files_sharing.get_list())
        nc.files_sharing.delete(new_share)
        assert n_shares == len(nc.files_sharing.get_list())
    finally:
        nc.files.delete("share_test.txt")
