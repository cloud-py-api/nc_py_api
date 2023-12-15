"""Notes App API wrapper."""

import dataclasses
import datetime
import json
import typing

import httpx

from ._exceptions import check_error
from ._misc import check_capabilities, clear_from_params_empty, require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class Note:
    """Class representing one **Note**."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def note_id(self) -> int:
        """Unique identifier which is created by the server."""
        return self._raw_data["id"]

    @property
    def etag(self) -> str:
        """The note's entity tag (ETag) indicates if a note's attribute has changed."""
        return self._raw_data.get("etag", "")

    @property
    def readonly(self) -> bool:
        """Indicates if the note is read-only."""
        return self._raw_data.get("readonly", False)

    @property
    def title(self) -> str:
        """The note's title is also used as filename for the note's file.

        .. note :: Some special characters are automatically removed and a sequential number is added
                if a note with the same title in the same category exists.
        """
        return self._raw_data.get("title", "")

    @property
    def content(self) -> str:
        """Notes can contain arbitrary text.

        .. note:: Formatting should be done using Markdown, but not every markup can be supported by every client.
        """
        return self._raw_data.get("content", "")

    @property
    def category(self) -> str:
        """Every note is assigned to a category.

        By default, the category is an empty string (not null), which means the note is uncategorized.

        .. note:: Categories are mapped to folders in the file backend.
            Illegal characters are automatically removed and the respective folder is automatically created.
            Sub-categories (mapped to sub-folders) can be created by using ``/`` as delimiter.
        """
        return self._raw_data.get("category", "")

    @property
    def favorite(self) -> bool:
        """If a note is marked as favorite, it is displayed at the top of the notes' list."""
        return self._raw_data.get("favorite", False)

    @property
    def last_modified(self) -> datetime.datetime:
        """Last modified date/time of the note.

        If not provided on note creation or content update, the current time is used.
        """
        modified = self._raw_data.get("modified", 0)
        return datetime.datetime.utcfromtimestamp(modified).replace(tzinfo=datetime.timezone.utc)

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.note_id}, title={self.title}, last_modified={self.last_modified}>"


class NotesSettings(typing.TypedDict):
    """Settings of Notes App."""

    notes_path: str
    """Path to the folder, where note's files are stored in Nextcloud.
        The path must be relative to the user folder. Default is the localized string **Notes**."""
    file_suffix: str
    """Newly created note's files will have this file suffix. Default is **.txt**."""


