"""
Nextcloud API for working with weather statuses.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Union

from ._session import NcSessionBasic
from .misc import check_capabilities, require_capabilities

ENDPOINT = "/ocs/v1.php/apps/weather_status/api/v1"


class WeatherLocationMode(IntEnum):
    """Source from where Nextcloud should determine user's location."""

    UNKNOWN = 0
    """Source is not defined"""
    MODE_BROWSER_LOCATION = 1
    """User location taken from the browser"""
    MODE_MANUAL_LOCATION = 2
    """User has set their location manually"""


@dataclass
class WeatherLocation:
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


class WeatherStatusAPI:
    """The class provides the weather status management API on the Nextcloud server."""

    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""

        return not check_capabilities("weather_status", self._session.capabilities)

    def get_location(self) -> WeatherLocation:
        """Returns the current location set on the Nextcloud server for the user."""

        require_capabilities("weather_status", self._session.capabilities)
        return WeatherLocation(self._session.ocs(method="GET", path=f"{ENDPOINT}/location"))

    def set_location(
        self, latitude: Optional[float] = None, longitude: Optional[float] = None, address: Optional[str] = None
    ) -> bool:
        """Sets the user's location on the Nextcloud server.

        :param latitude: north–south position of a point on the surface of the Earth.
        :param longitude: east–west position of a point on the surface of the Earth.
        :param address: city, index(*optional*) and country, e.g. "Paris, 75007, France"
        """

        require_capabilities("weather_status", self._session.capabilities)
        params: dict[str, Union[str, float]] = {}
        if latitude is not None and longitude is not None:
            params.update({"lat": latitude, "lon": longitude})
        elif address:
            params["address"] = address
        else:
            raise ValueError("latitude & longitude or address should be present")
        result = self._session.ocs(method="PUT", path=f"{ENDPOINT}/location", params=params)
        return result.get("success", False)

    def get_forecast(self) -> list[dict]:
        """Get forecast for the current location."""

        require_capabilities("weather_status", self._session.capabilities)
        return self._session.ocs(method="GET", path=f"{ENDPOINT}/forecast")

    def get_favorites(self) -> list[str]:
        """Returns favorites addresses list."""

        require_capabilities("weather_status", self._session.capabilities)
        return self._session.ocs(method="GET", path=f"{ENDPOINT}/favorites")

    def set_favorites(self, favorites: list[str]) -> bool:
        """Sets favorites addresses list."""

        require_capabilities("weather_status", self._session.capabilities)
        result = self._session.ocs(method="PUT", path=f"{ENDPOINT}/favorites", json={"favorites": favorites})
        return result.get("success", False)

    def set_mode(self, mode: WeatherLocationMode) -> bool:
        """Change the weather status mode."""

        if int(mode) == WeatherLocationMode.UNKNOWN.value:
            raise ValueError("This mode can not be set")
        require_capabilities("weather_status", self._session.capabilities)
        result = self._session.ocs(method="PUT", path=f"{ENDPOINT}/mode", params={"mode": int(mode)})
        return result.get("success", False)
