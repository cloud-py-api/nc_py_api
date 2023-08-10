"""All possible ExApp stuff for NextcloudApp that can be used."""
from .defs import ApiScope, LogLvl
from .integration_fastapi import (
    enable_heartbeat,
    nc_app,
    set_enabled_handler,
    set_scopes,
)
from .ui.files import UiActionFileInfo, UiFileActionHandlerInfo
