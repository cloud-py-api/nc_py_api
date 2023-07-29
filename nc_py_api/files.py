"""
Nextcloud API for working with the file system.
"""

import builtins
import os
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from random import choice
from string import ascii_lowercase, digits
from typing import Optional, Union
from urllib.parse import unquote
from xml.etree import ElementTree

import xmltodict
from httpx import Response

from ._session import NcSessionBasic
from .exceptions import NextcloudException, check_error


@dataclass
class FsNodeInfo:
    """Extra FS object attributes from Nextcloud"""

    size: int
    """Length of file in bytes, zero for directories.."""
    content_length: int
    """For directories it is size of all content in it, for files it is equal to ``size``."""
    permissions: str
    """Permissions for the object."""
    favorite: bool
    """Flag indicating if the object is marked as favorite."""
    fileid: int
    """Clear file ID without Nextcloud instance ID."""
    _last_modified: datetime

    def __init__(self, **kwargs):
        self.size = kwargs.get("size", 0)
        self.content_length = kwargs.get("content_length", 0)
        self.permissions = kwargs.get("permissions", "")
        self.favorite = kwargs.get("favorite", False)
        self.fileid = kwargs.get("fileid", 0)
        try:
            self.last_modified = kwargs.get("last_modified", datetime(1970, 1, 1))
        except (ValueError, TypeError):
            self.last_modified = datetime(1970, 1, 1)

    @property
    def last_modified(self) -> datetime:
        """Time when the object was last modified.

        .. note:: ETag if more preferable way to check if the object was changed."""

        return self._last_modified

    @last_modified.setter
    def last_modified(self, value: Union[str, datetime]):
        if isinstance(value, str):
            self._last_modified = parsedate_to_datetime(value)
        else:
            self._last_modified = value


@dataclass
class FsNode:
    """A class that represents a Nextcloud file object.

    Acceptable itself as a ``path`` parameter for the most file APIs."""

    full_path: str
    """Path to the object, including the username. Does not include `dav` prefix"""

    file_id: str
    """File ID + NC instance ID"""

    etag: str
    """An entity tag (ETag) of the object"""

    info: FsNodeInfo
    """Additional extra information for the object"""

    def __init__(self, full_path: str, **kwargs):
        self.full_path = full_path
        self.file_id = kwargs.get("file_id", "")
        self.etag = kwargs.get("etag", "")
        self.info = FsNodeInfo(**kwargs)

    @property
    def is_dir(self) -> bool:
        """Returns ``True`` for the directories, ``False`` otherwise."""

        return self.full_path.endswith("/")

    def __str__(self):
        return (
            f"{'Dir' if self.is_dir else 'File'}: `{self.name}` with id={self.file_id}"
            f" last modified at {str(self.info.last_modified)} and {self.info.permissions} permissions."
        )

    def __eq__(self, other):
        if self.file_id and self.file_id == other.file_id:
            return True
        return False

    @property
    def has_extra(self) -> bool:
        """Flag indicating whether this ``FsNode`` was obtained by the `mkdir` or `upload`
        methods and does not contain extended information."""

        return bool(self.info.permissions)

    @property
    def name(self) -> str:
        """Returns last ``pathname`` component."""

        return self.full_path.rstrip("/").rsplit("/", maxsplit=1)[-1]

    @property
    def user(self) -> str:
        """Returns user ID extracted from the `full_path`."""

        return self.full_path.lstrip("/").split("/", maxsplit=2)[1]

    @property
    def user_path(self) -> str:
        """Returns path relative to the user's root directory."""

        return self.full_path.lstrip("/").split("/", maxsplit=2)[-1]

    @property
    def is_shared(self) -> bool:
        """Check if a file or folder is shared"""

        return self.info.permissions.find("S") != -1

    @property
    def is_shareable(self) -> bool:
        """Check if a file or folder can be shared"""

        return self.info.permissions.find("R") != -1

    @property
    def is_mounted(self) -> bool:
        """Check if a file or folder is mounted"""

        return self.info.permissions.find("M") != -1

    @property
    def is_readable(self) -> bool:
        """Check if the file or folder is readable"""

        return self.info.permissions.find("G") != -1

    @property
    def is_deletable(self) -> bool:
        """Check if a file or folder can be deleted"""

        return self.info.permissions.find("D") != -1

    @property
    def is_updatable(self) -> bool:
        """Check if file/directory is writable"""

        if self.is_dir:
            return self.info.permissions.find("NV") != -1
        return self.info.permissions.find("W") != -1

    @property
    def is_creatable(self) -> bool:
        """Check whether new files or folders can be created inside this folder"""

        if not self.is_dir:
            return False
        return self.info.permissions.find("CK") != -1


