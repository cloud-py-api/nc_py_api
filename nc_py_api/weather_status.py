"""
Nextcloud API for working with weather statuses.
"""

from enum import IntEnum
from typing import Optional, TypedDict, Union

from ._session import NcSessionBasic
from .misc import check_capabilities, require_capabilities

ENDPOINT = "/ocs/v1.php/apps/weather_status/api/v1"


class WeatherLocationMode(IntEnum):
    UNKNOWN = 0
    MODE_BROWSER_LOCATION = 1
    MODE_MANUAL_LOCATION = 2


class WeatherLocation(TypedDict):
    latitude: float
    longitude: float
    address: str
    mode: WeatherLocationMode


class WeatherStatusAPI:
    def __init__(self, session: NcSessionBasic):
        self._session = session

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""

        return not check_capabilities("weather_status", self._session.capabilities)

    def get_location(self) -> WeatherLocation:
        require_capabilities("weather_status", self._session.capabilities)
        result = self._session.ocs(method="GET", path=f"{ENDPOINT}/location")
        lat = result.get("lat", "")
        lon = result.get("lon", "")
        return {
            "latitude": float(lat if lat else "0"),
            "longitude": float(lon if lon else "0"),
            "address": result.get("address", ""),
            "mode": WeatherLocationMode(int(result.get("mode", 0))),
        }

    def set_location(
        self, latitude: Optional[float] = None, longitude: Optional[float] = None, address: Optional[str] = None
    ) -> bool:
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
        require_capabilities("weather_status", self._session.capabilities)
        return self._session.ocs(method="GET", path=f"{ENDPOINT}/forecast")

    def get_favorites(self) -> list[str]:
        require_capabilities("weather_status", self._session.capabilities)
        return self._session.ocs(method="GET", path=f"{ENDPOINT}/favorites")

    def set_favorites(self, favorites: list[str]) -> bool:
        require_capabilities("weather_status", self._session.capabilities)
        result = self._session.ocs(method="PUT", path=f"{ENDPOINT}/favorites", json={"favorites": favorites})
        return result.get("success", False)

    def set_mode(self, mode: WeatherLocationMode) -> bool:
        if int(mode) == WeatherLocationMode.UNKNOWN.value:
            raise ValueError("This mode can not be set")
        require_capabilities("weather_status", self._session.capabilities)
        result = self._session.ocs(method="PUT", path=f"{ENDPOINT}/mode", params={"mode": int(mode)})
        return result.get("success", False)
