from datetime import datetime

import pytest

from nc_py_api import NextcloudException

# Currently we test only with the client mode, waiting this to be resolved to use it in Application mode:
# https://github.com/cloud-py-api/app_api/issues/80


def test_settings(nc_client):
    if nc_client.notes.available is False:
        pytest.skip("Notes is not installed")

    original_settings = nc_client.notes.get_settings()
    assert isinstance(original_settings["file_suffix"], str)
    assert isinstance(original_settings["notes_path"], str)
    nc_client.notes.set_settings(file_suffix=".ncpa")
    modified_settings = nc_client.notes.get_settings()
    assert modified_settings["file_suffix"] == ".ncpa"
    assert modified_settings["notes_path"] == original_settings["notes_path"]
    nc_client.notes.set_settings(file_suffix=original_settings["file_suffix"])
    modified_settings = nc_client.notes.get_settings()
    assert modified_settings["file_suffix"] == original_settings["file_suffix"]


def test_create_delete(nc_client):
    if nc_client.notes.available is False:
        pytest.skip("Notes is not installed")
    unix_timestamp = (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()
    new_note = nc_client.notes.create(str(unix_timestamp))
    nc_client.notes.delete(new_note)
    assert isinstance(new_note.note_id, int)
    assert isinstance(new_note.etag, str)
    assert isinstance(new_note.title, str)
    assert isinstance(new_note.content, str)
    assert isinstance(new_note.category, str)
    assert new_note.readonly is False
    assert new_note.favorite is False
    assert isinstance(new_note.last_modified, datetime)


def test_get_update_note(nc_client):
    if nc_client.notes.available is False:
        pytest.skip("Notes is not installed")

    for i in nc_client.notes.get_list():
        nc_client.notes.delete(i)

    assert not nc_client.notes.get_list()
    unix_timestamp = (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()
    new_note = nc_client.notes.create(str(unix_timestamp))
    try:
        all_notes = nc_client.notes.get_list()
        assert all_notes[0] == new_note
        assert not nc_client.notes.get_list(etag=True)
        assert nc_client.notes.get_list()[0] == new_note
        assert nc_client.notes.by_id(new_note) == new_note
        updated_note = nc_client.notes.update(new_note, content="content")
        assert updated_note.content == "content"
        all_notes = nc_client.notes.get_list()
        assert all_notes[0].content == "content"
        all_notes_no_content = nc_client.notes.get_list(no_content=True)
        assert all_notes_no_content[0].content == ""
        assert nc_client.notes.by_id(new_note).content == "content"
        with pytest.raises(NextcloudException):
            assert nc_client.notes.update(new_note, content="should be rejected")
        new_note = nc_client.notes.update(new_note, content="should not be rejected", overwrite=True)
        nc_client.notes.update(new_note, category="test_category", favorite=True)
        new_note = nc_client.notes.by_id(new_note)
        assert new_note.favorite is True
        assert new_note.category == "test_category"
    finally:
        nc_client.notes.delete(new_note)
