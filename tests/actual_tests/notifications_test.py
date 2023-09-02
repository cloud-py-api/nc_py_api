import pytest

from nc_py_api.notifications import Notification, NotificationInfo


def test_available(nc_app):
    assert nc_app.notifications.available


def test_create_as_client(nc_client):
    with pytest.raises(NotImplementedError):
        nc_client.notifications.create("caption")


def test_create(nc_app):
    obj_id = nc_app.notifications.create("subject0123", "message456")
    new_notification = nc_app.notifications.by_object_id(obj_id)
    assert isinstance(new_notification, Notification)
    assert isinstance(new_notification.info, NotificationInfo)
    assert new_notification.info.subject == "subject0123"
    assert new_notification.info.message == "message456"
    assert new_notification.info.icon
    assert not new_notification.info.link


def test_create_link_icon(nc_app):
    obj_id = nc_app.notifications.create("1", "", link="https://some.link/gg")
    new_notification = nc_app.notifications.by_object_id(obj_id)
    assert isinstance(new_notification, Notification)
    assert isinstance(new_notification.info, NotificationInfo)
    assert new_notification.info.subject == "1"
    assert not new_notification.info.message
    assert new_notification.info.icon
    assert new_notification.info.link == "https://some.link/gg"


def test_delete_all(nc_app):
    nc_app.notifications.create("subject0123", "message456")
    obj_id1 = nc_app.notifications.create("subject0123", "message456")
    ntf1 = nc_app.notifications.by_object_id(obj_id1)
    assert ntf1
    obj_id2 = nc_app.notifications.create("subject0123", "message456")
    ntf2 = nc_app.notifications.by_object_id(obj_id2)
    assert ntf2
    nc_app.notifications.delete_all()
    assert nc_app.notifications.by_object_id(obj_id1) is None
    assert nc_app.notifications.by_object_id(obj_id2) is None
    assert not nc_app.notifications.get_all()
    assert not nc_app.notifications.exists([ntf1.notification_id, ntf2.notification_id])


def test_delete_one(nc_app):
    obj_id1 = nc_app.notifications.create("subject0123")
    obj_id2 = nc_app.notifications.create("subject0123")
    ntf1 = nc_app.notifications.by_object_id(obj_id1)
    ntf2 = nc_app.notifications.by_object_id(obj_id2)
    nc_app.notifications.delete(ntf1.notification_id)
    assert nc_app.notifications.by_object_id(obj_id1) is None
    assert nc_app.notifications.by_object_id(obj_id2)
    assert nc_app.notifications.exists([ntf1.notification_id, ntf2.notification_id]) == [ntf2.notification_id]
    nc_app.notifications.delete(ntf2.notification_id)


def test_create_invalid_args(nc_app):
    with pytest.raises(ValueError):
        nc_app.notifications.create("")


def test_get_one(nc_app):
    nc_app.notifications.delete_all()
    obj_id1 = nc_app.notifications.create("subject0123")
    obj_id2 = nc_app.notifications.create("subject0123")
    ntf1 = nc_app.notifications.by_object_id(obj_id1)
    ntf2 = nc_app.notifications.by_object_id(obj_id2)
    ntf1_2 = nc_app.notifications.get_one(ntf1.notification_id)
    ntf2_2 = nc_app.notifications.get_one(ntf2.notification_id)
    assert ntf1 == ntf1_2
    assert ntf2 == ntf2_2