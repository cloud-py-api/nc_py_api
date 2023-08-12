import datetime

import pytest
from gfixture import NC_TO_TEST

from nc_py_api import (
    NextcloudException,
    NextcloudExceptionNotFound,
    SharePermissions,
    ShareType,
)
from nc_py_api.files.sharing import Share


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_available(nc):
    assert nc.files.sharing.available


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_create_delete(nc):
    nc.files.upload("share_test.txt", content="content of file")
    try:
        new_share = nc.files.sharing.create("share_test.txt", ShareType.TYPE_LINK)
        nc.files.sharing.delete(new_share)
        with pytest.raises(NextcloudExceptionNotFound):
            nc.files.sharing.delete(new_share)
    finally:
        nc.files.delete("share_test.txt")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_share_fields(nc):
    shared_file = nc.files.upload("share_test.txt", content="content of file")
    try:
        new_share = nc.files.sharing.create(shared_file, ShareType.TYPE_LINK, SharePermissions.PERMISSION_READ)
        try:
            get_by_id = nc.files.sharing.get_by_id(new_share.share_id)
            assert new_share.share_type == ShareType.TYPE_LINK
            assert not new_share.label
            assert not new_share.note
            assert new_share.mimetype.find("text") != -1
            assert new_share.permissions & SharePermissions.PERMISSION_READ
            assert new_share.url
            assert new_share.path == shared_file.user_path
            assert get_by_id.share_id == new_share.share_id
            assert get_by_id.path == new_share.path
            assert get_by_id.mimetype == new_share.mimetype
            assert get_by_id.share_type == new_share.share_type
            assert get_by_id.file_owner == new_share.file_owner
            assert get_by_id.share_owner == new_share.share_owner
            assert not get_by_id.share_with
            assert str(get_by_id) == str(new_share)
        finally:
            nc.files.sharing.delete(new_share)
    finally:
        nc.files.delete("share_test.txt")


@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_create_permissions(nc):
    nc.files.makedirs("share_test", exist_ok=True)
    try:
        new_share = nc.files.sharing.create("share_test", ShareType.TYPE_LINK, SharePermissions.PERMISSION_CREATE)
        nc.files.sharing.delete(new_share)
        assert (
            new_share.permissions
            == SharePermissions.PERMISSION_READ | SharePermissions.PERMISSION_CREATE | SharePermissions.PERMISSION_SHARE
        )
        new_share = nc.files.sharing.create("share_test", ShareType.TYPE_LINK, SharePermissions.PERMISSION_DELETE)
        nc.files.sharing.delete(new_share)
        assert (
            new_share.permissions
            == SharePermissions.PERMISSION_READ | SharePermissions.PERMISSION_DELETE | SharePermissions.PERMISSION_SHARE
        )
        new_share = nc.files.sharing.create("share_test", ShareType.TYPE_LINK, SharePermissions.PERMISSION_UPDATE)
        nc.files.sharing.delete(new_share)
        assert (
            new_share.permissions
            == SharePermissions.PERMISSION_READ | SharePermissions.PERMISSION_UPDATE | SharePermissions.PERMISSION_SHARE
        )
    finally:
        nc.files.delete("share_test")


