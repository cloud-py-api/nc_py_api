"""
Nextcloud API for working with drop down file's menu.
"""

from pydantic import BaseModel

from ._session import NcSessionApp
from .constants import APP_V2_BASIC_URL
from .exceptions import NextcloudExceptionNotFound
from .misc import require_capabilities


class UiActionFileInfo(BaseModel):
    fileId: int
    name: str
    dir: str


class UiFileActionHandlerInfo(BaseModel):
    actionName: str
    actionHandler: str
    actionFile: UiActionFileInfo


ENDPOINT_SUFFIX = "files/actions/menu"


class UiFilesActionsAPI:
    def __init__(self, session: NcSessionApp):
        self._session = session

    def register(self, name: str, display_name: str, callback_url: str, **kwargs) -> None:
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        params = {
            "fileActionMenuParams": {
                "name": name,
                "display_name": display_name,
                "mime": kwargs.get("mime", "file"),
                "permissions": kwargs.get("permissions", 31),
                "order": kwargs.get("order", 0),
                "icon": kwargs.get("icon", ""),
                "icon_class": kwargs.get("icon_class", "icon-app-ecosystem-v2"),
                "action_handler": callback_url,
            },
        }
        self._session.ocs(method="POST", path=f"{APP_V2_BASIC_URL}/{ENDPOINT_SUFFIX}", json=params)

    def unregister(self, name: str, not_fail=True) -> None:
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        params = {"fileActionMenuName": name}
        try:
            self._session.ocs(method="DELETE", path=f"{APP_V2_BASIC_URL}/{ENDPOINT_SUFFIX}", json=params)
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None
