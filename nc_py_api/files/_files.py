"""Helper functions for **FilesAPI** and **AsyncFilesAPI** classes."""

import enum
from io import BytesIO
from json import dumps, loads
from urllib.parse import unquote
from xml.etree import ElementTree

import xmltodict
from httpx import Response

from .._exceptions import NextcloudException, check_error
from .._misc import check_capabilities, clear_from_params_empty
from . import FsNode, SystemTag

PROPFIND_PROPERTIES = [
    "d:resourcetype",
    "d:getlastmodified",
    "d:getcontentlength",
    "d:getcontenttype",
    "d:getetag",
    "oc:size",
    "oc:id",
    "oc:fileid",
    "oc:downloadURL",
    "oc:dDC",
    "oc:permissions",
    "oc:checksums",
    "oc:share-types",
    "oc:favorite",
    "nc:is-encrypted",
]

PROPFIND_LOCKING_PROPERTIES = [
    "nc:lock",
    "nc:lock-owner-displayname",
    "nc:lock-owner",
    "nc:lock-owner-type",
    "nc:lock-owner-editor",  # App id of an app owned lock
    "nc:lock-time",  # Timestamp of the log creation time
    "nc:lock-timeout",  # TTL of the lock in seconds staring from the creation time
]

SEARCH_PROPERTIES_MAP = {
    "name": "d:displayname",  # like, eq
    "mime": "d:getcontenttype",  # like, eq
    "last_modified": "d:getlastmodified",  # gt, eq, lt
    "size": "oc:size",  # gt, gte, eq, lt
    "favorite": "oc:favorite",  # eq
    "fileid": "oc:fileid",  # eq
}


class PropFindType(enum.IntEnum):
    """Internal enum types for ``_listdir`` and ``_lf_parse_webdav_records`` methods."""

    DEFAULT = 0
    TRASHBIN = 1
    VERSIONS_FILEID = 2
    VERSIONS_FILE_ID = 3


def get_propfind_properties(capabilities: dict) -> list:
    r = PROPFIND_PROPERTIES
    if not check_capabilities("files.locking", capabilities):
        r += PROPFIND_LOCKING_PROPERTIES
    return r


def build_find_request(req: list, path: str | FsNode, user: str, capabilities: dict) -> ElementTree.Element:
    path = path.user_path if isinstance(path, FsNode) else path
    root = ElementTree.Element(
        "d:searchrequest",
        attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns", "xmlns:nc": "http://nextcloud.org/ns"},
    )
    xml_search = ElementTree.SubElement(root, "d:basicsearch")
    xml_select_prop = ElementTree.SubElement(ElementTree.SubElement(xml_search, "d:select"), "d:prop")
    for i in get_propfind_properties(capabilities):
        ElementTree.SubElement(xml_select_prop, i)
    xml_from_scope = ElementTree.SubElement(ElementTree.SubElement(xml_search, "d:from"), "d:scope")
    href = f"/files/{user}/{path.removeprefix('/')}"
    ElementTree.SubElement(xml_from_scope, "d:href").text = href
    ElementTree.SubElement(xml_from_scope, "d:depth").text = "infinity"
    xml_where = ElementTree.SubElement(xml_search, "d:where")
    build_search_req(xml_where, req)
    return root


def build_list_by_criteria_req(
    properties: list[str] | None, tags: list[int | SystemTag] | None, capabilities: dict
) -> ElementTree.Element:
    if not properties and not tags:
        raise ValueError("Either specify 'properties' or 'tags' to filter results.")
    root = ElementTree.Element(
        "oc:filter-files",
        attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns", "xmlns:nc": "http://nextcloud.org/ns"},
    )
    prop = ElementTree.SubElement(root, "d:prop")
    for i in get_propfind_properties(capabilities):
        ElementTree.SubElement(prop, i)
    xml_filter_rules = ElementTree.SubElement(root, "oc:filter-rules")
    if properties and "favorite" in properties:
        ElementTree.SubElement(xml_filter_rules, "oc:favorite").text = "1"
    if tags:
        for v in tags:
            tag_id = v.tag_id if isinstance(v, SystemTag) else v
            ElementTree.SubElement(xml_filter_rules, "oc:systemtag").text = str(tag_id)
    return root


def build_search_req(xml_element_where, req: list) -> None:
    def _process_or_and(xml_element, or_and: str):
        _where_part_root = ElementTree.SubElement(xml_element, f"d:{or_and}")
        _add_value(_where_part_root)
        _add_value(_where_part_root)

    def _add_value(xml_element, val=None) -> None:
        first_val = req.pop(0) if val is None else val
        if first_val in ("or", "and"):
            _process_or_and(xml_element, first_val)
            return
        _root = ElementTree.SubElement(xml_element, f"d:{first_val}")
        _ = ElementTree.SubElement(_root, "d:prop")
        ElementTree.SubElement(_, SEARCH_PROPERTIES_MAP[req.pop(0)])
        _ = ElementTree.SubElement(_root, "d:literal")
        value = req.pop(0)
        _.text = value if isinstance(value, str) else str(value)

    while len(req):
        where_part = req.pop(0)
        if where_part in ("or", "and"):
            _process_or_and(xml_element_where, where_part)
        else:
            _add_value(xml_element_where, where_part)


