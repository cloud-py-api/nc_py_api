import pytest

from nc_py_api import NextcloudException


@pytest.mark.asyncio(scope="session")
async def test_init_poll_async(anc_client):
    lf = await anc_client.loginflow_v2.init()
    assert isinstance(lf.endpoint, str)
    assert isinstance(lf.login, str)
    assert isinstance(lf.token, str)
    with pytest.raises(NextcloudException) as exc_info:
        await anc_client.loginflow_v2.poll(lf.token, 1)
    assert exc_info.value.status_code == 404
