# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0 - 2023-09-11]

### Changed

- AppEcosystem_V2 Project was renamed to App_API, adjust all routes, examples, and docs for this.
- The Application Authentication mechanism was changed to a much simple one.

## [0.1.0 - 2023-09-06]

### Added

- ActivityAPI: `get_filters` and `get_activities`. #112
- FilesAPI: added `tags` support. #115

### Changed

- FilesAPI: removed `listfav` method, use new more powerful `list_by_criteria` method. #115

### Fixed

- `NotificationInfo.time` - was always incorrectly parsed and equal to `datetime(1970,1,1)`

## [0.0.43 - 2023-09-02]

### Added

- Basic APIs for Nextcloud Talk(Part 2) #111

### Fixed

- `makedirs` correctly work with paths started with `/`
- `listdir` correctly handles `exclude_self=True` when input `path` starts with `/`

## [0.0.42 - 2023-08-30]

### Added

- TrashBin API:
  * `trashbin_list`
  * `trashbin_restore`
  * `trashbin_delete`
  * `trashbin_cleanup`
- File Versions API: `get_versions` and `restore_version`.

### Fixed

- Created `FsNode` from `UiActionFileInfo` now have the `file_id` with the NC instance ID as from the DAV requests.

## [0.0.41 - 2023-08-26]

### Added

- Nextcloud Talk API for bots + example

## [0.0.40 - 2023-08-22]

### Added

- Basic APIs for Nextcloud Talk(Part 1)

### Changed

- `require_capabilities`/`check_capabilities` can accept value with `dot`: like `files_sharing.api_enabled` and check for sub-values.
- Refactored all API(except `Files`) again.

### Fixed

- `options.NPA_NC_CERT` bug, when setting throw `.env` file.

## [0.0.31 - 2023-08-17]

### Added

- `FsNode` can be created from Nextcloud `UiActionFileInfo` reply.

### Fixed

- `files.find` error when searching by `"name"`. Thanks to @CooperGerman

## [0.0.30 - 2023-08-15]

### Added

- `Nextcloud.response_headers` property, to get headers from last response.

### Changed

- Reworked skeleton for the applications, added skeleton to examples.

## [0.0.29 - 2023-08-13]

### Added

- Finished `Share` API.

### Fixed

- `options` error when setting timeouts with the `.env` file.
- ShareAPI.create wrong handling of `share_with` parameter.

## [0.0.28 - 2023-08-11]

### Added

- APIs for enabling\disabling External Applications.
- FileAPI: `download_directory_as_zip` method.

### Changed

- Much more documentation.
- Regroup APIs, hopes for the last time.

### Fixed

- Assign groups in user creation

## [0.0.27 - 2023-08-05]

### Added

- `Notifications API`
- `options` now independent in each `Nextcloud` class. They can be specified in kwargs, environment or `.env` files.

### Changed

- Switched to `hatching` as a build system, now correct install optional dependencies.
- Renamed methods, attributes that was `shadowing a Python builtins`. Enabled additional `Ruff` linters checks.
- Regroup APIs, now Users related stuff starts with `user`, file related stuff with `file`, UI stuff with `gui`.

## [0.0.26 - 2023-07-29]

### Added

- More documentation.

### Changed

- Reworked `User Status API`, `Users Group API`
- Reworked return type for `weather_status.get_location`
- Reworked `Files API`: `mkdir`, `upload`, `copy`, `move` return new `FsNode` object.
- Reworked `listdir`: added `depth` parameter.
- Reworked `FsNode`: changed `info` from `TypedDict` to `dataclass`, correct fields names with correct descriptions.
- `FsNode` now allows comparison for equality.

## [0.0.25 - 2023-07-25]

### Added

- First `Files Sharing` APIs.

### Changed

- Updated documentation, description.
- Updated `FsNode` class with properties for parsing permissions.

## [0.0.24 - 2023-07-18]

### Added

- `VERIFY_NC_CERTIFICATE` option.
- `apps.ex_app_get_list` and `apps.ex_app_get_info` methods.
- `files.download2stream` and `files.upload_stream` methods.
- most of `FileAPI` can accept `FsNode` as a path.

### Changed

- License changed to `BSD-3 Clause`

## [0.0.23 - 2023-07-07]

### Fixed

- `nextcloud_url` can contain `/` at the end.
- work of `logs` during `enable`/`disable` events.

## [0.0.22 - 2023-07-05]

### Added

- `heartbeat` endpoint support for AppEcosystemV2.

## [0.0.21 - 2023-07-04]

### Added

- `app_cfg` property in the `NextcloudApp` class.

### Fixed

- All input environment variables now in Upper Case.

## [0.0.20 - 2023-07-03]

- Written from the scratch new version of the Nextcloud Python Client. Deep Alpha.