class _NotesAPI:
    """Class implementing Nextcloud Notes API."""

    _ep_base: str = "/index.php/apps/notes/api/v1"  # without `index.php` we will get 405 error.
    last_etag: str
    """Used by ``get_list``, when **etag** param is ``True``."""

    def __init__(self, session: NcSessionBasic):
        self._session = session
        self.last_etag = ""

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("notes", self._session.capabilities)

    def get_list(
        self,
        category: str | None = None,
        modified_since: int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        no_content: bool = False,
        etag: bool = False,
    ) -> list[Note]:
        """Get information of all Notes.

        :param category: Filter the result by category name. Notes with another category are not included in the result.
        :param modified_since: When provided only results newer than given Unix timestamp are returned.
        :param limit: Limit response to contain no more than the given number of notes.
            If there are more notes, then the result is chunked and the HTTP response header
            **X-Notes-Chunk-Cursor** is sent with a string value.

            .. note:: Use :py:attr:`~nc_py_api.nextcloud.Nextcloud.response_headers` property to achieve that.
        :param cursor: You should use the string value from the last request's HTTP response header
            ``X-Notes-Chunk-Cursor`` in order to get the next chunk of notes.
        :param no_content: Flag indicating should ``content`` field be excluded from response.
        :param etag: Flag indicating should ``ETag`` from last call be used. Default = **False**.
        """
        require_capabilities("notes", self._session.capabilities)
        params = {
            "category": category,
            "pruneBefore": modified_since,
            "exclude": "content" if no_content else None,
            "chunkSize": limit,
            "chunkCursor": cursor,
        }
        clear_from_params_empty(list(params.keys()), params)
        headers = {"If-None-Match": self.last_etag} if self.last_etag and etag else {}
        r = _res_to_json(self._session.adapter.get(self._ep_base + "/notes", params=params, headers=headers))
        self.last_etag = self._session.response_headers["ETag"]
        return [Note(i) for i in r]

    def by_id(self, note: Note) -> Note:
        """Get updated information about :py:class:`~nc_py_api.notes.Note`."""
        require_capabilities("notes", self._session.capabilities)
        r = _res_to_json(
            self._session.adapter.get(
                self._ep_base + f"/notes/{note.note_id}", headers={"If-None-Match": f'"{note.etag}"'}
            )
        )
        return Note(r) if r else note

    def create(
        self,
        title: str,
        content: str | None = None,
        category: str | None = None,
        favorite: bool | None = None,
        last_modified: int | str | datetime.datetime | None = None,
    ) -> Note:
        """Create new Note."""
        require_capabilities("notes", self._session.capabilities)
        params = {
            "title": title,
            "content": content,
            "category": category,
            "favorite": favorite,
            "modified": last_modified,
        }
        clear_from_params_empty(list(params.keys()), params)
        return Note(_res_to_json(self._session.adapter.post(self._ep_base + "/notes", json=params)))

    def update(
        self,
        note: Note,
        title: str | None = None,
        content: str | None = None,
        category: str | None = None,
        favorite: bool | None = None,
        overwrite: bool = False,
    ) -> Note:
        """Updates Note.

        ``overwrite`` specifies should be or not the Note updated even if it was changed on server(has different ETag).
        """
        require_capabilities("notes", self._session.capabilities)
        headers = {"If-Match": f'"{note.etag}"'} if not overwrite else {}
        params = {
            "title": title,
            "content": content,
            "category": category,
            "favorite": favorite,
        }
        clear_from_params_empty(list(params.keys()), params)
        if not params:
            raise ValueError("Nothing to update.")
        return Note(
            _res_to_json(
                self._session.adapter.put(self._ep_base + f"/notes/{note.note_id}", json=params, headers=headers)
            )
        )

    def delete(self, note: int | Note) -> None:
        """Deletes a Note."""
        require_capabilities("notes", self._session.capabilities)
        note_id = note.note_id if isinstance(note, Note) else note
        check_error(self._session.adapter.delete(self._ep_base + f"/notes/{note_id}"))

    def get_settings(self) -> NotesSettings:
        """Returns Notes App settings."""
        require_capabilities("notes", self._session.capabilities)
        r = _res_to_json(self._session.adapter.get(self._ep_base + "/settings"))
        return {"notes_path": r["notesPath"], "file_suffix": r["fileSuffix"]}

    def set_settings(self, notes_path: str | None = None, file_suffix: str | None = None) -> None:
        """Change specified setting(s)."""
        if notes_path is None and file_suffix is None:
            raise ValueError("No setting to change.")
        require_capabilities("notes", self._session.capabilities)
        params = {
            "notesPath": notes_path,
            "fileSuffix": file_suffix,
        }
        clear_from_params_empty(list(params.keys()), params)
        check_error(self._session.adapter.put(self._ep_base + "/settings", json=params))