def build_setfav_req(value: int | bool) -> ElementTree.Element:
    root = ElementTree.Element(
        "d:propertyupdate",
        attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns"},
    )
    xml_set = ElementTree.SubElement(root, "d:set")
    xml_set_prop = ElementTree.SubElement(xml_set, "d:prop")
    ElementTree.SubElement(xml_set_prop, "oc:favorite").text = str(int(bool(value)))
    return root


def build_list_tag_req() -> ElementTree.Element:
    root = ElementTree.Element(
        "d:propfind",
        attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns"},
    )
    properties = ["oc:id", "oc:display-name", "oc:user-visible", "oc:user-assignable"]
    prop_element = ElementTree.SubElement(root, "d:prop")
    for i in properties:
        ElementTree.SubElement(prop_element, i)
    return root


def build_list_tags_response(response: Response) -> list[SystemTag]:
    result = []
    records = _webdav_response_to_records(response, "list_tags")
    for record in records:
        prop_stat = record["d:propstat"]
        if str(prop_stat.get("d:status", "")).find("200 OK") == -1:
            continue
        result.append(SystemTag(prop_stat["d:prop"]))
    return result


def build_tags_ids_for_object(url_to_fetch: str, response: Response) -> list[int]:
    result = []
    records = _webdav_response_to_records(response, "list_tags_ids")
    for record in records:
        prop_stat = record["d:propstat"]
        if str(prop_stat.get("d:status", "")).find("200 OK") != -1:
            href_suffix = str(record["d:href"]).removeprefix(url_to_fetch).strip("/")
            if href_suffix:
                result.append(int(href_suffix))
    return result


def build_update_tag_req(
    name: str | None, user_visible: bool | None, user_assignable: bool | None
) -> ElementTree.Element:
    root = ElementTree.Element(
        "d:propertyupdate",
        attrib={
            "xmlns:d": "DAV:",
            "xmlns:oc": "http://owncloud.org/ns",
        },
    )
    properties = {
        "oc:display-name": name,
        "oc:user-visible": "true" if user_visible is True else "false" if user_visible is False else None,
        "oc:user-assignable": "true" if user_assignable is True else "false" if user_assignable is False else None,
    }
    clear_from_params_empty(list(properties.keys()), properties)
    if not properties:
        raise ValueError("No property specified to change.")
    xml_set = ElementTree.SubElement(root, "d:set")
    prop_element = ElementTree.SubElement(xml_set, "d:prop")
    for k, v in properties.items():
        ElementTree.SubElement(prop_element, k).text = v
    return root


def build_listdir_req(
    user: str, path: str, properties: list[str], prop_type: PropFindType
) -> tuple[ElementTree.Element, str]:
    root = ElementTree.Element(
        "d:propfind",
        attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns", "xmlns:nc": "http://nextcloud.org/ns"},
    )
    prop = ElementTree.SubElement(root, "d:prop")
    for i in properties:
        ElementTree.SubElement(prop, i)
    if prop_type in (PropFindType.VERSIONS_FILEID, PropFindType.VERSIONS_FILE_ID):
        dav_path = dav_get_obj_path(f"versions/{user}/versions", path, root_path="")
    elif prop_type == PropFindType.TRASHBIN:
        dav_path = dav_get_obj_path(f"trashbin/{user}/trash", path, root_path="")
    else:
        dav_path = dav_get_obj_path(user, path)
    return root, dav_path


def build_listdir_response(
    dav_url_suffix: str,
    webdav_response: Response,
    user: str,
    path: str,
    properties: list[str],
    exclude_self: bool,
    prop_type: PropFindType,
) -> list[FsNode]:
    result = lf_parse_webdav_response(
        dav_url_suffix,
        webdav_response,
        f"list: {user}, {path}, {properties}",
        prop_type,
    )
    if exclude_self:
        for index, v in enumerate(result):
            if v.user_path.rstrip("/") == path.strip("/"):
                del result[index]
                break
    return result


def element_tree_as_str(element) -> str:
    with BytesIO() as buffer:
        ElementTree.ElementTree(element).write(buffer, xml_declaration=True)
        buffer.seek(0)
        return buffer.read().decode("utf-8")


