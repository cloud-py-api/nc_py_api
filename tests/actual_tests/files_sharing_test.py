import datetime
from os import environ

import pytest

from nc_py_api import (
    FilePermissions,
    Nextcloud,
    NextcloudException,
    NextcloudExceptionNotFound,
    ShareType,
)
from nc_py_api.files.sharing import Share


def test_available(nc_any):
    assert nc_any.files.sharing.available


def test_create_delete(nc_any):
    new_share = nc_any.files.sharing.create("test_12345_text.txt", ShareType.TYPE_LINK)
    nc_any.files.sharing.delete(new_share)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_any.files.sharing.delete(new_share)


def test_share_fields(nc_any):
    shared_file = nc_any.files.by_path("test_12345_text.txt")
    new_share = nc_any.files.sharing.create(shared_file, ShareType.TYPE_LINK, FilePermissions.PERMISSION_READ)
    try:
        get_by_id = nc_any.files.sharing.get_by_id(new_share.share_id)
        assert new_share.share_type == ShareType.TYPE_LINK
        assert not new_share.label
        assert not new_share.note
        assert new_share.mimetype.find("text") != -1
        assert new_share.permissions & FilePermissions.PERMISSION_READ
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
        nc_any.files.sharing.delete(new_share)


def test_create_permissions(nc_any):
    new_share = nc_any.files.sharing.create("test_empty_dir", ShareType.TYPE_LINK, FilePermissions.PERMISSION_CREATE)
    nc_any.files.sharing.delete(new_share)
    assert (
        new_share.permissions
        == FilePermissions.PERMISSION_READ | FilePermissions.PERMISSION_CREATE | FilePermissions.PERMISSION_SHARE
    )
    new_share = nc_any.files.sharing.create("test_empty_dir", ShareType.TYPE_LINK, FilePermissions.PERMISSION_DELETE)
    nc_any.files.sharing.delete(new_share)
    assert (
        new_share.permissions
        == FilePermissions.PERMISSION_READ | FilePermissions.PERMISSION_DELETE | FilePermissions.PERMISSION_SHARE
    )
    new_share = nc_any.files.sharing.create("test_empty_dir", ShareType.TYPE_LINK, FilePermissions.PERMISSION_UPDATE)
    nc_any.files.sharing.delete(new_share)
    assert (
        new_share.permissions
        == FilePermissions.PERMISSION_READ | FilePermissions.PERMISSION_UPDATE | FilePermissions.PERMISSION_SHARE
    )


def test_create_public_upload(nc_any):
    new_share = nc_any.files.sharing.create("test_empty_dir", ShareType.TYPE_LINK, public_upload=True)
    nc_any.files.sharing.delete(new_share)
    assert (
        new_share.permissions
        == FilePermissions.PERMISSION_READ
        | FilePermissions.PERMISSION_UPDATE
        | FilePermissions.PERMISSION_SHARE
        | FilePermissions.PERMISSION_DELETE
        | FilePermissions.PERMISSION_CREATE
    )


def test_create_password(nc):
    if nc.check_capabilities("spreed"):
        pytest.skip(reason="Talk is not installed.")
    new_share = nc.files.sharing.create("test_generated_image.png", ShareType.TYPE_LINK, password="s2dDS_z44ad1")
    nc.files.sharing.delete(new_share)
    assert new_share.password
    assert new_share.send_password_by_talk is False
    new_share = nc.files.sharing.create(
        "test_generated_image.png", ShareType.TYPE_LINK, password="s2dDS_z44ad1", send_password_by_talk=True
    )
    nc.files.sharing.delete(new_share)
    assert new_share.password
    assert new_share.send_password_by_talk is True


def test_create_note_label(nc_any):
    new_share = nc_any.files.sharing.create(
        "test_empty_text.txt", ShareType.TYPE_LINK, note="This is note", label="label"
    )
    nc_any.files.sharing.delete(new_share)
    assert new_share.note == "This is note"
    assert new_share.label == "label"


