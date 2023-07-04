import pytest

from nc_py_api import NextcloudException
from nc_py_api.weather_status import WeatherLocationMode

from gfixture import NC_TO_TEST


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_available(nc):
    assert nc.weather_status.available


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_set_location(nc):
    try:
        nc.weather_status.set_location(longitude=0.0, latitude=0.0)
        loc = nc.weather_status.get_location()
        assert loc["latitude"] == 0.0
        assert loc["longitude"] == 0.0
        assert isinstance(loc["address"], str)
        assert isinstance(loc["mode"], int)
        assert nc.weather_status.set_location(address="Paris, 75007, France")
        loc = nc.weather_status.get_location()
        assert loc["latitude"]
        assert loc["longitude"]
        assert loc["address"].find("Paris") != -1
        assert nc.weather_status.set_location(latitude=41.896655, longitude=12.488776)
        loc = nc.weather_status.get_location()
        assert loc["latitude"] == 41.896655
        assert loc["longitude"] == 12.488776
        assert loc["address"].find("Rom") != -1
        assert nc.weather_status.set_location(latitude=41.896655, longitude=12.488776, address="Paris, France")
        loc = nc.weather_status.get_location()
        assert loc["latitude"] == 41.896655
        assert loc["longitude"] == 12.488776
        assert loc["address"].find("Rom") != -1
    except NextcloudException as e:
        if e.status_code != 500:
            raise e from None
        print("\033[93m" + " WARNING: Set Location failed." + "\033[0m")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_set_location_no_lat_lon_address(nc):
    with pytest.raises(ValueError):
        nc.weather_status.set_location()


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_forecast(nc):
    try:
        nc.weather_status.set_location(address="Paris, 75007, France")
        forecast = nc.weather_status.get_forecast()
        assert isinstance(forecast, list)
        assert forecast
        assert isinstance(forecast[0], dict)
    except NextcloudException as e:
        if e.status_code != 500:
            raise e from None
        print("\033[93m" + " WARNING: Get Forecast failed." + "\033[0m")


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_set_favorites(nc):
    nc.weather_status.set_favorites([])
    r = nc.weather_status.get_favorites()
    assert isinstance(r, list)
    assert not r
    nc.weather_status.set_favorites(["Paris, France", "Madrid, Spain"])
    r = nc.weather_status.get_favorites()
    assert any("Paris" in x for x in r)
    assert any("Madrid" in x for x in r)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_set_mode(nc):
    nc.weather_status.set_mode(WeatherLocationMode.MODE_BROWSER_LOCATION)
    assert nc.weather_status.get_location()["mode"] == WeatherLocationMode.MODE_BROWSER_LOCATION.value
    nc.weather_status.set_mode(WeatherLocationMode.MODE_MANUAL_LOCATION)
    assert nc.weather_status.get_location()["mode"] == WeatherLocationMode.MODE_MANUAL_LOCATION.value


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_set_mode_invalid(nc):
    with pytest.raises(ValueError):
        nc.weather_status.set_mode(WeatherLocationMode.UNKNOWN)
    with pytest.raises(ValueError):
        nc.weather_status.set_mode(0)