def dav_get_obj_path(user: str, path: str = "", root_path="/files") -> str:
    obj_dav_path = root_path
    if user:
        obj_dav_path += "/" + user
    if path:
        obj_dav_path += "/" + path.lstrip("/")
    return obj_dav_path


def etag_fileid_from_response(response: Response) -> dict:
    return {"etag": response.headers.get("OC-Etag", ""), "file_id": response.headers["OC-FileId"]}


def _parse_record(full_path: str, prop_stats: list[dict]) -> FsNode:  # noqa pylint: disable = too-many-branches
    fs_node_args = {}
    for prop_stat in prop_stats:
        if str(prop_stat.get("d:status", "")).find("200 OK") == -1:
            continue
        prop: dict = prop_stat["d:prop"]
        prop_keys = prop.keys()
        if "oc:id" in prop_keys:
            fs_node_args["file_id"] = prop["oc:id"]
        if "oc:fileid" in prop_keys:
            fs_node_args["fileid"] = int(prop["oc:fileid"])
        if "oc:size" in prop_keys:
            fs_node_args["size"] = int(prop["oc:size"])
        if "d:getcontentlength" in prop_keys:
            fs_node_args["content_length"] = int(prop["d:getcontentlength"])
        if "d:getetag" in prop_keys:
            fs_node_args["etag"] = prop["d:getetag"]
        if "d:getlastmodified" in prop_keys:
            fs_node_args["last_modified"] = prop["d:getlastmodified"]
        if "d:getcontenttype" in prop_keys:
            fs_node_args["mimetype"] = prop["d:getcontenttype"]
        if "oc:permissions" in prop_keys:
            fs_node_args["permissions"] = prop["oc:permissions"]
        if "oc:favorite" in prop_keys:
            fs_node_args["favorite"] = bool(int(prop["oc:favorite"]))
        if "nc:trashbin-filename" in prop_keys:
            fs_node_args["trashbin_filename"] = prop["nc:trashbin-filename"]
        if "nc:trashbin-original-location" in prop_keys:
            fs_node_args["trashbin_original_location"] = prop["nc:trashbin-original-location"]
        if "nc:trashbin-deletion-time" in prop_keys:
            fs_node_args["trashbin_deletion_time"] = prop["nc:trashbin-deletion-time"]
        for k, v in {
            "nc:lock": "is_locked",
            "nc:lock-owner-type": "lock_owner_type",
            "nc:lock-owner": "lock_owner",
            "nc:lock-owner-displayname": "lock_owner_displayname",
            "nc:lock-owner-editor": "lock_owner_editor",
            "nc:lock-time": "lock_time",
            "nc:lock-timeout": "lock_ttl",
        }.items():
            if k in prop_keys and prop[k] is not None:
                fs_node_args[v] = prop[k]
    return FsNode(full_path, **fs_node_args)


def _parse_records(dav_url_suffix: str, fs_records: list[dict], response_type: PropFindType) -> list[FsNode]:
    result: list[FsNode] = []
    for record in fs_records:
        obj_full_path = unquote(record.get("d:href", ""))
        obj_full_path = obj_full_path.replace(dav_url_suffix, "").lstrip("/")
        propstat = record["d:propstat"]
        fs_node = _parse_record(obj_full_path, propstat if isinstance(propstat, list) else [propstat])
        if fs_node.etag and response_type in (
            PropFindType.VERSIONS_FILE_ID,
            PropFindType.VERSIONS_FILEID,
        ):
            fs_node.full_path = fs_node.full_path.rstrip("/")
            fs_node.info.is_version = True
            if response_type == PropFindType.VERSIONS_FILEID:
                fs_node.info.fileid = int(fs_node.full_path.rsplit("/", 2)[-2])
                fs_node.file_id = str(fs_node.info.fileid)
            else:
                fs_node.file_id = fs_node.full_path.rsplit("/", 2)[-2]
        if fs_node.file_id:
            result.append(fs_node)
    return result


def lf_parse_webdav_response(
    dav_url_suffix: str, webdav_res: Response, info: str, response_type: PropFindType = PropFindType.DEFAULT
) -> list[FsNode]:
    return _parse_records(dav_url_suffix, _webdav_response_to_records(webdav_res, info), response_type)


def _webdav_response_to_records(webdav_res: Response, info: str) -> list[dict]:
    check_error(webdav_res, info=info)
    if webdav_res.status_code != 207:  # multistatus
        raise NextcloudException(webdav_res.status_code, "Response is not a multistatus.", info=info)
    response_data = loads(dumps(xmltodict.parse(webdav_res.text)))
    if "d:error" in response_data:
        err = response_data["d:error"]
        raise NextcloudException(reason=f'{err["s:exception"]}: {err["s:message"]}'.replace("\n", ""), info=info)
    response = response_data["d:multistatus"].get("d:response", [])
    return [response] if isinstance(response, dict) else response
