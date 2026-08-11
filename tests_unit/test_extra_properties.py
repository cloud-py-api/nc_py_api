"""Tests for requesting additional WebDAV properties and reading them back from FsNode."""

import pytest

from nc_py_api.files import FsNode
from nc_py_api.files._files import (
    MAPPED_PROPERTIES,
    PROPFIND_PROPERTIES,
    _parse_record,
    get_propfind_properties,
)

NO_LOCKING = {"files": {}}  # `files.locking` not advertised, so only the base properties are requested


def _prop_stat(props: dict, status: str = "HTTP/1.1 200 OK") -> dict:
    return {"d:status": status, "d:prop": props}


def test_no_extra_properties_keeps_the_default_request():
    assert get_propfind_properties(NO_LOCKING) == list(PROPFIND_PROPERTIES)
    assert get_propfind_properties(NO_LOCKING, []) == list(PROPFIND_PROPERTIES)
    assert get_propfind_properties(NO_LOCKING, None) == list(PROPFIND_PROPERTIES)


def test_extra_properties_are_appended_in_order():
    requested = get_propfind_properties(NO_LOCKING, ["nc:has-preview", "oc:owner-id"])
    assert requested == [*PROPFIND_PROPERTIES, "nc:has-preview", "oc:owner-id"]


def test_extra_properties_are_deduplicated():
    # neither against each other nor against what is requested anyway
    requested = get_propfind_properties(NO_LOCKING, ["nc:has-preview", "nc:has-preview", "oc:size", "d:getetag"])
    assert requested == [*PROPFIND_PROPERTIES, "nc:has-preview"]


def test_extra_properties_reject_unknown_namespaces():
    for invalid in ("bogus:prop", "has-preview", ":has-preview"):
        with pytest.raises(ValueError, match="Invalid property"):
            get_propfind_properties(NO_LOCKING, [invalid])


def test_unmapped_properties_land_in_extra_properties():
    node = _parse_record(
        "files/admin/a.txt",
        [_prop_stat({"oc:id": "00000123", "oc:fileid": "123", "nc:has-preview": "true", "oc:owner-id": "admin"})],
    )
    assert node.file_id == "00000123"  # modelled fields stay where they were
    assert node.info.fileid == 123
    assert node.extra_properties == {"nc:has-preview": "true", "oc:owner-id": "admin"}


def test_modelled_properties_are_not_duplicated_into_extra_properties():
    node = _parse_record(
        "files/admin/a.txt",
        [_prop_stat(dict.fromkeys(MAPPED_PROPERTIES, "1"))],
    )
    assert node.extra_properties == {}


def test_properties_the_server_could_not_return_are_ignored():
    node = _parse_record(
        "files/admin/a.txt",
        [
            _prop_stat({"nc:has-preview": "true"}),
            _prop_stat({"nc:made-up-property": None}, status="HTTP/1.1 404 Not Found"),
        ],
    )
    assert node.extra_properties == {"nc:has-preview": "true"}


def test_values_are_kept_as_the_server_sent_them():
    # strings, None for empty ones and a dict for the nested ones such as `oc:share-types`
    node = _parse_record(
        "files/admin/a.txt",
        [_prop_stat({"oc:share-types": {"oc:share-type": "3"}, "nc:mount-type": None, "nc:has-preview": "true"})],
    )
    assert node.extra_properties == {
        "oc:share-types": {"oc:share-type": "3"},
        "nc:mount-type": None,
        "nc:has-preview": "true",
    }


def test_fs_node_without_extra_properties():
    assert FsNode("files/admin/a.txt").extra_properties == {}
    assert FsNode("files/admin/a.txt", extra_properties=None).extra_properties == {}


def test_xml_attributes_are_not_reported_as_properties():
    node = _parse_record("files/admin/a.txt", [_prop_stat({"@xmlns:d": "DAV:", "nc:has-preview": "true"})])
    assert node.extra_properties == {"nc:has-preview": "true"}


WITH_LOCKING = {"files": {"locking": "1.0"}}  # `files.locking` advertised -> the lock properties are requested too


def test_extra_properties_are_deduplicated_against_the_locking_ones():
    from nc_py_api.files._files import PROPFIND_LOCKING_PROPERTIES

    requested = get_propfind_properties(WITH_LOCKING, ["nc:lock-owner", "nc:has-preview"])
    assert requested == [*PROPFIND_PROPERTIES, *PROPFIND_LOCKING_PROPERTIES, "nc:has-preview"]


def test_extra_properties_come_after_the_default_ones():
    requested = get_propfind_properties(WITH_LOCKING, ["nc:has-preview"])
    assert requested[-1] == "nc:has-preview"
    assert len(requested) == len(set(requested))
