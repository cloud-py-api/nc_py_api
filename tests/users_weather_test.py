import pytest
from gfixture import NC_TO_TEST

from nc_py_api import NextcloudException, users_defs


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_available(nc):
    assert nc.users.weather.available


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_set_location(nc):
    nc.users.weather.set_location(longitude=0.0, latitude=0.0)
    loc = nc.users.weather.get_location()
    assert loc.latitude == 0.0
    assert loc.longitude == 0.0
    assert isinstance(loc.address, str)
    assert isinstance(loc.mode, int)
    try:
        assert nc.users.weather.set_location(address="Paris, 75007, France")
    except NextcloudException as e:
        if e.status_code == 500:
            pytest.skip("Some network problem on the host")
        raise e from None
    loc = nc.users.weather.get_location()
    assert loc.latitude
    assert loc.longitude
    if loc.address.find("Unknown") != -1:
        pytest.skip("Some network problem on the host")
    assert loc.address.find("Paris") != -1
    assert nc.users.weather.set_location(latitude=41.896655, longitude=12.488776)
    loc = nc.users.weather.get_location()
    assert loc.latitude == 41.896655
    assert loc.longitude == 12.488776
    if loc.address.find("Unknown") != -1:
        pytest.skip("Some network problem on the host")
    assert loc.address.find("Rom") != -1
    assert nc.users.weather.set_location(latitude=41.896655, longitude=12.488776, address="Paris, France")
    loc = nc.users.weather.get_location()
    assert loc.latitude == 41.896655
    assert loc.longitude == 12.488776
    if loc.address.find("Unknown") != -1:
        pytest.skip("Some network problem on the host")
    assert loc.address.find("Rom") != -1


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_set_location_no_lat_lon_address(nc):
    with pytest.raises(ValueError):
        nc.users.weather.set_location()


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_forecast(nc):
    nc.users.weather.set_location(latitude=41.896655, longitude=12.488776)
    if nc.users.weather.get_location().address.find("Unknown") != -1:
        pytest.skip("Some network problem on the host")
    forecast = nc.users.weather.get_forecast()
    assert isinstance(forecast, list)
    assert forecast
    assert isinstance(forecast[0], dict)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_set_favorites(nc):
    nc.users.weather.set_favorites([])
    r = nc.users.weather.get_favorites()
    assert isinstance(r, list)
    assert not r
    nc.users.weather.set_favorites(["Paris, France", "Madrid, Spain"])
    r = nc.users.weather.get_favorites()
    assert any("Paris" in x for x in r)
    assert any("Madrid" in x for x in r)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_set_mode(nc):
    nc.users.weather.set_mode(users_defs.WeatherLocationMode.MODE_BROWSER_LOCATION)
    assert nc.users.weather.get_location().mode == users_defs.WeatherLocationMode.MODE_BROWSER_LOCATION.value
    nc.users.weather.set_mode(users_defs.WeatherLocationMode.MODE_MANUAL_LOCATION)
    assert nc.users.weather.get_location().mode == users_defs.WeatherLocationMode.MODE_MANUAL_LOCATION.value


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_set_mode_invalid(nc):
    with pytest.raises(ValueError):
        nc.users.weather.set_mode(users_defs.WeatherLocationMode.UNKNOWN)
    with pytest.raises(ValueError):
        nc.users.weather.set_mode(0)