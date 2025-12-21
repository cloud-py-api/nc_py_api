"""Nextcloud API for working with Recommendations."""

import dataclasses

from ._misc import check_capabilities, clear_from_params_empty, require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


@dataclasses.dataclass
class Recommendation:
    """Class representing one recommendation."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def file_id(self) -> int:
        """File ID of the recommended file."""
        return self._raw_data["fileId"]

    @property
    def file_name(self) -> str:
        """Name of the recommended file."""
        return self._raw_data["fileName"]

    @property
    def file_path(self) -> str:
        """Path to the recommended file relative to the user's root."""
        return self._raw_data["filePath"]

    @property
    def reason(self) -> str:
        """Reason why this file was recommended."""
        return self._raw_data.get("reason", "")

    @property
    def score(self) -> float:
        """Recommendation score (higher is better)."""
        return self._raw_data.get("score", 0.0)

    def __repr__(self):
        return f"<{self.__class__.__name__} file_id={self.file_id}, file_name={self.file_name}, score={self.score}>"


class _RecommendationsAPI:
    """Class providing the Recommendations API on the Nextcloud server."""

    _ep_base: str = "/ocs/v2.php/apps/recommendations/api/v1"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("recommendations", self._session.capabilities)

    def get_recommendations(self, limit: int | None = None) -> list[Recommendation]:
        """Returns a list of recommended files and folders for the current user.

        :param limit: Maximum number of recommendations to return. If not specified, all recommendations are returned.
        """
        require_capabilities("recommendations", self._session.capabilities)
        params = {"limit": limit} if limit is not None else {}
        clear_from_params_empty(list(params.keys()), params)
        result = self._session.ocs("GET", f"{self._ep_base}/recommendations", params=params)
        return [Recommendation(i) for i in result]

    def get_settings(self) -> dict:
        """Returns user recommendation settings."""
        require_capabilities("recommendations", self._session.capabilities)
        return self._session.ocs("GET", f"{self._ep_base}/settings")


class _AsyncRecommendationsAPI:
    """Class provides async Recommendations API on the Nextcloud server."""

    _ep_base: str = "/ocs/v2.php/apps/recommendations/api/v1"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("recommendations", await self._session.capabilities)

    async def get_recommendations(self, limit: int | None = None) -> list[Recommendation]:
        """Returns a list of recommended files and folders for the current user.

        :param limit: Maximum number of recommendations to return. If not specified, all recommendations are returned.
        """
        require_capabilities("recommendations", await self._session.capabilities)
        params = {"limit": limit} if limit is not None else {}
        clear_from_params_empty(list(params.keys()), params)
        result = await self._session.ocs("GET", f"{self._ep_base}/recommendations", params=params)
        return [Recommendation(i) for i in result]

    async def get_settings(self) -> dict:
        """Returns user recommendation settings."""
        require_capabilities("recommendations", await self._session.capabilities)
        return await self._session.ocs("GET", f"{self._ep_base}/settings")
