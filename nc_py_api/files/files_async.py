"""Nextcloud API for working with the file system."""

import builtins
import os
from pathlib import Path
from urllib.parse import quote

from httpx import Headers

from .._exceptions import NextcloudException, NextcloudExceptionNotFound, check_error
from .._misc import random_string, require_capabilities
from .._session import AsyncNcSessionBasic
from . import FsNode, LockType, SystemTag
from ._files import (
    PROPFIND_PROPERTIES,
    PropFindType,
    build_find_request,
    build_list_by_criteria_req,
    build_list_tag_req,
    build_list_tags_response,
    build_listdir_req,
    build_listdir_response,
    build_setfav_req,
    build_tags_ids_for_object,
    build_update_tag_req,
    dav_get_obj_path,
    element_tree_as_str,
    etag_fileid_from_response,
    get_propfind_properties,
    lf_parse_webdav_response,
)
from .sharing import _AsyncFilesSharingAPI


class AsyncFilesAPI:
    """Class that encapsulates async file system and file sharing API."""

    sharing: _AsyncFilesSharingAPI
    """API for managing Files Shares"""

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session
        self.sharing = _AsyncFilesSharingAPI(session)

    async def listdir(self, path: str | FsNode = "", depth: int = 1, exclude_self=True) -> list[FsNode]:
        """Returns a list of all entries in the specified directory.

        :param path: path to the directory to get the list.
        :param depth: how many directory levels should be included in output. Default = **1** (only specified directory)
        :param exclude_self: boolean value indicating whether the `path` itself should be excluded from the list or not.
            Default = **True**.
        """
        if exclude_self and not depth:
            raise ValueError("Wrong input parameters, query will return nothing.")
        properties = get_propfind_properties(await self._session.capabilities)
        path = path.user_path if isinstance(path, FsNode) else path
        return await self._listdir(
            await self._session.user, path, properties=properties, depth=depth, exclude_self=exclude_self
        )

    async def by_id(self, file_id: int | str | FsNode) -> FsNode | None:
        """Returns :py:class:`~nc_py_api.files.FsNode` by file_id if any.

        :param file_id: can be full file ID with Nextcloud instance ID or only clear file ID.
        """
        file_id = file_id.file_id if isinstance(file_id, FsNode) else file_id
        result = await self.find(req=["eq", "fileid", file_id])
        return result[0] if result else None

    async def by_path(self, path: str | FsNode) -> FsNode | None:
        """Returns :py:class:`~nc_py_api.files.FsNode` by exact path if any."""
        path = path.user_path if isinstance(path, FsNode) else path
        result = await self.listdir(path, depth=0, exclude_self=False)
        return result[0] if result else None

    async def find(self, req: list, path: str | FsNode = "") -> list[FsNode]:
        """Searches a directory for a file or subdirectory with a name.

        :param req: list of conditions to search for. Detailed description here...
        :param path: path where to search from. Default = **""**.
        """
        # `req` possible keys: "name", "mime", "last_modified", "size", "favorite", "fileid"
        root = build_find_request(req, path, await self._session.user, await self._session.capabilities)
        webdav_response = await self._session.adapter_dav.request(
            "SEARCH", "", content=element_tree_as_str(root), headers={"Content-Type": "text/xml"}
        )
        request_info = f"find: {await self._session.user}, {req}, {path}"
        return lf_parse_webdav_response(self._session.cfg.dav_url_suffix, webdav_response, request_info)

    async def download(self, path: str | FsNode) -> bytes:
        """Downloads and returns the content of a file."""
        path = path.user_path if isinstance(path, FsNode) else path
        response = await self._session.adapter_dav.get(quote(dav_get_obj_path(await self._session.user, path)))
        check_error(response, f"download: user={await self._session.user}, path={path}")
        return response.content

    async def download2stream(self, path: str | FsNode, fp, **kwargs) -> None:
        """Downloads file to the given `fp` object.

        :param path: path to download file.
        :param fp: filename (string), pathlib.Path object or a file object.
            The object must implement the ``file.write`` method and be able to write binary data.
        :param kwargs: **chunk_size** an int value specifying chunk size to write. Default = **5Mb**
        """
        path = quote(dav_get_obj_path(await self._session.user, path.user_path if isinstance(path, FsNode) else path))
        await self._session.download2stream(path, fp, dav=True, **kwargs)

    async def download_directory_as_zip(
        self, path: str | FsNode, local_path: str | Path | None = None, **kwargs
    ) -> Path:
        """Downloads a remote directory as zip archive.

        :param path: path to directory to download.
        :param local_path: relative or absolute file path to save zip file.
        :returns: Path to the saved zip archive.

        .. note:: This works only for directories, you should not use this to download a file.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        result_path = local_path if local_path else os.path.basename(path)
        with open(result_path, "wb") as fp:
            await self._session.download2fp(
                "/index.php/apps/files/ajax/download.php", fp, dav=False, params={"dir": path}, **kwargs
            )
        return Path(result_path)

    async def upload(self, path: str | FsNode, content: bytes | str) -> FsNode:
        """Creates a file with the specified content at the specified path.

        :param path: file's upload path.
        :param content: content to create the file. If it is a string, it will be encoded into bytes using UTF-8.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        full_path = dav_get_obj_path(await self._session.user, path)
        response = await self._session.adapter_dav.put(quote(full_path), content=content)
        check_error(response, f"upload: user={await self._session.user}, path={path}, size={len(content)}")
        return FsNode(full_path.strip("/"), **etag_fileid_from_response(response))

    async def upload_stream(self, path: str | FsNode, fp, **kwargs) -> FsNode:
        """Creates a file with content provided by `fp` object at the specified path.

        :param path: file's upload path.
        :param fp: filename (string), pathlib.Path object or a file object.
            The object must implement the ``file.read`` method providing data with str or bytes type.
        :param kwargs: **chunk_size** an int value specifying chunk size to read. Default = **5Mb**
        """
        path = path.user_path if isinstance(path, FsNode) else path
        chunk_size = kwargs.get("chunk_size", 5 * 1024 * 1024)
        if isinstance(fp, str | Path):
            with builtins.open(fp, "rb") as f:
                return await self.__upload_stream(path, f, chunk_size)
        elif hasattr(fp, "read"):
            return await self.__upload_stream(path, fp, chunk_size)
        else:
            raise TypeError("`fp` must be a path to file or an object with `read` method.")

    async def mkdir(self, path: str | FsNode) -> FsNode:
        """Creates a new directory.

        :param path: path of the directory to be created.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        full_path = dav_get_obj_path(await self._session.user, path)
        response = await self._session.adapter_dav.request("MKCOL", quote(full_path))
        check_error(response)
        full_path += "/" if not full_path.endswith("/") else ""
        return FsNode(full_path.lstrip("/"), **etag_fileid_from_response(response))

    async def makedirs(self, path: str | FsNode, exist_ok=False) -> FsNode | None:
        """Creates a new directory and subdirectories.

        :param path: path of the directories to be created.
        :param exist_ok: ignore error if any of pathname components already exists.
        :returns: `FsNode` if directory was created or ``None`` if it was already created.
        """
        _path = ""
        path = path.user_path if isinstance(path, FsNode) else path
        path = path.lstrip("/")
        result = None
        for i in Path(path).parts:
            _path = os.path.join(_path, i)
            if not exist_ok:
                result = await self.mkdir(_path)
            else:
                try:
                    result = await self.mkdir(_path)
                except NextcloudException as e:
                    if e.status_code != 405:
                        raise e from None
        return result

    async def delete(self, path: str | FsNode, not_fail=False) -> None:
        """Deletes a file/directory (moves to trash if trash is enabled).

        :param path: path to delete.
        :param not_fail: if set to ``True`` and the object is not found, it does not raise an exception.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        response = await self._session.adapter_dav.delete(quote(dav_get_obj_path(await self._session.user, path)))
        if response.status_code == 404 and not_fail:
            return
        check_error(response)

    async def move(self, path_src: str | FsNode, path_dest: str | FsNode, overwrite=False) -> FsNode:
        """Moves an existing file or a directory.

        :param path_src: path of an existing file/directory.
        :param path_dest: name of the new one.
        :param overwrite: if ``True`` and the destination object already exists, it gets overwritten.
            Default = **False**.
        """
        path_src = path_src.user_path if isinstance(path_src, FsNode) else path_src
        full_dest_path = dav_get_obj_path(
            await self._session.user, path_dest.user_path if isinstance(path_dest, FsNode) else path_dest
        )
        dest = self._session.cfg.dav_endpoint + quote(full_dest_path)
        headers = Headers({"Destination": dest, "Overwrite": "T" if overwrite else "F"}, encoding="utf-8")
        response = await self._session.adapter_dav.request(
            "MOVE",
            quote(dav_get_obj_path(await self._session.user, path_src)),
            headers=headers,
        )
        check_error(response, f"move: user={await self._session.user}, src={path_src}, dest={dest}, {overwrite}")
        return (await self.find(req=["eq", "fileid", response.headers["OC-FileId"]]))[0]

    async def copy(self, path_src: str | FsNode, path_dest: str | FsNode, overwrite=False) -> FsNode:
        """Copies an existing file/directory.

        :param path_src: path of an existing file/directory.
        :param path_dest: name of the new one.
        :param overwrite: if ``True`` and the destination object already exists, it gets overwritten.
            Default = **False**.
        """
        path_src = path_src.user_path if isinstance(path_src, FsNode) else path_src
        full_dest_path = dav_get_obj_path(
            await self._session.user, path_dest.user_path if isinstance(path_dest, FsNode) else path_dest
        )
        dest = self._session.cfg.dav_endpoint + quote(full_dest_path)
        headers = Headers({"Destination": dest, "Overwrite": "T" if overwrite else "F"}, encoding="utf-8")
        response = await self._session.adapter_dav.request(
            "COPY",
            quote(dav_get_obj_path(await self._session.user, path_src)),
            headers=headers,
        )
        check_error(response, f"copy: user={await self._session.user}, src={path_src}, dest={dest}, {overwrite}")
        return (await self.find(req=["eq", "fileid", response.headers["OC-FileId"]]))[0]

    async def list_by_criteria(
        self, properties: list[str] | None = None, tags: list[int | SystemTag] | None = None
    ) -> list[FsNode]:
        """Returns a list of all files/directories for the current user filtered by the specified values.

        :param properties: List of ``properties`` that should have been set for the file.
            Supported values: **favorite**
        :param tags: List of ``tags ids`` or ``SystemTag`` that should have been set for the file.
        """
        root = build_list_by_criteria_req(properties, tags, await self._session.capabilities)
        webdav_response = await self._session.adapter_dav.request(
            "REPORT", dav_get_obj_path(await self._session.user), content=element_tree_as_str(root)
        )
        request_info = f"list_files_by_criteria: {await self._session.user}"
        check_error(webdav_response, request_info)
        return lf_parse_webdav_response(self._session.cfg.dav_url_suffix, webdav_response, request_info)

    async def setfav(self, path: str | FsNode, value: int | bool) -> None:
        """Sets or unsets favourite flag for specific file.

        :param path: path to the object to set the state.
        :param value: value to set for the ``favourite`` state.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        root = build_setfav_req(value)
        webdav_response = await self._session.adapter_dav.request(
            "PROPPATCH", quote(dav_get_obj_path(await self._session.user, path)), content=element_tree_as_str(root)
        )
        check_error(webdav_response, f"setfav: path={path}, value={value}")

    async def trashbin_list(self) -> list[FsNode]:
        """Returns a list of all entries in the TrashBin."""
        properties = PROPFIND_PROPERTIES
        properties += ["nc:trashbin-filename", "nc:trashbin-original-location", "nc:trashbin-deletion-time"]
        return await self._listdir(
            await self._session.user,
            "",
            properties=properties,
            depth=1,
            exclude_self=False,
            prop_type=PropFindType.TRASHBIN,
        )

    async def trashbin_restore(self, path: str | FsNode) -> None:
        """Restore a file/directory from the TrashBin.

        :param path: path to delete, e.g., the ``user_path`` field from ``FsNode`` or the **FsNode** class itself.
        """
        restore_name = path.name if isinstance(path, FsNode) else path.split("/", maxsplit=1)[-1]
        path = path.user_path if isinstance(path, FsNode) else path

        dest = self._session.cfg.dav_endpoint + f"/trashbin/{await self._session.user}/restore/{restore_name}"
        headers = Headers({"Destination": dest}, encoding="utf-8")
        response = await self._session.adapter_dav.request(
            "MOVE",
            quote(f"/trashbin/{await self._session.user}/{path}"),
            headers=headers,
        )
        check_error(response, f"trashbin_restore: user={await self._session.user}, src={path}, dest={dest}")

    async def trashbin_delete(self, path: str | FsNode, not_fail=False) -> None:
        """Deletes a file/directory permanently from the TrashBin.

        :param path: path to delete, e.g., the ``user_path`` field from ``FsNode`` or the **FsNode** class itself.
        :param not_fail: if set to ``True`` and the object is not found, it does not raise an exception.
        """
        path = path.user_path if isinstance(path, FsNode) else path
        response = await self._session.adapter_dav.delete(quote(f"/trashbin/{await self._session.user}/{path}"))
        if response.status_code == 404 and not_fail:
            return
        check_error(response)

    async def trashbin_cleanup(self) -> None:
        """Empties the TrashBin."""
        check_error(await self._session.adapter_dav.delete(f"/trashbin/{await self._session.user}/trash"))

    async def get_versions(self, file_object: FsNode) -> list[FsNode]:
        """Returns a list of all file versions if any."""
        require_capabilities("files.versioning", await self._session.capabilities)
        return await self._listdir(
            await self._session.user,
            str(file_object.info.fileid) if file_object.info.fileid else file_object.file_id,
            properties=PROPFIND_PROPERTIES,
            depth=1,
            exclude_self=False,
            prop_type=PropFindType.VERSIONS_FILEID if file_object.info.fileid else PropFindType.VERSIONS_FILE_ID,
        )

    async def restore_version(self, file_object: FsNode) -> None:
        """Restore a file with specified version.

        :param file_object: The **FsNode** class from :py:meth:`~nc_py_api.files.files.FilesAPI.get_versions`.
        """
        require_capabilities("files.versioning", await self._session.capabilities)
        dest = self._session.cfg.dav_endpoint + f"/versions/{await self._session.user}/restore/{file_object.name}"
        headers = Headers({"Destination": dest}, encoding="utf-8")
        response = await self._session.adapter_dav.request(
            "MOVE",
            quote(f"/versions/{await self._session.user}/{file_object.user_path}"),
            headers=headers,
        )
        check_error(response, f"restore_version: user={await self._session.user}, src={file_object.user_path}")

    async def list_tags(self) -> list[SystemTag]:
        """Returns list of the avalaible Tags."""
        root = build_list_tag_req()
        response = await self._session.adapter_dav.request("PROPFIND", "/systemtags", content=element_tree_as_str(root))
        return build_list_tags_response(response)

    async def get_tags(self, file_id: FsNode | int) -> list[SystemTag]:
        """Returns list of Tags assigned to the File or Directory."""
        fs_object = file_id.info.fileid if isinstance(file_id, FsNode) else file_id
        url_to_fetch = f"/systemtags-relations/files/{fs_object}/"
        response = await self._session.adapter_dav.request("PROPFIND", url_to_fetch)
        object_tags_ids = build_tags_ids_for_object(self._session.cfg.dav_url_suffix + url_to_fetch, response)
        if not object_tags_ids:
            return []
        all_tags = await self.list_tags()
        return [tag for tag in all_tags if tag.tag_id in object_tags_ids]

    async def create_tag(self, name: str, user_visible: bool = True, user_assignable: bool = True) -> None:
        """Creates a new Tag.

        :param name: Name of the tag.
        :param user_visible: Should be Tag visible in the UI.
        :param user_assignable: Can Tag be assigned from the UI.
        """
        response = await self._session.adapter_dav.post(
            "/systemtags",
            json={
                "name": name,
                "userVisible": user_visible,
                "userAssignable": user_assignable,
            },
        )
        check_error(response, info=f"create_tag({name})")

    async def update_tag(
        self,
        tag_id: int | SystemTag,
        name: str | None = None,
        user_visible: bool | None = None,
        user_assignable: bool | None = None,
    ) -> None:
        """Updates the Tag information."""
        tag_id = tag_id.tag_id if isinstance(tag_id, SystemTag) else tag_id
        root = build_update_tag_req(name, user_visible, user_assignable)
        response = await self._session.adapter_dav.request(
            "PROPPATCH", f"/systemtags/{tag_id}", content=element_tree_as_str(root)
        )
        check_error(response)

    async def delete_tag(self, tag_id: int | SystemTag) -> None:
        """Deletes the tag."""
        tag_id = tag_id.tag_id if isinstance(tag_id, SystemTag) else tag_id
        response = await self._session.adapter_dav.delete(f"/systemtags/{tag_id}")
        check_error(response)

    async def tag_by_name(self, tag_name: str) -> SystemTag:
        """Returns Tag info by its name if found or ``None`` otherwise."""
        r = [i for i in await self.list_tags() if i.display_name == tag_name]
        if not r:
            raise NextcloudExceptionNotFound(f"Tag with name='{tag_name}' not found.")
        return r[0]

    async def assign_tag(self, file_id: FsNode | int, tag_id: SystemTag | int) -> None:
        """Assigns Tag to a file/directory."""
        await self._file_change_tag_state(file_id, tag_id, True)

    async def unassign_tag(self, file_id: FsNode | int, tag_id: SystemTag | int) -> None:
        """Removes Tag from a file/directory."""
        await self._file_change_tag_state(file_id, tag_id, False)

    async def lock(self, path: FsNode | str, lock_type: LockType = LockType.MANUAL_LOCK) -> None:
        """Locks the file.

        .. note:: Exception codes: 423 - existing lock present.
        """
        require_capabilities("files.locking", await self._session.capabilities)
        full_path = dav_get_obj_path(await self._session.user, path.user_path if isinstance(path, FsNode) else path)
        response = await self._session.adapter_dav.request(
            "LOCK",
            quote(full_path),
            headers={"X-User-Lock": "1", "X-User-Lock-Type": str(lock_type.value)},
        )
        check_error(response, f"lock: user={self._session.user}, path={full_path}")

    async def unlock(self, path: FsNode | str) -> None:
        """Unlocks the file.

        .. note:: Exception codes: 412 - the file is not locked, 423 - the lock is owned by another user.
        """
        require_capabilities("files.locking", await self._session.capabilities)
        full_path = dav_get_obj_path(await self._session.user, path.user_path if isinstance(path, FsNode) else path)
        response = await self._session.adapter_dav.request(
            "UNLOCK",
            quote(full_path),
            headers={"X-User-Lock": "1"},
        )
        check_error(response, f"unlock: user={self._session.user}, path={full_path}")

    async def _file_change_tag_state(self, file_id: FsNode | int, tag_id: SystemTag | int, tag_state: bool) -> None:
        fs_object = file_id.info.fileid if isinstance(file_id, FsNode) else file_id
        tag = tag_id.tag_id if isinstance(tag_id, SystemTag) else tag_id
        response = await self._session.adapter_dav.request(
            "PUT" if tag_state else "DELETE", f"/systemtags-relations/files/{fs_object}/{tag}"
        )
        check_error(
            response,
            info=f"({'Adding' if tag_state else 'Removing'} `{tag}` {'to' if tag_state else 'from'} {fs_object})",
        )

    async def _listdir(
        self,
        user: str,
        path: str,
        properties: list[str],
        depth: int,
        exclude_self: bool,
        prop_type: PropFindType = PropFindType.DEFAULT,
    ) -> list[FsNode]:
        root, dav_path = build_listdir_req(user, path, properties, prop_type)
        webdav_response = await self._session.adapter_dav.request(
            "PROPFIND",
            quote(dav_path),
            content=element_tree_as_str(root),
            headers={"Depth": "infinity" if depth == -1 else str(depth)},
        )
        return build_listdir_response(
            self._session.cfg.dav_url_suffix, webdav_response, user, path, properties, exclude_self, prop_type
        )

    async def __upload_stream(self, path: str, fp, chunk_size: int) -> FsNode:
        _tmp_path = "nc-py-api-" + random_string(56)
        _dav_path = quote(dav_get_obj_path(await self._session.user, _tmp_path, root_path="/uploads"))
        _v2 = bool(self._session.cfg.options.upload_chunk_v2 and chunk_size >= 5 * 1024 * 1024)
        full_path = dav_get_obj_path(await self._session.user, path)
        headers = Headers({"Destination": self._session.cfg.dav_endpoint + quote(full_path)}, encoding="utf-8")
        if _v2:
            response = await self._session.adapter_dav.request("MKCOL", _dav_path, headers=headers)
        else:
            response = await self._session.adapter_dav.request("MKCOL", _dav_path)
        check_error(response)
        try:
            start_bytes = end_bytes = chunk_number = 0
            while True:
                piece = fp.read(chunk_size)
                if not piece:
                    break
                end_bytes = start_bytes + len(piece)
                if _v2:
                    response = await self._session.adapter_dav.put(
                        _dav_path + "/" + str(chunk_number), content=piece, headers=headers
                    )
                else:
                    _filename = str(start_bytes).rjust(15, "0") + "-" + str(end_bytes).rjust(15, "0")
                    response = await self._session.adapter_dav.put(_dav_path + "/" + _filename, content=piece)
                check_error(
                    response,
                    f"upload_stream(v={_v2}): user={await self._session.user}, path={path}, cur_size={end_bytes}",
                )
                start_bytes = end_bytes
                chunk_number += 1

            response = await self._session.adapter_dav.request(
                "MOVE",
                _dav_path + "/.file",
                headers=headers,
            )
            check_error(
                response,
                f"upload_stream(v={_v2}): user={await self._session.user}, path={path}, total_size={end_bytes}",
            )
            return FsNode(full_path.strip("/"), **etag_fileid_from_response(response))
        finally:
            await self._session.adapter_dav.delete(_dav_path)
