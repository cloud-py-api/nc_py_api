import pytest

from nc_py_api import NextcloudException


def test_init_poll(nc_any):
    lf = nc_any.loginflow_v2.init()
    assert isinstance(lf.endpoint, str)
    assert isinstance(lf.login, str)
    assert isinstance(lf.token, str)
    with pytest.raises(NextcloudException):
        nc_any.loginflow_v2.poll(lf.token, 1)


@pytest.mark.asyncio(scope="session")
async def test_init_poll_async(anc_any):
    lf = await anc_any.loginflow_v2.init()
    assert isinstance(lf.endpoint, str)
    assert isinstance(lf.login, str)
    assert isinstance(lf.token, str)
    with pytest.raises(NextcloudException):
        await anc_any.loginflow_v2.poll(lf.token, 1)
