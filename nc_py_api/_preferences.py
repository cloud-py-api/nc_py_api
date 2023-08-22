"""Nextcloud API for working with classics app's storage with user's context (table oc_preferences)."""

from ._misc import check_capabilities, require_capabilities
from ._session import NcSessionBasic


class PreferencesAPI:
    """API for setting/removing configuration values of applications that support it."""

    _ep_base: str = "/ocs/v1.php/apps/provisioning_api/api/v1/config/users"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("provisioning_api", self._session.capabilities)

    def set_value(self, app_name: str, key: str, value: str) -> None:
        """Sets the value for the key for the specific application."""
        require_capabilities("provisioning_api", self._session.capabilities)
        self._session.ocs(method="POST", path=f"{self._ep_base}/{app_name}/{key}", params={"configValue": value})

    def delete(self, app_name: str, key: str) -> None:
        """Removes a key and its value for a specific application."""
        require_capabilities("provisioning_api", self._session.capabilities)
        self._session.ocs(method="DELETE", path=f"{self._ep_base}/{app_name}/{key}")
