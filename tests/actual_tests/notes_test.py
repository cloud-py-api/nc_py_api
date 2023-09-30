import pytest

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