class _AsyncNotesAPI:
    """Class implements Async Nextcloud Notes API."""

    _ep_base: str = "/index.php/apps/notes/api/v1"  # without `index.php` we will get 405 error.
    last_etag: str
    """Used by ``get_list``, when **etag** param is ``True``."""

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session
        self.last_etag = ""

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("notes", await self._session.capabilities)

    async def get_list(
        self,
        category: str | None = None,
        modified_since: int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        no_content: bool = False,
        etag: bool = False,
    ) -> list[Note]:
        """Get information of all Notes.

        :param category: Filter the result by category name. Notes with another category are not included in the result.
        :param modified_since: When provided only results newer than given Unix timestamp are returned.
        :param limit: Limit response to contain no more than the given number of notes.
            If there are more notes, then the result is chunked and the HTTP response header
            **X-Notes-Chunk-Cursor** is sent with a string value.

            .. note:: Use :py:attr:`~nc_py_api.nextcloud.Nextcloud.response_headers` property to achieve that.
        :param cursor: You should use the string value from the last request's HTTP response header
            ``X-Notes-Chunk-Cursor`` in order to get the next chunk of notes.
        :param no_content: Flag indicating should ``content`` field be excluded from response.
        :param etag: Flag indicating should ``ETag`` from last call be used. Default = **False**.
        """
        require_capabilities("notes", await self._session.capabilities)
        params = {
            "category": category,
            "pruneBefore": modified_since,
            "exclude": "content" if no_content else None,
            "chunkSize": limit,
            "chunkCursor": cursor,
        }
        clear_from_params_empty(list(params.keys()), params)
        headers = {"If-None-Match": self.last_etag} if self.last_etag and etag else {}
        r = _res_to_json(await self._session.adapter.get(self._ep_base + "/notes", params=params, headers=headers))
        self.last_etag = self._session.response_headers["ETag"]
        return [Note(i) for i in r]

    async def by_id(self, note: Note) -> Note:
        """Get updated information about :py:class:`~nc_py_api.notes.Note`."""
        require_capabilities("notes", await self._session.capabilities)
        r = _res_to_json(
            await self._session.adapter.get(
                self._ep_base + f"/notes/{note.note_id}", headers={"If-None-Match": f'"{note.etag}"'}
            )
        )
        return Note(r) if r else note

    async def create(
        self,
        title: str,
        content: str | None = None,
        category: str | None = None,
        favorite: bool | None = None,
        last_modified: int | str | datetime.datetime | None = None,
    ) -> Note:
        """Create new Note."""
        require_capabilities("notes", await self._session.capabilities)
        params = {
            "title": title,
            "content": content,
            "category": category,
            "favorite": favorite,
            "modified": last_modified,
        }
        clear_from_params_empty(list(params.keys()), params)
        return Note(_res_to_json(await self._session.adapter.post(self._ep_base + "/notes", json=params)))

    async def update(
        self,
        note: Note,
        title: str | None = None,
        content: str | None = None,
        category: str | None = None,
        favorite: bool | None = None,
        overwrite: bool = False,
    ) -> Note:
        """Updates Note.

        ``overwrite`` specifies should be or not the Note updated even if it was changed on server(has different ETag).
        """
        require_capabilities("notes", await self._session.capabilities)
        headers = {"If-Match": f'"{note.etag}"'} if not overwrite else {}
        params = {
            "title": title,
            "content": content,
            "category": category,
            "favorite": favorite,
        }
        clear_from_params_empty(list(params.keys()), params)
        if not params:
            raise ValueError("Nothing to update.")
        return Note(
            _res_to_json(
                await self._session.adapter.put(self._ep_base + f"/notes/{note.note_id}", json=params, headers=headers)
            )
        )

    async def delete(self, note: int | Note) -> None:
        """Deletes a Note."""
        require_capabilities("notes", await self._session.capabilities)
        note_id = note.note_id if isinstance(note, Note) else note
        check_error(await self._session.adapter.delete(self._ep_base + f"/notes/{note_id}"))

    async def get_settings(self) -> NotesSettings:
        """Returns Notes App settings."""
        require_capabilities("notes", await self._session.capabilities)
        r = _res_to_json(await self._session.adapter.get(self._ep_base + "/settings"))
        return {"notes_path": r["notesPath"], "file_suffix": r["fileSuffix"]}

    async def set_settings(self, notes_path: str | None = None, file_suffix: str | None = None) -> None:
        """Change specified setting(s)."""
        if notes_path is None and file_suffix is None:
            raise ValueError("No setting to change.")
        require_capabilities("notes", await self._session.capabilities)
        params = {
            "notesPath": notes_path,
            "fileSuffix": file_suffix,
        }
        clear_from_params_empty(list(params.keys()), params)
        check_error(await self._session.adapter.put(self._ep_base + "/settings", json=params))


def _res_to_json(response: httpx.Response) -> dict:
    check_error(response)
    return json.loads(response.text) if response.status_code != 304 else {}