def test_create_expire_time(nc):
    expire_time = datetime.datetime.now() + datetime.timedelta(days=1)
    expire_time = expire_time.replace(hour=0, minute=0, second=0, microsecond=0)
    new_share = nc.files.sharing.create("test_12345_text.txt", ShareType.TYPE_LINK, expire_date=expire_time)
    nc.files.sharing.delete(new_share)
    assert new_share.expire_date == expire_time
    with pytest.raises(NextcloudException):
        nc.files.sharing.create(
            "test_12345_text.txt", ShareType.TYPE_LINK, expire_date=datetime.datetime.now() - datetime.timedelta(days=1)
        )
    new_share.raw_data["expiration"] = "invalid time"
    new_share2 = Share(new_share.raw_data)
    assert new_share2.expire_date == datetime.datetime(1970, 1, 1)


def test_get_list(nc):
    shared_file = nc.files.by_path("test_12345_text.txt")
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


def test_create_update(nc):
    if nc.check_capabilities("spreed"):
        pytest.skip(reason="Talk is not installed.")
    new_share = nc.files.sharing.create(
        "test_empty_dir",
        ShareType.TYPE_LINK,
        permissions=FilePermissions.PERMISSION_READ
        + FilePermissions.PERMISSION_SHARE
        + FilePermissions.PERMISSION_UPDATE,
    )
    update_share = nc.files.sharing.update(new_share, password="s2dDS_z44ad1")
    assert update_share.password
    assert update_share.permissions != FilePermissions.PERMISSION_READ + FilePermissions.PERMISSION_SHARE
    update_share = nc.files.sharing.update(
        new_share, permissions=FilePermissions.PERMISSION_READ + FilePermissions.PERMISSION_SHARE
    )
    assert update_share.password
    assert update_share.permissions == FilePermissions.PERMISSION_READ + FilePermissions.PERMISSION_SHARE
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


def test_get_inherited(nc_any):
    new_share = nc_any.files.sharing.create("test_dir/subdir", ShareType.TYPE_LINK)
    assert not nc_any.files.sharing.get_inherited("test_dir")
    assert not nc_any.files.sharing.get_inherited("test_dir/subdir")
    new_share2 = nc_any.files.sharing.get_inherited("test_dir/subdir/test_12345_text.txt")[0]
    assert new_share.share_id == new_share2.share_id
    assert new_share.share_owner == new_share2.share_owner
    assert new_share.file_owner == new_share2.file_owner
    assert new_share.url == new_share2.url


def test_share_with(nc, nc_client):
    nc_second_user = Nextcloud(nc_auth_user=environ["TEST_USER_ID"], nc_auth_pass=environ["TEST_USER_PASS"])
    assert not nc_second_user.files.sharing.get_list()
    shared_file = nc.files.by_path("test_empty_text.txt")
    folder_share = nc.files.sharing.create(
        "test_empty_dir_in_dir", ShareType.TYPE_USER, share_with=environ["TEST_USER_ID"]
    )
    file_share = nc.files.sharing.create(shared_file, ShareType.TYPE_USER, share_with=environ["TEST_USER_ID"])
    shares_list1 = nc.files.sharing.get_list(path="test_empty_dir_in_dir/")
    shares_list2 = nc.files.sharing.get_list(path="test_empty_text.txt")
    second_user_shares_list = nc_second_user.files.sharing.get_list()
    second_user_shares_list_with_me = nc_second_user.files.sharing.get_list(shared_with_me=True)
    nc.files.sharing.delete(folder_share)
    nc.files.sharing.delete(file_share)
    assert not second_user_shares_list
    assert len(second_user_shares_list_with_me) == 2
    assert len(shares_list1) == 1
    assert len(shares_list2) == 1
    assert not nc_second_user.files.sharing.get_list()


def test_pending(nc_any):
    assert isinstance(nc_any.files.sharing.get_pending(), list)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_any.files.sharing.accept_share(99999999)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_any.files.sharing.decline_share(99999999)


def test_deleted(nc_any):
    assert isinstance(nc_any.files.sharing.get_deleted(), list)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_any.files.sharing.undelete(99999999)
