"""Tests for S3 presigned download URL properties on FsNode/FsNodeInfo."""

from nc_py_api.files import FsNode, FsNodeInfo
from nc_py_api.files._files import _parse_record


def test_fsnode_info_download_url_defaults():
    info = FsNodeInfo()
    assert info.download_url == ""
    assert info.download_url_expiration == 0


def test_fsnode_info_download_url_with_values():
    info = FsNodeInfo(download_url="https://s3.example.com/bucket/obj?sig=abc", download_url_expiration=1700000000)
    assert info.download_url == "https://s3.example.com/bucket/obj?sig=abc"
    assert info.download_url_expiration == 1700000000


def test_fsnode_passes_download_url_to_info():
    node = FsNode(
        "files/admin/test.txt", file_id="00000123", download_url="https://s3.test/f", download_url_expiration=9999
    )
    assert node.info.download_url == "https://s3.test/f"
    assert node.info.download_url_expiration == 9999


def test_parse_record_with_download_url():
    prop_stat = {
        "d:status": "HTTP/1.1 200 OK",
        "d:prop": {
            "oc:id": "00000123",
            "oc:fileid": "123",
            "oc:permissions": "RGDNVW",
            "d:getetag": '"abc123"',
            "oc:downloadURL": "https://s3.example.com/bucket/urn:oid:123?X-Amz-Signature=abc",
            "nc:download-url-expiration": "1700000000",
        },
    }
    node = _parse_record("files/admin/test.txt", [prop_stat])
    assert node.info.download_url == "https://s3.example.com/bucket/urn:oid:123?X-Amz-Signature=abc"
    assert node.info.download_url_expiration == 1700000000


def test_parse_record_without_download_url():
    prop_stat = {
        "d:status": "HTTP/1.1 200 OK",
        "d:prop": {
            "oc:id": "00000123",
            "oc:fileid": "123",
            "oc:permissions": "RGDNVW",
            "d:getetag": '"abc123"',
        },
    }
    node = _parse_record("files/admin/test.txt", [prop_stat])
    assert node.info.download_url == ""
    assert node.info.download_url_expiration == 0


def test_parse_record_with_false_download_url():
    """When storage doesn't support presigned URLs, server returns 'false'."""
    prop_stat = {
        "d:status": "HTTP/1.1 200 OK",
        "d:prop": {
            "oc:id": "00000123",
            "oc:fileid": "123",
            "oc:permissions": "RGDNVW",
            "d:getetag": '"abc123"',
            "oc:downloadURL": False,
            "nc:download-url-expiration": False,
        },
    }
    node = _parse_record("files/admin/test.txt", [prop_stat])
    assert node.info.download_url == ""
    assert node.info.download_url_expiration == 0


def test_parse_record_with_malformed_expiration():
    """Malformed expiration should not crash parsing."""
    prop_stat = {
        "d:status": "HTTP/1.1 200 OK",
        "d:prop": {
            "oc:id": "00000123",
            "oc:fileid": "123",
            "oc:permissions": "RGDNVW",
            "d:getetag": '"abc123"',
            "oc:downloadURL": "https://s3.test/f",
            "nc:download-url-expiration": "not-a-number",
        },
    }
    node = _parse_record("files/admin/test.txt", [prop_stat])
    assert node.info.download_url == "https://s3.test/f"
    assert node.info.download_url_expiration == 0
