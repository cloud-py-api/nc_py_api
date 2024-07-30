# Changelog

All notable changes to this project will be documented in this file.

## [0.15.1 - 2024-07-30]

### Fixed

- Corrected behaviour of `ocs` function for `Group Folders` app routes(they are not fully OCS API). #279
- NextcloudApp: `get_computation_device` function now correctly returns result in upper_case. #278

## [0.15.0 - 2024-07-19]

### Added

- Initial Webhooks API support for the upcoming Nextcloud 30. #272

### Changed

- NextcloudApp: `fetch_models_task` function now saves paths to downloaded models. #274 Thanks to @kyteinsky

## [0.14.0 - 2024-07-09]

### Added

- `LoginFlowV2` implementation by @blvdek #255
- `files.get_tags` function to get all tags assigned to the file or directory. #260
- NextcloudApp: `nc.ui.files_dropdown_menu.register_ex` to register new version of FileActions(AppAPI 2.6.0+) #252
- NextcloudApp: `enabled_state` property to check if the current ExApp is disabled or enabled. #268
- NextcloudApp: support for the new AI API for the Nextcloud 30. #254

## [0.13.0 - 2024-04-28]

### Added

- NextcloudApp: `occ` commands registration API(AppAPI 2.5.0+). #247
- NextcloudApp: `Nodes` events listener registration API(AppAPI 2.5.0+). #249

## [0.12.1 - 2024-04-05]

### Fixed

- Incorrect `Display name` when creating user, which led to the parameter being ignored. #239 Thanks to @derekbuckley

## [0.12.0 - 2024-04-02]

Update with new features only for `NextcloudApp` class. #233

### Added

- `ex_app.get_computation_device` function for retrieving GPU type(only with AppAPI `2.5.0`+).
- `ex_app.integration_fastapi.fetch_models_task` are now public function, added `progress_init_start_value` param.
- Global authentication when used now sets `request.scope["username"]` for easy use.

### Changed

- `UiActionFileInfo` class marked as deprecated, instead `ActionFileInfo` class should be used.

## [0.11.0 - 2024-02-17]

### Added

- Files: `lock` and `unlock` methods, lock file information to `FsNode`. #227

### Fixed

- NextcloudApp: `MachineTranslation` provider registration - added optional `actionDetectLang` param. #229

## [0.10.0 - 2024-02-14]

### Added

- NextcloudApp: `set_handlers`: `models_to_fetch` can now accept direct links to a files to download. #217
- NextcloudApp: DeclarativeSettings UI API for Nextcloud `29`. #222

### Changed

- NextcloudApp: adjusted code related to changes in AppAPI `2.0.3` #216
- NextcloudApp: `set_handlers` **rework of optional parameters** see PR for information. #226

## [0.9.0 - 2024-01-25]

### Added

- class `Share`: added missing `file_source_id`, `can_edit`, `can_delete` properties. #206
- NextcloudApp: `AppAPIAuthMiddleware` for easy cover all endpoints. #205
- NextcloudApp: API for registering `MachineTranslation` providers(*avalaible from Nextcloud 29*). #207

### Changed

- **large amount of incompatible changes** for `AppAPI 2.0`, see PR for description. #212
- class `Share`.raw_data marked as deprecated and changed to `_raw_data`. #206
- `ex_app.talk_bot_app`/`ex_app.atalk_bot_app` renamed to `ex_app.talk_bot_msg`/`ex_app.atalk_bot_msg`.

## [0.8.0 - 2024-01-12]

### Added

- `download_log` method to download `nextcloud.log`. #199
- NextcloudApp: API for registering `Speech to Text` providers(*avalaible from Nextcloud 29*). #196
- NextcloudApp: API for registering `Text Processing` providers(*avalaible from Nextcloud 29*). #198
- NextcloudApp: added `get_model_path` wrapper around huggingface_hub:snapshot_download. #202

### Fixed

- OCS: Correctly handling of `HTTP 204 No Content` status. #197

## [0.7.2 - 2023-12-28]

### Fixed

- files: proper url encoding of special chars in `mkdir` and `delete` methods. #191 Thanks to @tobenary
- files: proper url encoding of special chars in all other `DAV` methods. #194

## [0.7.1 - 2023-12-21]

