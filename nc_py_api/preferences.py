"""
Nextcloud API for working with classics app's storage with user's context (table oc_preferences).
"""

from ._session import NcSessionBasic
from .misc import check_capabilities, require_capabilities

ENDPOINT = "/ocs/v1.php/apps/provisioning_api/api/v1/config/users"


class PreferencesAPI:
    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        return not check_capabilities("provisioning_api", self._session.capabilities)

    def set(self, app_name: str, key: str, value: str) -> None:
        require_capabilities("provisioning_api", self._session.capabilities)
        self._session.ocs(method="POST", path=f"{ENDPOINT}/{app_name}/{key}", params={"configValue": value})

    def delete(self, app_name: str, key: str) -> None:
        require_capabilities("provisioning_api", self._session.capabilities)
        self._session.ocs(method="DELETE", path=f"{ENDPOINT}/{app_name}/{key}")
