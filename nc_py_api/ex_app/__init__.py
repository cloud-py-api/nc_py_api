"""All possible ExApp stuff for NextcloudApp that can be used."""

from ..files import ActionFileInfo
from .defs import FileSystemEventNotification, LogLvl
from .integration_fastapi import (
    AppAPIAuthMiddleware,
    anc_app,
    atalk_bot_msg,
    nc_app,
    set_handlers,
    talk_bot_msg,
)
from .misc import (
    get_computation_device,
    get_model_path,
    persistent_storage,
    verify_version,
)
from .ui.settings import SettingsField, SettingsFieldType, SettingsForm
from .uvicorn_fastapi import run_app


class UiActionFileInfo(ActionFileInfo):
    """``Deprecated``: use :py:class:`~nc_py_api.files.ActionFileInfo` instead."""
