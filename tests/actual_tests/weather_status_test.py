import pytest

from nc_py_api import NextcloudException, weather_status


@pytest.mark.asyncio(scope="session")
async def test_available_async(anc):
    assert await anc.weather_status.available


@pytest.mark.asyncio(scope="session")
async def test_get_set_location_async(anc_any):
    try:
        await anc_any.weather_status.set_location(longitude=0.0, latitude=0.0)
    except NextcloudException as e:
        if e.status_code in (408, 500, 996):
            pytest.skip("Some network problem on the host")
        raise e from None
    loc = await anc_any.weather_status.get_location()
    assert loc.latitude == 0.0
    assert loc.longitude == 0.0
    assert isinstance(loc.address, str)
    assert isinstance(loc.mode, int)
    try:
        assert await anc_any.weather_status.set_location(address="Paris, 75007, France")
    except NextcloudException as e:
        if e.status_code in (500, 996):
            pytest.skip("Some network problem on the host")
        raise e from None
    loc = await anc_any.weather_status.get_location()
    assert loc.latitude
    assert loc.longitude
    if loc.address.find("Unknown") != -1:
        pytest.skip("Some network problem on the host")
    assert loc.address.find("Paris") != -1
    assert await anc_any.weather_status.set_location(latitude=41.896655, longitude=12.488776)
    loc = await anc_any.weather_status.get_location()
    assert loc.latitude == 41.896655
    assert loc.longitude == 12.488776
    if loc.address.find("Unknown") != -1:
        pytest.skip("Some network problem on the host")
    assert loc.address.find("Rom") != -1


@pytest.mark.asyncio(scope="session")
async def test_get_set_location_no_lat_lon_address_async(anc):
    with pytest.raises(ValueError):
        await anc.weather_status.set_location()


@pytest.mark.asyncio(scope="session")
async def test_get_forecast_async(anc_any):
    await anc_any.weather_status.set_location(latitude=41.896655, longitude=12.488776)
    if (await anc_any.weather_status.get_location()).address.find("Unknown") != -1:
        pytest.skip("Some network problem on the host")
    forecast = await anc_any.weather_status.get_forecast()
    assert isinstance(forecast, list)
    assert forecast
    assert isinstance(forecast[0], dict)


@pytest.mark.asyncio(scope="session")
async def test_get_set_favorites_async(anc):
    await anc.weather_status.set_favorites([])
    r = await anc.weather_status.get_favorites()
    assert isinstance(r, list)
    assert not r
    await anc.weather_status.set_favorites(["Paris, France", "Madrid, Spain"])
    r = await anc.weather_status.get_favorites()
    assert any("Paris" in x for x in r)
    assert any("Madrid" in x for x in r)


@pytest.mark.asyncio(scope="session")
async def test_set_mode_async(anc):
    await anc.weather_status.set_mode(weather_status.WeatherLocationMode.MODE_BROWSER_LOCATION)
    assert (
        await anc.weather_status.get_location()
    ).mode == weather_status.WeatherLocationMode.MODE_BROWSER_LOCATION.value
    await anc.weather_status.set_mode(weather_status.WeatherLocationMode.MODE_MANUAL_LOCATION)
    assert (
        await anc.weather_status.get_location()
    ).mode == weather_status.WeatherLocationMode.MODE_MANUAL_LOCATION.value


@pytest.mark.asyncio(scope="session")
async def test_set_mode_invalid_async(anc):
    with pytest.raises(ValueError):
        await anc.weather_status.set_mode(weather_status.WeatherLocationMode.UNKNOWN)
    with pytest.raises(ValueError):
        await anc.weather_status.set_mode(0)
