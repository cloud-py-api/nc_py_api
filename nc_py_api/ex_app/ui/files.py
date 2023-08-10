"""Nextcloud API for working with drop-down file's menu."""
from pydantic import BaseModel

from ..._exceptions import NextcloudExceptionNotFound
from ..._misc import require_capabilities
from ..._session import NcSessionApp

ENDPOINT_SUFFIX = "files/actions/menu"


class UiActionFileInfo(BaseModel):
    """File Information Nextcloud sends to the External Application."""

    fileId: int
    name: str
    directory: str
    etag: str
    mime: str
    favorite: str
    permissions: int


class UiFileActionHandlerInfo(BaseModel):
    """Action information Nextcloud sends to the External Application."""

    actionName: str
    actionHandler: str
    actionFile: UiActionFileInfo


class _UiFilesActionsAPI:
    """API for the drop-down menu in Nextcloud ``Files`` app."""

    def __init__(self, session: NcSessionApp):
        self._session = session

    def register(self, name: str, display_name: str, callback_url: str, **kwargs) -> None:
        """Registers the files a dropdown menu element."""
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
        self._session.ocs(method="POST", path=f"{self._session.ae_url}/{ENDPOINT_SUFFIX}", json=params)

    def unregister(self, name: str, not_fail=True) -> None:
        """Removes files dropdown menu element."""
        require_capabilities("app_ecosystem_v2", self._session.capabilities)
        params = {"fileActionMenuName": name}
        try:
            self._session.ocs(method="DELETE", path=f"{self._session.ae_url}/{ENDPOINT_SUFFIX}", json=params)
        except NextcloudExceptionNotFound as e:
            if not not_fail:
                raise e from None
