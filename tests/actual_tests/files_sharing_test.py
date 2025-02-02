import datetime
from os import environ

import pytest

from nc_py_api import (
    FilePermissions,
    FsNode,
    Nextcloud,
    NextcloudException,
    NextcloudExceptionNotFound,
    ShareType,
)
from nc_py_api.files.sharing import Share


def test_available(nc_any):
    assert nc_any.files.sharing.available


@pytest.mark.asyncio(scope="session")
async def test_available_async(anc_any):
    assert await anc_any.files.sharing.available


def test_create_delete(nc_any):
    new_share = nc_any.files.sharing.create("test_12345_text.txt", ShareType.TYPE_LINK)
    nc_any.files.sharing.delete(new_share)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_any.files.sharing.delete(new_share)


@pytest.mark.asyncio(scope="session")
async def test_create_delete_async(anc_any):
    new_share = await anc_any.files.sharing.create("test_12345_text.txt", ShareType.TYPE_LINK)
    await anc_any.files.sharing.delete(new_share)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_any.files.sharing.delete(new_share)


def _test_share_fields(new_share: Share, get_by_id: Share, shared_file: FsNode):
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
    assert get_by_id.file_source_id == shared_file.info.fileid
    assert get_by_id.can_delete is True
    assert get_by_id.can_edit is True


def test_share_fields(nc_any):
    shared_file = nc_any.files.by_path("test_12345_text.txt")
    new_share = nc_any.files.sharing.create(shared_file, ShareType.TYPE_LINK, FilePermissions.PERMISSION_READ)
    try:
        get_by_id = nc_any.files.sharing.get_by_id(new_share.share_id)
        _test_share_fields(new_share, get_by_id, shared_file)
    finally:
        nc_any.files.sharing.delete(new_share)


@pytest.mark.asyncio(scope="session")
async def test_share_fields_async(anc_any):
    shared_file = await anc_any.files.by_path("test_12345_text.txt")
    new_share = await anc_any.files.sharing.create(shared_file, ShareType.TYPE_LINK, FilePermissions.PERMISSION_READ)
    try:
        get_by_id = await anc_any.files.sharing.get_by_id(new_share.share_id)
        _test_share_fields(new_share, get_by_id, shared_file)
    finally:
        await anc_any.files.sharing.delete(new_share)


def test_create_permissions(nc_any):
    new_share = nc_any.files.sharing.create("test_empty_dir", ShareType.TYPE_LINK, FilePermissions.PERMISSION_CREATE)
    nc_any.files.sharing.delete(new_share)
    assert (new_share.permissions & FilePermissions.PERMISSION_CREATE) == FilePermissions.PERMISSION_CREATE
    new_share = nc_any.files.sharing.create(
        "test_empty_dir",
        ShareType.TYPE_LINK,
        FilePermissions.PERMISSION_CREATE + FilePermissions.PERMISSION_READ + FilePermissions.PERMISSION_DELETE,
    )
    nc_any.files.sharing.delete(new_share)
    assert (new_share.permissions & FilePermissions.PERMISSION_DELETE) == FilePermissions.PERMISSION_DELETE
    new_share = nc_any.files.sharing.create(
        "test_empty_dir",
        ShareType.TYPE_LINK,
        FilePermissions.PERMISSION_CREATE + FilePermissions.PERMISSION_READ + FilePermissions.PERMISSION_UPDATE,
    )
    nc_any.files.sharing.delete(new_share)
    assert (new_share.permissions & FilePermissions.PERMISSION_UPDATE) == FilePermissions.PERMISSION_UPDATE


@pytest.mark.asyncio(scope="session")
async def test_create_permissions_async(anc_any):
    new_share = await anc_any.files.sharing.create(
        "test_empty_dir", ShareType.TYPE_LINK, FilePermissions.PERMISSION_CREATE
    )
    await anc_any.files.sharing.delete(new_share)
    assert (new_share.permissions & FilePermissions.PERMISSION_CREATE) == FilePermissions.PERMISSION_CREATE
    new_share = await anc_any.files.sharing.create(
        "test_empty_dir",
        ShareType.TYPE_LINK,
        FilePermissions.PERMISSION_CREATE + FilePermissions.PERMISSION_READ + FilePermissions.PERMISSION_DELETE,
    )
    await anc_any.files.sharing.delete(new_share)
    assert (new_share.permissions & FilePermissions.PERMISSION_DELETE) == FilePermissions.PERMISSION_DELETE
    new_share = await anc_any.files.sharing.create(
        "test_empty_dir",
        ShareType.TYPE_LINK,
        FilePermissions.PERMISSION_CREATE + FilePermissions.PERMISSION_READ + FilePermissions.PERMISSION_UPDATE,
    )
    await anc_any.files.sharing.delete(new_share)
    assert (new_share.permissions & FilePermissions.PERMISSION_UPDATE) == FilePermissions.PERMISSION_UPDATE


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


