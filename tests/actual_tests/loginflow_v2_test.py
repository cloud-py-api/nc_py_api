import pytest

from nc_py_api import NextcloudException


def test_init_poll(nc_client):
    lf = nc_client.loginflow_v2.init()
    assert isinstance(lf.endpoint, str)
    assert isinstance(lf.login, str)
    assert isinstance(lf.token, str)
    with pytest.raises(NextcloudException):
        nc_client.loginflow_v2.poll(lf.token, 1)


@pytest.mark.asyncio(scope="session")
async def test_init_poll_async(anc_client):
    lf = await anc_client.loginflow_v2.init()
    assert isinstance(lf.endpoint, str)
    assert isinstance(lf.login, str)
    assert isinstance(lf.token, str)
    with pytest.raises(NextcloudException):
        await anc_client.loginflow_v2.poll(lf.token, 1)