@pytest.mark.parametrize("nc", NC_TO_TEST[:1])
def test_create_public_upload(nc):
    nc.files.makedirs("share_test", exist_ok=True)
    try:
        new_share = nc.files.sharing.create("share_test", ShareType.TYPE_LINK, public_upload=True)
        nc.files.sharing.delete(new_share)
        assert (
            new_share.permissions
            == SharePermissions.PERMISSION_READ
            | SharePermissions.PERMISSION_UPDATE
            | SharePermissions.PERMISSION_SHARE
            | SharePermissions.PERMISSION_DELETE
            | SharePermissions.PERMISSION_CREATE
        )
    finally:
        nc.files.delete("share_test")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_create_password(nc):
    if nc.check_capabilities("spreed"):
        pytest.skip(reason="Talk is not installed.")
    nc.files.upload("share_test.txt", content="content of file")
    try:
        new_share = nc.files.sharing.create("share_test.txt", ShareType.TYPE_LINK, password="s2dDS_z44ad1")
        nc.files.sharing.delete(new_share)
        assert new_share.password
        assert new_share.send_password_by_talk is False
        new_share = nc.files.sharing.create(
            "share_test.txt", ShareType.TYPE_LINK, password="s2dDS_z44ad1", send_password_by_talk=True
        )
        nc.files.sharing.delete(new_share)
        assert new_share.password
        assert new_share.send_password_by_talk is True
    finally:
        nc.files.delete("share_test.txt")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_create_note_label(nc):
    nc.files.upload("share_test.txt", content="content of file")
    try:
        new_share = nc.files.sharing.create("share_test.txt", ShareType.TYPE_LINK, note="This is not", label="label")
        nc.files.sharing.delete(new_share)
        assert new_share.note == "This is not"
        assert new_share.label == "label"
    finally:
        nc.files.delete("share_test.txt")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_create_expire_time(nc):
    nc.files.upload("share_test.txt", content="content of file")
    try:
        expire_time = datetime.datetime.now() + datetime.timedelta(days=1)
        expire_time = expire_time.replace(hour=0, minute=0, second=0, microsecond=0)
        new_share = nc.files.sharing.create("share_test.txt", ShareType.TYPE_LINK, expire_date=expire_time)
        nc.files.sharing.delete(new_share)
        assert new_share.expire_date == expire_time
        with pytest.raises(NextcloudException):
            nc.files.sharing.create(
                "share_test.txt", ShareType.TYPE_LINK, expire_date=datetime.datetime.now() - datetime.timedelta(days=1)
            )
        new_share.raw_data["expiration"] = "invalid time"
        new_share2 = Share(new_share.raw_data)
        assert new_share2.expire_date == datetime.datetime(1970, 1, 1)
    finally:
        nc.files.delete("share_test.txt")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_list(nc):
    shared_file = nc.files.upload("share_test.txt", content="content of file")
    try:
        result = nc.files.sharing.get_list()
        assert isinstance(result, list)
        n_shares = len(result)
        new_share = nc.files.sharing.create(shared_file, ShareType.TYPE_LINK)
        assert isinstance(new_share, Share)
        shares_list = nc.files.sharing.get_list()
        assert n_shares + 1 == len(shares_list)
        share_by_id = nc.files.sharing.get_by_id(shares_list[-1].share_id)
        nc.files.sharing.delete(new_share)
        assert n_shares == len(nc.files.sharing.get_list())
        assert share_by_id.share_owner == shares_list[-1].share_owner
        assert share_by_id.mimetype == shares_list[-1].mimetype
        assert share_by_id.password == shares_list[-1].password
        assert share_by_id.permissions == shares_list[-1].permissions
        assert share_by_id.url == shares_list[-1].url
    finally:
        nc.files.delete("share_test.txt")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_create_update(nc):
    if nc.check_capabilities("spreed"):
        pytest.skip(reason="Talk is not installed.")
    nc.files.makedirs("share_test", exist_ok=True)
    try:
        new_share = nc.files.sharing.create(
            "share_test",
            ShareType.TYPE_LINK,
            permissions=SharePermissions.PERMISSION_READ
            + SharePermissions.PERMISSION_SHARE
            + SharePermissions.PERMISSION_UPDATE,
        )
        update_share = nc.files.sharing.update(new_share, password="s2dDS_z44ad1")
        assert update_share.password
        assert update_share.permissions != SharePermissions.PERMISSION_READ + SharePermissions.PERMISSION_SHARE
        update_share = nc.files.sharing.update(
            new_share, permissions=SharePermissions.PERMISSION_READ + SharePermissions.PERMISSION_SHARE
        )
        assert update_share.password
        assert update_share.permissions == SharePermissions.PERMISSION_READ + SharePermissions.PERMISSION_SHARE
        assert update_share.send_password_by_talk is False
        update_share = nc.files.sharing.update(new_share, send_password_by_talk=True, public_upload=True)
        assert update_share.password
        assert update_share.send_password_by_talk is True
        expire_time = datetime.datetime.now() + datetime.timedelta(days=1)
        expire_time = expire_time.replace(hour=0, minute=0, second=0, microsecond=0)
        update_share = nc.files.sharing.update(new_share, expire_date=expire_time)
        assert update_share.expire_date == expire_time
        update_share = nc.files.sharing.update(new_share, note="note", label="label")
        assert update_share.note == "note"
        assert update_share.label == "label"
        nc.files.sharing.delete(new_share)
    finally:
        nc.files.delete("share_test")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_inherited(nc):
    nc.files.makedirs("test_folder1/test_subfolder", exist_ok=True)
    nc.files.upload("test_folder1/test_subfolder/share_test.txt", content="content of file")
    try:
        new_share = nc.files.sharing.create("test_folder1/test_subfolder", ShareType.TYPE_LINK)
        assert not nc.files.sharing.get_inherited("test_folder1")
        assert not nc.files.sharing.get_inherited("test_folder1/test_subfolder")
        new_share2 = nc.files.sharing.get_inherited("test_folder1/test_subfolder/share_test.txt")[0]
        assert new_share.share_id == new_share2.share_id
        assert new_share.share_owner == new_share2.share_owner
        assert new_share.file_owner == new_share2.file_owner
        assert new_share.url == new_share2.url
    finally:
        nc.files.delete("test_folder1")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_pending(nc):
    assert isinstance(nc.files.sharing.get_pending(), list)
    with pytest.raises(NextcloudExceptionNotFound):
        nc.files.sharing.accept_share(99999999)
    with pytest.raises(NextcloudExceptionNotFound):
        nc.files.sharing.decline_share(99999999)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_deleted(nc):
    assert isinstance(nc.files.sharing.get_deleted(), list)
    with pytest.raises(NextcloudExceptionNotFound):
        nc.files.sharing.undelete(99999999)
