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


def test_propfind_constants_are_immutable():
    assert isinstance(PROPFIND_PROPERTIES, tuple)
    assert isinstance(PROPFIND_LOCKING_PROPERTIES, tuple)
    with pytest.raises(AttributeError):
        PROPFIND_PROPERTIES.append("nc:not-allowed")


def test_get_propfind_properties_does_not_mutate_constants():
    before, before_locking = PROPFIND_PROPERTIES, PROPFIND_LOCKING_PROPERTIES
    for _ in range(10):
        get_propfind_properties(CAPS_WITH_LOCKING)
        get_propfind_properties(CAPS_WITHOUT_LOCKING)
    assert before == PROPFIND_PROPERTIES
    assert before_locking == PROPFIND_LOCKING_PROPERTIES


def test_get_propfind_properties_returns_fresh_list():
    first = get_propfind_properties(CAPS_WITH_LOCKING)
    second = get_propfind_properties(CAPS_WITH_LOCKING)
    assert first == second
    assert first is not second
    first.append("nc:added-by-caller")
    assert "nc:added-by-caller" not in second
    assert "nc:added-by-caller" not in PROPFIND_PROPERTIES


def test_get_propfind_properties_locking_capability():
    with_locking = get_propfind_properties(CAPS_WITH_LOCKING)
    without_locking = get_propfind_properties(CAPS_WITHOUT_LOCKING)
    assert len(with_locking) == len(PROPFIND_PROPERTIES) + len(PROPFIND_LOCKING_PROPERTIES)
    assert len(without_locking) == len(PROPFIND_PROPERTIES)
    assert set(PROPFIND_LOCKING_PROPERTIES).issubset(with_locking)
    assert not set(PROPFIND_LOCKING_PROPERTIES).intersection(without_locking)


def test_trashbin_list_does_not_mutate_constants(monkeypatch):
    requested = []

    def _fake_listdir(_self, _user, _path, **kwargs):
        requested.append(list(kwargs["properties"]))
        return []

    monkeypatch.setattr(FilesAPI, "_listdir", _fake_listdir)
    files_api = FilesAPI(types.SimpleNamespace(user="admin"))
    before = PROPFIND_PROPERTIES
    for _ in range(3):
        files_api.trashbin_list()
    assert before == PROPFIND_PROPERTIES
    for properties in requested:
        assert properties == [*PROPFIND_PROPERTIES, *TRASHBIN_PROPERTIES]


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
    before = PROPFIND_PROPERTIES
    for _ in range(3):
        await files_api.trashbin_list()
    assert before == PROPFIND_PROPERTIES
    for properties in requested:
        assert properties == [*PROPFIND_PROPERTIES, *TRASHBIN_PROPERTIES]


def test_trashbin_list_requests_trashbin_prop_type(monkeypatch):
    calls = []

    def _fake_listdir(_self, _user, _path, **kwargs):
        calls.append(kwargs["prop_type"])
        return []

    monkeypatch.setattr(FilesAPI, "_listdir", _fake_listdir)
    FilesAPI(types.SimpleNamespace(user="admin")).trashbin_list()
    assert calls == [PropFindType.TRASHBIN]
