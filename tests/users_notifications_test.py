import pytest
from gfixture import NC, NC_APP

from nc_py_api import users_defs

if NC_APP is None or "app_ecosystem_v2" not in NC_APP.capabilities:
    pytest.skip("app_ecosystem_v2 is not installed.", allow_module_level=True)


def test_available():
    assert NC_APP.users.notifications.available


@pytest.mark.skipif(NC is None, reason="Not available for NextcloudApp.")
def test_create_as_client():
    with pytest.raises(NotImplementedError):
        NC.users.notifications.create("caption")


def test_create():
    obj_id = NC_APP.users.notifications.create("subject0123", "message456")
    new_notification = NC_APP.users.notifications.by_object_id(obj_id)
    assert isinstance(new_notification, users_defs.Notification)
    assert isinstance(new_notification.info, users_defs.NotificationInfo)
    assert new_notification.info.subject == "subject0123"
    assert new_notification.info.message == "message456"
    assert new_notification.info.icon
    assert not new_notification.info.link


def test_create_link_icon():
    obj_id = NC_APP.users.notifications.create("1", "", link="https://some.link/gg")
    new_notification = NC_APP.users.notifications.by_object_id(obj_id)
    assert isinstance(new_notification, users_defs.Notification)
    assert isinstance(new_notification.info, users_defs.NotificationInfo)
    assert new_notification.info.subject == "1"
    assert not new_notification.info.message
    assert new_notification.info.icon
    assert new_notification.info.link == "https://some.link/gg"


def test_delete_all():
    NC_APP.users.notifications.create("subject0123", "message456")
    obj_id1 = NC_APP.users.notifications.create("subject0123", "message456")
    ntf1 = NC_APP.users.notifications.by_object_id(obj_id1)
    assert ntf1
    obj_id2 = NC_APP.users.notifications.create("subject0123", "message456")
    ntf2 = NC_APP.users.notifications.by_object_id(obj_id2)
    assert ntf2
    NC_APP.users.notifications.delete_all()
    assert NC_APP.users.notifications.by_object_id(obj_id1) is None
    assert NC_APP.users.notifications.by_object_id(obj_id2) is None
    assert not NC_APP.users.notifications.get_all()
    assert not NC_APP.users.notifications.exists([ntf1.notification_id, ntf2.notification_id])


def test_delete_one():
    obj_id1 = NC_APP.users.notifications.create("subject0123")
    obj_id2 = NC_APP.users.notifications.create("subject0123")
    ntf1 = NC_APP.users.notifications.by_object_id(obj_id1)
    ntf2 = NC_APP.users.notifications.by_object_id(obj_id2)
    NC_APP.users.notifications.delete(ntf1.notification_id)
    assert NC_APP.users.notifications.by_object_id(obj_id1) is None
    assert NC_APP.users.notifications.by_object_id(obj_id2)
    assert NC_APP.users.notifications.exists([ntf1.notification_id, ntf2.notification_id]) == [ntf2.notification_id]
    NC_APP.users.notifications.delete(ntf2.notification_id)


def test_create_invalid_args():
    with pytest.raises(ValueError):
        NC_APP.users.notifications.create("")


def test_get_one():
    NC_APP.users.notifications.delete_all()
    obj_id1 = NC_APP.users.notifications.create("subject0123")
    obj_id2 = NC_APP.users.notifications.create("subject0123")
    ntf1 = NC_APP.users.notifications.by_object_id(obj_id1)
    ntf2 = NC_APP.users.notifications.by_object_id(obj_id2)
    ntf1_2 = NC_APP.users.notifications.get_one(ntf1.notification_id)
    ntf2_2 = NC_APP.users.notifications.get_one(ntf2.notification_id)
    assert ntf1 == ntf1_2
    assert ntf2 == ntf2_2
