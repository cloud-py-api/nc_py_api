# Changelog

All notable changes to this project will be documented in this file.

## [0.0.26 - 2023-07-29]

### Added

- More documentation.

### Changed

- Reworked `User Status API`, `Users Group API`
- Reworked return type for `weather_status.get_location`
- Reworked `Files API`: `mkdir`, `upload`, `copy`, `move` return new `FsNode` object
- Reworked `listdir`: added `depth` parameter
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