### Added

- The `ocs` method is now public, making it easy to use Nextcloud OCS that has not yet been described. #187

## [0.7.0 - 2023-12-17]

### Added

- implemented `AsyncNextcloud` and `AsyncNextcloudApp` classes. #181

### Changed

- set_handlers: `enabled_handler`, `heartbeat_handler`, `init_handler` now can be async(Coroutines). #175 #181
- set_handlers: `models_to_fetch` and `models_download_params` united in one more flexible parameter. #184
- drop Python 3.9 support. #180
- internal code refactoring and clean-up #177

## [0.6.0 - 2023-12-06]

### Added

- Ability to develop applications with `UI`, example of such app, support for all new stuff of `AppAPI 1.4`. #168

### Fixed

- AppAPI: added authentication to the `/init` endpoint. #162

## [0.5.1 - 2023-11-12]

### Fixed

- `move`, `copy`, `trashbin_restore` correctly set `utf-8` headers. #157 Thanks to @tschechniker
- `upload_stream` correctly set `utf-8` headers. #159
- `headers` can now be `httpx.Headers` and not only `dict`. #158

## [0.5.0 - 2023-10-23]

### Added

- Support for the new `/init` AppAPI endpoint and the ability to automatically load models from `huggingface`. #151

### Changed

- All examples were adjusted to changes in AppAPI.
- The examples now use FastAPIs `lifespan` instead of the deprecated `on_event`.

## [0.4.0 - 2023-10-15]

As the project moves closer to `beta`, final unification changes are being made.
This release contains some breaking changes in `users`, `notifications` API.

### Added

- Support for users avatars(`get_avatar`). #149
- `__repr__` method added for most objects(previously it was only present for `FsNode`). #147

### Changed

- `users.get_details` renamed to `get_user` and returns a class instead of a dictionary. #145
- Optional argument `displayname` in `users.create` renamed to `display_name`.
- The `apps.ExAppInfo` class has been rewritten in the same format as all the others. #146
- `notifications.Notification` class has been rewritten in the same format as all the others.

### Fixed

- `users.get_details` with empty parameter in some cases was raised exception.
- ClientMode: in case when LDAP was used as user backend, user login differs from `user id`, and most API failed with 404. #148

## [0.3.1 - 2023-10-07]

### Added

- CalendarAPI with the help of [caldav](https://pypi.org/project/caldav/) package. #136
- [NotesAPI](https://github.com/nextcloud/notes) #137
- TalkAPI: `list_participants` method to list conversation participants. #142

### Fixed

- TalkAPI: In One-to-One conversations the `status_message` and `status_icon` fields were always empty.
- Missing CSS styles in the documentation. #143

## [0.3.0 - 2023-09-28]

### Added

- TalkAPI:
  * `send_file` to easy send `FsNode` to Talk chat.
  * `receive_messages` can return the `TalkFileMessage` subclass of usual `TalkMessage` with additional functionality.
- NextcloudApp: The `ex_app.verify_version` function to simply check whether the application has been updated.

### Changed

- NextcloudApp: Updated `info.xml` in examples to reflect upcoming changes in the [AppStore](https://github.com/nextcloud/appstore/pull/1145)

## [0.2.2 - 2023-09-26]

### Added

- FilesAPI: [Chunked v2 upload](https://docs.nextcloud.com/server/latest/developer_manual/client_apis/WebDAV/chunking.html#chunked-upload-v2) support, enabled by default.
- New option to disable `chunked v2 upload` if there is a need for that: `CHUNKED_UPLOAD_V2`
- TalkAPI: Poll API support(create_poll, get_poll, vote_poll, close_poll).
- TalkAPI: Conversation avatar API(get_conversation_avatar, set_conversation_avatar, delete_conversation_avatar)

### Changed

- Default `chunk_size` argument is now 5Mb instead of 4Mb.

## [0.2.1 - 2023-09-14]

### Added

- NextcloudApp: `ex_app.persistent_storage` function that returns path for the Application persistent storage.
- NextcloudApp: `from nc_py_api.ex_app import persist_transformers_cache` - automatic use of persistent app directory for the AI models caching.

## [0.2.0 - 2023-09-13]

### Added

- FilesAPI: `FsNode.info` added `mimetype` property.

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