@pytest.mark.asyncio(scope="session")
async def test_create_public_upload_async(anc_any):
    new_share = await anc_any.files.sharing.create("test_empty_dir", ShareType.TYPE_LINK, public_upload=True)
    await anc_any.files.sharing.delete(new_share)
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


@pytest.mark.asyncio(scope="session")
async def test_create_password_async(anc):
    if await anc.check_capabilities("spreed"):
        pytest.skip(reason="Talk is not installed.")
    new_share = await anc.files.sharing.create("test_generated_image.png", ShareType.TYPE_LINK, password="s2dDS_z44ad1")
    await anc.files.sharing.delete(new_share)
    assert new_share.password
    assert new_share.send_password_by_talk is False
    new_share = await anc.files.sharing.create(
        "test_generated_image.png", ShareType.TYPE_LINK, password="s2dDS_z44ad1", send_password_by_talk=True
    )
    await anc.files.sharing.delete(new_share)
    assert new_share.password
    assert new_share.send_password_by_talk is True


def test_create_note_label(nc_any):
    new_share = nc_any.files.sharing.create(
        "test_empty_text.txt", ShareType.TYPE_LINK, note="This is note", label="label"
    )
    nc_any.files.sharing.delete(new_share)
    assert new_share.note == "This is note"
    assert new_share.label == "label"


@pytest.mark.asyncio(scope="session")
async def test_create_note_label_async(anc_any):
    new_share = await anc_any.files.sharing.create(
        "test_empty_text.txt", ShareType.TYPE_LINK, note="This is note", label="label"
    )
    await anc_any.files.sharing.delete(new_share)
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
    assert new_share2.expire_date == datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


@pytest.mark.asyncio(scope="session")
async def test_create_expire_time_async(anc):
    expire_time = datetime.datetime.now() + datetime.timedelta(days=1)
    expire_time = expire_time.replace(hour=0, minute=0, second=0, microsecond=0)
    new_share = await anc.files.sharing.create("test_12345_text.txt", ShareType.TYPE_LINK, expire_date=expire_time)
    await anc.files.sharing.delete(new_share)
    assert new_share.expire_date == expire_time
    with pytest.raises(NextcloudException):
        await anc.files.sharing.create(
            "test_12345_text.txt", ShareType.TYPE_LINK, expire_date=datetime.datetime.now() - datetime.timedelta(days=1)
        )
    new_share.raw_data["expiration"] = "invalid time"
    new_share2 = Share(new_share.raw_data)
    assert new_share2.expire_date == datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


def _test_get_list(share_by_id: Share, shares_list: list[Share]):
    assert share_by_id.share_owner == shares_list[-1].share_owner
    assert share_by_id.mimetype == shares_list[-1].mimetype
    assert share_by_id.password == shares_list[-1].password
    assert share_by_id.permissions == shares_list[-1].permissions
    assert share_by_id.url == shares_list[-1].url


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
    _test_get_list(share_by_id, shares_list)


@pytest.mark.asyncio(scope="session")
async def test_get_list_async(anc):
    shared_file = await anc.files.by_path("test_12345_text.txt")
    result = await anc.files.sharing.get_list()
    assert isinstance(result, list)
    n_shares = len(result)
    new_share = await anc.files.sharing.create(shared_file, ShareType.TYPE_LINK)
    assert isinstance(new_share, Share)
    shares_list = await anc.files.sharing.get_list()
    assert n_shares + 1 == len(shares_list)
    share_by_id = await anc.files.sharing.get_by_id(shares_list[-1].share_id)
    await anc.files.sharing.delete(new_share)
    assert n_shares == len(await anc.files.sharing.get_list())
    _test_get_list(share_by_id, shares_list)


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


