"""Nextcloud API for working with weather statuses."""

import dataclasses
import enum

from ._misc import check_capabilities, require_capabilities
from ._session import AsyncNcSessionBasic, NcSessionBasic


class WeatherLocationMode(enum.IntEnum):
    """Source from where Nextcloud should determine user's location."""

    UNKNOWN = 0
    """Source is not defined"""
    MODE_BROWSER_LOCATION = 1
    """User location taken from the browser"""
    MODE_MANUAL_LOCATION = 2
    """User has set their location manually"""


@dataclasses.dataclass
class WeatherLocation:
    """Class representing information about the user's location."""

    latitude: float
    """Latitude in decimal degree format"""
    longitude: float
    """Longitude in decimal degree format"""
    address: str
    """Any approximate or exact address"""
    mode: WeatherLocationMode
    """Weather status mode"""

    def __init__(self, raw_location: dict):
        lat = raw_location.get("lat", "")
        lon = raw_location.get("lon", "")
        self.latitude = float(lat if lat else "0")
        self.longitude = float(lon if lon else "0")
        self.address = raw_location.get("address", "")
        self.mode = WeatherLocationMode(int(raw_location.get("mode", 0)))


class _WeatherStatusAPI:
    """Class providing the weather status management API on the Nextcloud server."""

    _ep_base: str = "/ocs/v1.php/apps/weather_status/api/v1"

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("weather_status.enabled", self._session.capabilities)

    def get_location(self) -> WeatherLocation:
        """Returns the current location set on the Nextcloud server for the user."""
        require_capabilities("weather_status.enabled", self._session.capabilities)
        return WeatherLocation(self._session.ocs("GET", f"{self._ep_base}/location"))

    def set_location(
        self,
        latitude: float | None = None,
        longitude: float | None = None,
        address: str | None = None,
    ) -> bool:
        """Sets the user's location on the Nextcloud server.

        :param latitude: north-south position of a point on the surface of the Earth.
        :param longitude: east-west position of a point on the surface of the Earth.
        :param address: city, index(*optional*) and country, e.g. "Paris, 75007, France"
        """
        require_capabilities("weather_status.enabled", self._session.capabilities)
        params: dict[str, str | float] = {}
        if latitude is not None and longitude is not None:
            params.update({"lat": latitude, "lon": longitude})
        elif address:
            params["address"] = address
        else:
            raise ValueError("latitude & longitude or address should be present")
        result = self._session.ocs("PUT", f"{self._ep_base}/location", params=params)
        return result.get("success", False)

    def get_forecast(self) -> list[dict]:
        """Get forecast for the current location."""
        require_capabilities("weather_status.enabled", self._session.capabilities)
        return self._session.ocs("GET", f"{self._ep_base}/forecast")

    def get_favorites(self) -> list[str]:
        """Returns favorites addresses list."""
        require_capabilities("weather_status.enabled", self._session.capabilities)
        return self._session.ocs("GET", f"{self._ep_base}/favorites")

    def set_favorites(self, favorites: list[str]) -> bool:
        """Sets favorites addresses list."""
        require_capabilities("weather_status.enabled", self._session.capabilities)
        result = self._session.ocs("PUT", f"{self._ep_base}/favorites", json={"favorites": favorites})
        return result.get("success", False)

    def set_mode(self, mode: WeatherLocationMode) -> bool:
        """Change the weather status mode."""
        if int(mode) == WeatherLocationMode.UNKNOWN.value:
            raise ValueError("This mode can not be set")
        require_capabilities("weather_status.enabled", self._session.capabilities)
        result = self._session.ocs("PUT", f"{self._ep_base}/mode", params={"mode": int(mode)})
        return result.get("success", False)


class _AsyncWeatherStatusAPI:
    """Class provides async weather status management API on the Nextcloud server."""

    _ep_base: str = "/ocs/v1.php/apps/weather_status/api/v1"

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("weather_status.enabled", await self._session.capabilities)

    async def get_location(self) -> WeatherLocation:
        """Returns the current location set on the Nextcloud server for the user."""
        require_capabilities("weather_status.enabled", await self._session.capabilities)
        return WeatherLocation(await self._session.ocs("GET", f"{self._ep_base}/location"))

    async def set_location(
        self,
        latitude: float | None = None,
        longitude: float | None = None,
        address: str | None = None,
    ) -> bool:
        """Sets the user's location on the Nextcloud server.

        :param latitude: north-south position of a point on the surface of the Earth.
        :param longitude: east-west position of a point on the surface of the Earth.
        :param address: city, index(*optional*) and country, e.g. "Paris, 75007, France"
        """
        require_capabilities("weather_status.enabled", await self._session.capabilities)
        params: dict[str, str | float] = {}
        if latitude is not None and longitude is not None:
            params.update({"lat": latitude, "lon": longitude})
        elif address:
            params["address"] = address
        else:
            raise ValueError("latitude & longitude or address should be present")
        result = await self._session.ocs("PUT", f"{self._ep_base}/location", params=params)
        return result.get("success", False)

    async def get_forecast(self) -> list[dict]:
        """Get forecast for the current location."""
        require_capabilities("weather_status.enabled", await self._session.capabilities)
        return await self._session.ocs("GET", f"{self._ep_base}/forecast")

    async def get_favorites(self) -> list[str]:
        """Returns favorites addresses list."""
        require_capabilities("weather_status.enabled", await self._session.capabilities)
        return await self._session.ocs("GET", f"{self._ep_base}/favorites")

    async def set_favorites(self, favorites: list[str]) -> bool:
        """Sets favorites addresses list."""
        require_capabilities("weather_status.enabled", await self._session.capabilities)
        result = await self._session.ocs("PUT", f"{self._ep_base}/favorites", json={"favorites": favorites})
        return result.get("success", False)

    async def set_mode(self, mode: WeatherLocationMode) -> bool:
        """Change the weather status mode."""
        if int(mode) == WeatherLocationMode.UNKNOWN.value:
            raise ValueError("This mode can not be set")
        require_capabilities("weather_status.enabled", await self._session.capabilities)
        result = await self._session.ocs("PUT", f"{self._ep_base}/mode", params={"mode": int(mode)})
        return result.get("success", False)