PROPFIND_PROPERTIES = [
    "d:resourcetype",
    "d:getlastmodified",
    "d:getcontentlength",
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
    "nc:lock",
    "nc:lock-owner-displayname",
    "nc:lock-owner",
    "nc:lock-owner-type",
    "nc:lock-owner-editor",
    "nc:lock-time",
    "nc:lock-timeout",
]

SEARCH_PROPERTIES_MAP = {
    "name:": "d:displayname",  # like, eq
    "mime": "d:getcontenttype",  # like, eq
    "last_modified": "d:getlastmodified",  # gt, eq, lt
    "size": "oc:size",  # gt, gte, eq, lt
    "favorite": "oc:favorite",  # eq
    "fileid": "oc:fileid",  # eq
}


class FilesAPI:
    """This class provides all WebDAV functionality related to the files."""

    def __init__(self, session: NcSessionBasic):
        self._session = session

    def listdir(self, path: Union[str, FsNode] = "", depth: int = 1, exclude_self=True) -> list[FsNode]:
        """Returns a list of all entries in the specified directory.

        :param path: path to the directory to get the list.
        :param depth: how many directory levels should be included in output. Default = **1** (only specified directory)
        :param exclude_self: boolean value indicating whether the `path` itself should be excluded from the list or not.
            Default = **True**.
        """

        if exclude_self and not depth:
            raise ValueError("Wrong input parameters, query will return nothing.")
        properties = PROPFIND_PROPERTIES
        path = path.user_path if isinstance(path, FsNode) else path
        return self._listdir(self._session.user, path, properties=properties, depth=depth, exclude_self=exclude_self)

    def by_id(self, file_id: Union[int, str, FsNode]) -> Optional[FsNode]:
        """Returns :py:class:`FsNode` by file_id if any.

        :param file_id: can be full file ID with Nextcloud instance ID or only clear file ID.
        """

        file_id = file_id.file_id if isinstance(file_id, FsNode) else file_id
        result = self.find(req=["eq", "fileid", file_id])
        return result[0] if result else None

    def by_path(self, path: Union[str, FsNode]) -> Optional[FsNode]:
        """Returns :py:class:`FsNode` by exact path if any."""

        path = path.user_path if isinstance(path, FsNode) else path
        result = self.listdir(path, depth=0, exclude_self=False)
        return result[0] if result else None

    def find(self, req: list, path: Union[str, FsNode] = "") -> list[FsNode]:
        """Searches a directory for a file or subdirectory with a name.

        :param req: list of conditions to search for. Detailed description here...
        :param path: path where to search from. Default = **""**.
        """

        # `req` possible keys: "name", "mime", "last_modified", "size", "favorite", "fileid"
        path = path.user_path if isinstance(path, FsNode) else path
        root = ElementTree.Element(
            "d:searchrequest",
            attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns", "xmlns:nc": "http://nextcloud.org/ns"},
        )
        xml_search = ElementTree.SubElement(root, "d:basicsearch")
        xml_select_prop = ElementTree.SubElement(ElementTree.SubElement(xml_search, "d:select"), "d:prop")
        for i in PROPFIND_PROPERTIES:
            ElementTree.SubElement(xml_select_prop, i)
        xml_from_scope = ElementTree.SubElement(ElementTree.SubElement(xml_search, "d:from"), "d:scope")
        href = f"/files/{self._session.user}/{path.removeprefix('/')}"
        ElementTree.SubElement(xml_from_scope, "d:href").text = href
        ElementTree.SubElement(xml_from_scope, "d:depth").text = "infinity"
        xml_where = ElementTree.SubElement(xml_search, "d:where")
        self._build_search_req(xml_where, req)

        headers = {"Content-Type": "text/xml"}
        webdav_response = self._session.dav("SEARCH", "", data=self._element_tree_as_str(root), headers=headers)
        request_info = f"find: {self._session.user}, {req}, {path}"
        return self._lf_parse_webdav_records(webdav_response, request_info)

    def download(self, path: Union[str, FsNode]) -> bytes:
        """Downloads and returns the content of a file.

        :param path: path to download file.
        """

        path = path.user_path if isinstance(path, FsNode) else path
        response = self._session.dav("GET", self._dav_get_obj_path(self._session.user, path))
        check_error(response.status_code, f"download: user={self._session.user}, path={path}")
        return response.content

    def download2stream(self, path: Union[str, FsNode], fp, **kwargs) -> None:
        """Downloads file to the given `fp` object.

        :param path: path to download file.
        :param fp: filename (string), pathlib.Path object or a file object.
            The object must implement the ``file.write`` method and be able to write binary data.
        :param kwargs: **chunk_size** an int value specifying chunk size to write. Default = **4Mb**
        """

        path = path.user_path if isinstance(path, FsNode) else path
        if isinstance(fp, (str, Path)):
            with builtins.open(fp, "wb") as f:
                self.__download2stream(path, f, **kwargs)
        elif hasattr(fp, "write"):
            self.__download2stream(path, fp, **kwargs)
        else:
            raise TypeError("`fp` must be a path to file or an object with `write` method.")

    def upload(self, path: Union[str, FsNode], content: Union[bytes, str]) -> FsNode:
        """Creates a file with the specified content at the specified path.

        :param path: file's upload path.
        :param content: content to create the file. If it is a string, it will be encoded into bytes using UTF-8.
        """

        path = path.user_path if isinstance(path, FsNode) else path
        full_path = self._dav_get_obj_path(self._session.user, path)
        response = self._session.dav("PUT", full_path, data=content)
        check_error(response.status_code, f"upload: user={self._session.user}, path={path}, size={len(content)}")
        return FsNode(full_path.strip("/"), **self.__get_etag_fileid_from_response(response))

    def upload_stream(self, path: Union[str, FsNode], fp, **kwargs) -> FsNode:
        """Creates a file with content provided by `fp` object at the specified path.

        :param path: file's upload path.
        :param fp: filename (string), pathlib.Path object or a file object.
            The object must implement the ``file.read`` method providing data with str or bytes type.
        :param kwargs: **chunk_size** an int value specifying chunk size to read. Default = **4Mb**
        """

        path = path.user_path if isinstance(path, FsNode) else path
        if isinstance(fp, (str, Path)):
            with builtins.open(fp, "rb") as f:
                return self.__upload_stream(path, f, **kwargs)
        elif hasattr(fp, "read"):
            return self.__upload_stream(path, fp, **kwargs)
        else:
            raise TypeError("`fp` must be a path to file or an object with `read` method.")

    def mkdir(self, path: Union[str, FsNode]) -> FsNode:
        """Creates a new directory.

        :param path: path of the directory to be created.
        """

        path = path.user_path if isinstance(path, FsNode) else path
        full_path = self._dav_get_obj_path(self._session.user, path)
        response = self._session.dav("MKCOL", full_path)
        check_error(response.status_code, f"mkdir: user={self._session.user}, path={path}")
        full_path += "/" if not full_path.endswith("/") else ""
        return FsNode(full_path.lstrip("/"), **self.__get_etag_fileid_from_response(response))

    def makedirs(self, path: Union[str, FsNode], exist_ok=False) -> Optional[FsNode]:
        """Creates a new directory and subdirectories.

        :param path: path of the directories to be created.
        :param exist_ok: ignore error if any of pathname components already exists.
        :returns: `FsNode` if directory was created or ``None`` if it was already created.
        """

        _path = ""
        path = path.user_path if isinstance(path, FsNode) else path
        result = None
        for i in Path(path).parts:
            _path = os.path.join(_path, i)
            if not exist_ok:
                result = self.mkdir(_path)
            else:
                try:
                    result = self.mkdir(_path)
                except NextcloudException as e:
                    if e.status_code != 405:
                        raise e from None
        return result

    def delete(self, path: Union[str, FsNode], not_fail=False) -> None:
        """Deletes a file/directory (moves to trash if trash is enabled).

        :param path: path to delete.
        :param not_fail: if set to ``True`` and the object is not found, it does not raise an exception.
        """

        path = path.user_path if isinstance(path, FsNode) else path
        response = self._session.dav("DELETE", self._dav_get_obj_path(self._session.user, path))
        if response.status_code == 404 and not_fail:
            return
        check_error(response.status_code, f"delete: user={self._session.user}, path={path}")

    def move(self, path_src: Union[str, FsNode], path_dest: Union[str, FsNode], overwrite=False) -> FsNode:
        """Moves an existing file or a directory.

        :param path_src: path of an existing file/directory.
        :param path_dest: name of the new one.
        :param overwrite: if ``True`` and the destination object already exists, it gets overwritten.
            Default = **False**.
        """

        path_src = path_src.user_path if isinstance(path_src, FsNode) else path_src
        full_dest_path = self._dav_get_obj_path(
            self._session.user, path_dest.user_path if isinstance(path_dest, FsNode) else path_dest
        )
        dest = self._session.cfg.dav_endpoint + full_dest_path
        headers = {"Destination": dest, "Overwrite": "T" if overwrite else "F"}
        response = self._session.dav(
            "MOVE",
            self._dav_get_obj_path(self._session.user, path_src),
            headers=headers,
        )
        check_error(response.status_code, f"move: user={self._session.user}, src={path_src}, dest={dest}, {overwrite}")
        return self.find(req=["eq", "fileid", response.headers["OC-FileId"]])[0]

    def copy(self, path_src: Union[str, FsNode], path_dest: Union[str, FsNode], overwrite=False) -> FsNode:
        """Copies an existing file/directory.

        :param path_src: path of an existing file/directory.
        :param path_dest: name of the new one.
        :param overwrite: if ``True`` and the destination object already exists, it gets overwritten.
            Default = **False**.
        """

        path_src = path_src.user_path if isinstance(path_src, FsNode) else path_src
        full_dest_path = self._dav_get_obj_path(
            self._session.user, path_dest.user_path if isinstance(path_dest, FsNode) else path_dest
        )
        dest = self._session.cfg.dav_endpoint + full_dest_path
        headers = {"Destination": dest, "Overwrite": "T" if overwrite else "F"}
        response = self._session.dav(
            "COPY",
            self._dav_get_obj_path(self._session.user, path_src),
            headers=headers,
        )
        check_error(response.status_code, f"copy: user={self._session.user}, src={path_src}, dest={dest}, {overwrite}")
        return self.find(req=["eq", "fileid", response.headers["OC-FileId"]])[0]

    def listfav(self) -> list[FsNode]:
        """Returns a list of the current user's favorite files."""

        root = ElementTree.Element(
            "oc:filter-files",
            attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns", "xmlns:nc": "http://nextcloud.org/ns"},
        )
        xml_filter_rules = ElementTree.SubElement(root, "oc:filter-rules")
        ElementTree.SubElement(xml_filter_rules, "oc:favorite").text = "1"
        webdav_response = self._session.dav(
            "REPORT", self._dav_get_obj_path(self._session.user), data=self._element_tree_as_str(root)
        )
        request_info = f"listfav: {self._session.user}"
        check_error(webdav_response.status_code, request_info)
        return self._lf_parse_webdav_records(webdav_response, request_info, favorite=True)

    def setfav(self, path: Union[str, FsNode], value: Union[int, bool]) -> None:
        """Sets or unsets favourite flag for specific file.

        :param path: path to the object to set the state.
        :param value: value to set for the ``favourite`` state.
        """

        path = path.user_path if isinstance(path, FsNode) else path
        root = ElementTree.Element(
            "d:propertyupdate",
            attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns"},
        )
        xml_set = ElementTree.SubElement(root, "d:set")
        xml_set_prop = ElementTree.SubElement(xml_set, "d:prop")
        ElementTree.SubElement(xml_set_prop, "oc:favorite").text = str(int(bool(value)))
        webdav_response = self._session.dav(
            "PROPPATCH", self._dav_get_obj_path(self._session.user, path), data=self._element_tree_as_str(root)
        )
        check_error(webdav_response.status_code, f"setfav: path={path}, value={value}")

    def _listdir(self, user: str, path: str, properties: list[str], depth: int, exclude_self: bool) -> list[FsNode]:
        root = ElementTree.Element(
            "d:propfind",
            attrib={"xmlns:d": "DAV:", "xmlns:oc": "http://owncloud.org/ns", "xmlns:nc": "http://nextcloud.org/ns"},
        )
        prop = ElementTree.SubElement(root, "d:prop")
        for i in properties:
            ElementTree.SubElement(prop, i)
        headers = {"Depth": "infinity" if depth == -1 else str(depth)}
        webdav_response = self._session.dav(
            "PROPFIND", self._dav_get_obj_path(user, path), data=self._element_tree_as_str(root), headers=headers
        )
        request_info = f"list: {user}, {path}, {properties}"
        result = self._lf_parse_webdav_records(webdav_response, request_info)
        if exclude_self:
            for index, v in enumerate(result):
                if v.user_path.rstrip("/") == path.rstrip("/"):
                    del result[index]
                    break
        return result

    def _parse_records(self, fs_records: list[dict], favorite: bool):
        result: list[FsNode] = []
        for record in fs_records:
            obj_full_path = unquote(record.get("d:href", ""))
            obj_full_path = obj_full_path.replace(self._session.cfg.dav_url_suffix, "").lstrip("/")
            propstat = record["d:propstat"]
            fs_node = self._parse_record(obj_full_path, propstat if isinstance(propstat, list) else [propstat])
            if favorite and not fs_node.file_id:
                _fs_node = self.by_path(fs_node.user_path)
                if _fs_node:
                    _fs_node.info.favorite = True
                    result.append(_fs_node)
            elif fs_node.file_id:
                result.append(fs_node)
        return result

    @staticmethod
    def _parse_record(full_path: str, prop_stats: list[dict]) -> FsNode:
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
            if "oc:permissions" in prop_keys:
                fs_node_args["permissions"] = prop["oc:permissions"]
            if "oc:favorite" in prop_keys:
                fs_node_args["favorite"] = bool(int(prop["oc:favorite"]))
            # xz = prop.get("oc:dDC", "")
        return FsNode(full_path, **fs_node_args)

    def _lf_parse_webdav_records(self, webdav_res: Response, info: str, favorite=False) -> list[FsNode]:
        check_error(webdav_res.status_code, info=info)
        if webdav_res.status_code != 207:  # multistatus
            raise NextcloudException(webdav_res.status_code, "Response is not a multistatus.", info=info)
        response_data = loads(dumps(xmltodict.parse(webdav_res.text)))
        if "d:error" in response_data:
            err = response_data["d:error"]
            raise NextcloudException(reason=f'{err["s:exception"]}: {err["s:message"]}'.replace("\n", ""), info=info)
        response = response_data["d:multistatus"].get("d:response", [])
        return self._parse_records([response] if isinstance(response, dict) else response, favorite)

    @staticmethod
    def _dav_get_obj_path(user: str, path: str = "", root_path="/files") -> str:
        obj_dav_path = root_path
        if user:
            obj_dav_path += "/" + user
        if path:
            obj_dav_path += "/" + path.lstrip("/")
        return obj_dav_path

    @staticmethod
    def _element_tree_as_str(element) -> str:
        with BytesIO() as buffer:
            ElementTree.ElementTree(element).write(buffer, xml_declaration=True)
            buffer.seek(0)
            return buffer.read().decode("utf-8")

    @staticmethod
    def _build_search_req(xml_element_where, req: list) -> None:
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

    def __download2stream(self, path: str, fp, **kwargs) -> None:
        with self._session.dav_stream(
            "GET", self._dav_get_obj_path(self._session.user, path)
        ) as response:  # type: ignore
            check_error(response.status_code, f"download_stream: user={self._session.user}, path={path}")
            for data_chunk in response.iter_raw(chunk_size=kwargs.get("chunk_size", 4 * 1024 * 1024)):
                fp.write(data_chunk)

    def __upload_stream(self, path: str, fp, **kwargs) -> FsNode:
        _rnd_folder = "".join(choice(digits + ascii_lowercase) for _ in range(64))
        _dav_path = self._dav_get_obj_path(self._session.user, _rnd_folder, root_path="/uploads")
        response = self._session.dav("MKCOL", _dav_path)
        check_error(response.status_code)
        try:
            chunk_size = kwargs.get("chunk_size", 4 * 1024 * 1024)
            start_bytes = end_bytes = 0
            while True:
                piece = fp.read(chunk_size)
                if not piece:
                    break
                end_bytes = start_bytes + len(piece)
                _filename = str(start_bytes).rjust(15, "0") + "-" + str(end_bytes).rjust(15, "0")
                response = self._session.dav("PUT", _dav_path + "/" + _filename, data=piece)
                check_error(
                    response.status_code, f"upload_stream: user={self._session.user}, path={path}, cur_size={end_bytes}"
                )
                start_bytes = end_bytes
            full_path = self._dav_get_obj_path(self._session.user, path)
            headers = {"Destination": self._session.cfg.dav_endpoint + full_path}
            response = self._session.dav(
                "MOVE",
                _dav_path + "/.file",
                headers=headers,
            )
            check_error(
                response.status_code, f"upload_stream: user={self._session.user}, path={path}, total_size={end_bytes}"
            )
            return FsNode(full_path.strip("/"), **self.__get_etag_fileid_from_response(response))
        finally:
            self._session.dav("DELETE", _dav_path)

    @staticmethod
    def __get_etag_fileid_from_response(response: Response) -> dict:
        return {"etag": response.headers.get("OC-Etag", ""), "file_id": response.headers["OC-FileId"]}
