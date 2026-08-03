"""Tests that the shared PROPFIND property lists are never mutated in place."""

import types

import pytest

from nc_py_api.files._files import (
    PROPFIND_LOCKING_PROPERTIES,
    PROPFIND_PROPERTIES,
    PropFindType,
    get_propfind_properties,
)
from nc_py_api.files.files import FilesAPI
from nc_py_api.files.files_async import AsyncFilesAPI

CAPS_WITH_LOCKING = {"files": {"locking": "1.0"}}
CAPS_WITHOUT_LOCKING = {"files": {}}
TRASHBIN_PROPERTIES = ["nc:trashbin-filename", "nc:trashbin-original-location", "nc:trashbin-deletion-time"]
# real copies taken at import: comparing against the live constants would be vacuous
# if they are ever turned back into lists, since the name would alias the same object
EXPECTED_PROPERTIES = tuple(PROPFIND_PROPERTIES)
EXPECTED_LOCKING_PROPERTIES = tuple(PROPFIND_LOCKING_PROPERTIES)


def test_propfind_constants_are_immutable():
    assert isinstance(PROPFIND_PROPERTIES, tuple)
    assert isinstance(PROPFIND_LOCKING_PROPERTIES, tuple)
    with pytest.raises(AttributeError):
        PROPFIND_PROPERTIES.append("nc:not-allowed")


def test_get_propfind_properties_does_not_mutate_constants():
    for _ in range(10):
        get_propfind_properties(CAPS_WITH_LOCKING)
        get_propfind_properties(CAPS_WITHOUT_LOCKING)
    assert tuple(PROPFIND_PROPERTIES) == EXPECTED_PROPERTIES
    assert tuple(PROPFIND_LOCKING_PROPERTIES) == EXPECTED_LOCKING_PROPERTIES


def test_get_propfind_properties_returns_fresh_list():
    first = get_propfind_properties(CAPS_WITH_LOCKING)
    second = get_propfind_properties(CAPS_WITH_LOCKING)
    assert isinstance(first, list)
    assert first == second
    assert first is not second
    first.append("nc:added-by-caller")
    assert "nc:added-by-caller" not in second
    assert "nc:added-by-caller" not in PROPFIND_PROPERTIES
    assert tuple(PROPFIND_PROPERTIES) == EXPECTED_PROPERTIES


def test_get_propfind_properties_locking_capability():
    with_locking = get_propfind_properties(CAPS_WITH_LOCKING)
    without_locking = get_propfind_properties(CAPS_WITHOUT_LOCKING)
    assert with_locking == [*EXPECTED_PROPERTIES, *EXPECTED_LOCKING_PROPERTIES]
    assert without_locking == list(EXPECTED_PROPERTIES)


def test_trashbin_list_does_not_mutate_constants(monkeypatch):
    requested = []

    def _fake_listdir(_self, _user, _path, **kwargs):
        requested.append(list(kwargs["properties"]))
        return []

    monkeypatch.setattr(FilesAPI, "_listdir", _fake_listdir)
    files_api = FilesAPI(types.SimpleNamespace(user="admin"))
    for _ in range(3):
        files_api.trashbin_list()
    assert tuple(PROPFIND_PROPERTIES) == EXPECTED_PROPERTIES
    for properties in requested:
        assert properties == [*EXPECTED_PROPERTIES, *TRASHBIN_PROPERTIES]


async def test_trashbin_list_async_does_not_mutate_constants(monkeypatch):
    requested = []

    async def _fake_listdir(_self, _user, _path, **kwargs):
        requested.append(list(kwargs["properties"]))
        return []

    class _StubSession:
        @property
        async def user(self) -> str:
            return "admin"

    monkeypatch.setattr(AsyncFilesAPI, "_listdir", _fake_listdir)
    files_api = AsyncFilesAPI(_StubSession())
    for _ in range(3):
        await files_api.trashbin_list()
    assert tuple(PROPFIND_PROPERTIES) == EXPECTED_PROPERTIES
    for properties in requested:
        assert properties == [*EXPECTED_PROPERTIES, *TRASHBIN_PROPERTIES]


def test_trashbin_list_requests_trashbin_prop_type(monkeypatch):
    calls = []

    def _fake_listdir(_self, _user, _path, **kwargs):
        calls.append(kwargs["prop_type"])
        return []

    monkeypatch.setattr(FilesAPI, "_listdir", _fake_listdir)
    FilesAPI(types.SimpleNamespace(user="admin")).trashbin_list()
    assert calls == [PropFindType.TRASHBIN]
