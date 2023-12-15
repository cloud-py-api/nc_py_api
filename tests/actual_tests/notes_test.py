from datetime import datetime

import pytest

from nc_py_api import NextcloudException, notes


def test_settings(nc_any):
    if nc_any.notes.available is False:
        pytest.skip("Notes is not installed")

    original_settings = nc_any.notes.get_settings()
    assert isinstance(original_settings["file_suffix"], str)
    assert isinstance(original_settings["notes_path"], str)
    nc_any.notes.set_settings(file_suffix=".ncpa")
    modified_settings = nc_any.notes.get_settings()
    assert modified_settings["file_suffix"] == ".ncpa"
    assert modified_settings["notes_path"] == original_settings["notes_path"]
    nc_any.notes.set_settings(file_suffix=original_settings["file_suffix"])
    modified_settings = nc_any.notes.get_settings()
    assert modified_settings["file_suffix"] == original_settings["file_suffix"]
    with pytest.raises(ValueError):
        nc_any.notes.set_settings()


@pytest.mark.asyncio(scope="session")
async def test_settings_async(anc_any):
    if await anc_any.notes.available is False:
        pytest.skip("Notes is not installed")

    original_settings = await anc_any.notes.get_settings()
    assert isinstance(original_settings["file_suffix"], str)
    assert isinstance(original_settings["notes_path"], str)
    await anc_any.notes.set_settings(file_suffix=".ncpa")
    modified_settings = await anc_any.notes.get_settings()
    assert modified_settings["file_suffix"] == ".ncpa"
    assert modified_settings["notes_path"] == original_settings["notes_path"]
    await anc_any.notes.set_settings(file_suffix=original_settings["file_suffix"])
    modified_settings = await anc_any.notes.get_settings()
    assert modified_settings["file_suffix"] == original_settings["file_suffix"]
    with pytest.raises(ValueError):
        await anc_any.notes.set_settings()


def test_create_delete(nc_any):
    if nc_any.notes.available is False:
        pytest.skip("Notes is not installed")
    unix_timestamp = (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()
    new_note = nc_any.notes.create(str(unix_timestamp))
    nc_any.notes.delete(new_note)
    _test_create_delete(new_note)


@pytest.mark.asyncio(scope="session")
async def test_create_delete_async(anc_any):
    if await anc_any.notes.available is False:
        pytest.skip("Notes is not installed")
    unix_timestamp = (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()
    new_note = await anc_any.notes.create(str(unix_timestamp))
    await anc_any.notes.delete(new_note)
    _test_create_delete(new_note)


def _test_create_delete(new_note: notes.Note):
    assert isinstance(new_note.note_id, int)
    assert isinstance(new_note.etag, str)
    assert isinstance(new_note.title, str)
    assert isinstance(new_note.content, str)
    assert isinstance(new_note.category, str)
    assert new_note.readonly is False
    assert new_note.favorite is False
    assert isinstance(new_note.last_modified, datetime)
    assert str(new_note).find("title=") != -1


def test_get_update_note(nc_any):
    if nc_any.notes.available is False:
        pytest.skip("Notes is not installed")

    for i in nc_any.notes.get_list():
        nc_any.notes.delete(i)

    assert not nc_any.notes.get_list()
    unix_timestamp = (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()
    new_note = nc_any.notes.create(str(unix_timestamp))
    try:
        all_notes = nc_any.notes.get_list()
        assert all_notes[0] == new_note
        assert not nc_any.notes.get_list(etag=True)
        assert nc_any.notes.get_list()[0] == new_note
        assert nc_any.notes.by_id(new_note) == new_note
        updated_note = nc_any.notes.update(new_note, content="content")
        assert updated_note.content == "content"
        all_notes = nc_any.notes.get_list()
        assert all_notes[0].content == "content"
        all_notes_no_content = nc_any.notes.get_list(no_content=True)
        assert all_notes_no_content[0].content == ""
        assert nc_any.notes.by_id(new_note).content == "content"
        with pytest.raises(NextcloudException):
            assert nc_any.notes.update(new_note, content="should be rejected")
        new_note = nc_any.notes.update(new_note, content="should not be rejected", overwrite=True)
        nc_any.notes.update(new_note, category="test_category", favorite=True)
        new_note = nc_any.notes.by_id(new_note)
        assert new_note.favorite is True
        assert new_note.category == "test_category"
    finally:
        nc_any.notes.delete(new_note)


@pytest.mark.asyncio(scope="session")
async def test_get_update_note_async(anc_any):
    if await anc_any.notes.available is False:
        pytest.skip("Notes is not installed")

    for i in await anc_any.notes.get_list():
        await anc_any.notes.delete(i)

    assert not await anc_any.notes.get_list()
    unix_timestamp = (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()
    new_note = await anc_any.notes.create(str(unix_timestamp))
    try:
        all_notes = await anc_any.notes.get_list()
        assert all_notes[0] == new_note
        assert not await anc_any.notes.get_list(etag=True)
        assert (await anc_any.notes.get_list())[0] == new_note
        assert await anc_any.notes.by_id(new_note) == new_note
        updated_note = await anc_any.notes.update(new_note, content="content")
        assert updated_note.content == "content"
        all_notes = await anc_any.notes.get_list()
        assert all_notes[0].content == "content"
        all_notes_no_content = await anc_any.notes.get_list(no_content=True)
        assert all_notes_no_content[0].content == ""
        assert (await anc_any.notes.by_id(new_note)).content == "content"
        with pytest.raises(NextcloudException):
            assert await anc_any.notes.update(new_note, content="should be rejected")
        new_note = await anc_any.notes.update(new_note, content="should not be rejected", overwrite=True)
        await anc_any.notes.update(new_note, category="test_category", favorite=True)
        new_note = await anc_any.notes.by_id(new_note)
        assert new_note.favorite is True
        assert new_note.category == "test_category"
    finally:
        await anc_any.notes.delete(new_note)


def test_update_note_invalid_param(nc_any):
    if nc_any.notes.available is False:
        pytest.skip("Notes is not installed")
    with pytest.raises(ValueError):
        nc_any.notes.update(notes.Note({"id": 0, "etag": "42242"}))


@pytest.mark.asyncio(scope="session")
async def test_update_note_invalid_param_async(anc_any):
    if await anc_any.notes.available is False:
        pytest.skip("Notes is not installed")
    with pytest.raises(ValueError):
        await anc_any.notes.update(notes.Note({"id": 0, "etag": "42242"}))
