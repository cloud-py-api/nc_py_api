"""Tests for FsNode.etag: kept exactly as the server sent it, with a bare variant next to it."""

from nc_py_api.files import ActionFileInfo, FsNode
from nc_py_api.files._files import _parse_record, etag_fileid_from_response


class _FakeResponse:
    def __init__(self, headers: dict):
        self.headers = headers


def _prop_stat(etag) -> dict:
    return {
        "d:status": "HTTP/1.1 200 OK",
        "d:prop": {"oc:id": "00000123", "oc:fileid": "123", "oc:permissions": "RGDNVW", "d:getetag": etag},
    }


def test_etag_is_kept_as_the_server_sent_it():
    # the quotes are part of the entity tag, so `etag` stays usable in a request header as-is
    assert FsNode("files/admin/a.txt", etag='"6a351fb28bebc"').etag == '"6a351fb28bebc"'


def test_etag_unquoted_strips_the_quotes():
    assert FsNode("files/admin/a.txt", etag='"6a351fb28bebc"').etag_unquoted == "6a351fb28bebc"


def test_unquoted_etag_passes_through_both_ways():
    # versions endpoints answer with a bare timestamp instead of a quoted tag
    node = FsNode("files/admin/a.txt", etag="1785767946")
    assert node.etag == "1785767946"
    assert node.etag_unquoted == "1785767946"


def test_missing_and_empty_etag_become_empty_string():
    for node in (FsNode("files/admin/a.txt"), FsNode("files/admin/a.txt", etag=""), FsNode("f/a", etag=None)):
        assert node.etag == ""
        assert node.etag_unquoted == ""


def test_propfind_record_keeps_the_quoted_etag():
    assert _parse_record("files/admin/a.txt", [_prop_stat('"6a351fb28bebc"')]).etag == '"6a351fb28bebc"'
    assert _parse_record("files/admin/a.txt", [_prop_stat('"6a351fb28bebc"')]).etag_unquoted == "6a351fb28bebc"
    # the trashbin sends `<d:getetag/>`, which arrives as None
    assert _parse_record("files/admin/a.txt", [_prop_stat(None)]).etag == ""


def test_oc_etag_header_keeps_the_quoted_etag():
    response = _FakeResponse({"OC-Etag": '"e9673fb8e3e49ff7cbbff9f21e9c60d1"', "OC-FileId": "00000123"})
    node = FsNode("files/admin/a.txt", **etag_fileid_from_response(response))
    assert node.etag == '"e9673fb8e3e49ff7cbbff9f21e9c60d1"'
    assert node.etag_unquoted == "e9673fb8e3e49ff7cbbff9f21e9c60d1"


def test_etag_missing_from_headers():
    response = _FakeResponse({"OC-FileId": "00000123"})
    assert FsNode("files/admin/a.txt", **etag_fileid_from_response(response)).etag == ""


def test_both_sources_agree_for_the_same_file():
    from_propfind = _parse_record("files/admin/a.txt", [_prop_stat('"e9673fb8e3e49ff7cbbff9f21e9c60d1"')])
    from_header = FsNode(
        "files/admin/a.txt",
        **etag_fileid_from_response(
            _FakeResponse({"OC-Etag": '"e9673fb8e3e49ff7cbbff9f21e9c60d1"', "OC-FileId": "00000123"})
        ),
    )
    assert from_propfind.etag == from_header.etag
    assert from_propfind.etag_unquoted == from_header.etag_unquoted == "e9673fb8e3e49ff7cbbff9f21e9c60d1"


def test_action_file_info_to_fs_node_keeps_etag():
    # the ExApp UI file actions build FsNode from data the server posts to the ExApp
    action_file = ActionFileInfo(
        fileId=123,
        name="a.txt",
        directory="/",
        etag='"6a351fb28bebc"',
        mime="text/plain",
        fileType="file",
        size=7,
        favorite="false",
        permissions=27,
        mtime=1785767946,
        userId="admin",
    )
    assert action_file.to_fs_node().etag == '"6a351fb28bebc"'
    assert action_file.to_fs_node().etag_unquoted == "6a351fb28bebc"