@pytest.mark.asyncio(scope="session")
async def test_create_update_async(anc):
    if await anc.check_capabilities("spreed"):
        pytest.skip(reason="Talk is not installed.")
    new_share = await anc.files.sharing.create(
        "test_empty_dir",
        ShareType.TYPE_LINK,
        permissions=FilePermissions.PERMISSION_READ
        + FilePermissions.PERMISSION_SHARE
        + FilePermissions.PERMISSION_UPDATE,
    )
    update_share = await anc.files.sharing.update(new_share, password="s2dDS_z44ad1")
    assert update_share.password
    assert update_share.permissions != FilePermissions.PERMISSION_READ + FilePermissions.PERMISSION_SHARE
    update_share = await anc.files.sharing.update(
        new_share, permissions=FilePermissions.PERMISSION_READ + FilePermissions.PERMISSION_SHARE
    )
    assert update_share.password
    assert update_share.permissions == FilePermissions.PERMISSION_READ + FilePermissions.PERMISSION_SHARE
    assert update_share.send_password_by_talk is False
    update_share = await anc.files.sharing.update(new_share, send_password_by_talk=True, public_upload=True)
    assert update_share.password
    assert update_share.send_password_by_talk is True
    expire_time = datetime.datetime.now() + datetime.timedelta(days=1)
    expire_time = expire_time.replace(hour=0, minute=0, second=0, microsecond=0)
    update_share = await anc.files.sharing.update(new_share, expire_date=expire_time)
    assert update_share.expire_date == expire_time
    update_share = await anc.files.sharing.update(new_share, note="note", label="label")
    assert update_share.note == "note"
    assert update_share.label == "label"
    await anc.files.sharing.delete(new_share)


def test_get_inherited(nc_any):
    new_share = nc_any.files.sharing.create("test_dir/subdir", ShareType.TYPE_LINK)
    assert not nc_any.files.sharing.get_inherited("test_dir")
    assert not nc_any.files.sharing.get_inherited("test_dir/subdir")
    new_share2 = nc_any.files.sharing.get_inherited("test_dir/subdir/test_12345_text.txt")[0]
    assert new_share.share_id == new_share2.share_id
    assert new_share.share_owner == new_share2.share_owner
    assert new_share.file_owner == new_share2.file_owner
    assert new_share.url == new_share2.url
    nc_any.files.sharing.delete(new_share)


@pytest.mark.asyncio(scope="session")
async def test_get_inherited_async(anc_any):
    new_share = await anc_any.files.sharing.create("test_dir/subdir", ShareType.TYPE_LINK)
    assert not await anc_any.files.sharing.get_inherited("test_dir")
    assert not await anc_any.files.sharing.get_inherited("test_dir/subdir")
    new_share2 = (await anc_any.files.sharing.get_inherited("test_dir/subdir/test_12345_text.txt"))[0]
    assert new_share.share_id == new_share2.share_id
    assert new_share.share_owner == new_share2.share_owner
    assert new_share.file_owner == new_share2.file_owner
    assert new_share.url == new_share2.url
    await anc_any.files.sharing.delete(new_share)


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


@pytest.mark.asyncio(scope="session")
async def test_share_with_async(anc, anc_client):
    nc_second_user = Nextcloud(nc_auth_user=environ["TEST_USER_ID"], nc_auth_pass=environ["TEST_USER_PASS"])
    assert not nc_second_user.files.sharing.get_list()
    shared_file = await anc.files.by_path("test_empty_text.txt")
    folder_share = await anc.files.sharing.create(
        "test_empty_dir_in_dir", ShareType.TYPE_USER, share_with=environ["TEST_USER_ID"]
    )
    file_share = await anc.files.sharing.create(shared_file, ShareType.TYPE_USER, share_with=environ["TEST_USER_ID"])
    shares_list1 = await anc.files.sharing.get_list(path="test_empty_dir_in_dir/")
    shares_list2 = await anc.files.sharing.get_list(path="test_empty_text.txt")
    second_user_shares_list = nc_second_user.files.sharing.get_list()
    second_user_shares_list_with_me = nc_second_user.files.sharing.get_list(shared_with_me=True)
    await anc.files.sharing.delete(folder_share)
    await anc.files.sharing.delete(file_share)
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


@pytest.mark.asyncio(scope="session")
async def test_pending_async(anc_any):
    assert isinstance(await anc_any.files.sharing.get_pending(), list)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_any.files.sharing.accept_share(99999999)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_any.files.sharing.decline_share(99999999)


def test_deleted(nc_any):
    assert isinstance(nc_any.files.sharing.get_deleted(), list)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_any.files.sharing.undelete(99999999)


@pytest.mark.asyncio(scope="session")
async def test_deleted_async(anc_any):
    assert isinstance(await anc_any.files.sharing.get_deleted(), list)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_any.files.sharing.undelete(99999999)
