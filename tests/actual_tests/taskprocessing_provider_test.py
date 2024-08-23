import pytest

from nc_py_api import NextcloudException, NextcloudExceptionNotFound
from nc_py_api.ex_app.providers.task_processing import TaskProcessingProvider


@pytest.mark.require_nc(major=30)
def test_task_processing_provider(nc_app):
    provider_info = TaskProcessingProvider(
        id=f"test_id", name=f"Test Display Name", task_type="core:text2image"  # noqa
    )
    nc_app.providers.task_processing.register(provider_info)
    nc_app.providers.task_processing.unregister(provider_info.id)
    with pytest.raises(NextcloudExceptionNotFound):
        nc_app.providers.task_processing.unregister(provider_info.id, not_fail=False)
    nc_app.providers.task_processing.unregister(provider_info.id)
    nc_app.providers.task_processing.register(provider_info)
    assert not nc_app.providers.task_processing.next_task(["test_id"], ["core:text2image"])
    assert not nc_app.providers.task_processing.set_progress(9999, 0.5)
    assert not nc_app.providers.task_processing.report_result(9999, error_message="no such task")
    with pytest.raises(NextcloudException):
        nc_app.providers.task_processing.upload_result_file(9999, b"00")
    nc_app.providers.task_processing.unregister(provider_info.id, not_fail=False)


@pytest.mark.asyncio(scope="session")
@pytest.mark.require_nc(major=30)
async def test_task_processing_async(anc_app):
    provider_info = TaskProcessingProvider(
        id=f"test_id", name=f"Test Display Name", task_type="core:text2image"  # noqa
    )
    await anc_app.providers.task_processing.register(provider_info)
    await anc_app.providers.task_processing.unregister(provider_info.id)
    with pytest.raises(NextcloudExceptionNotFound):
        await anc_app.providers.task_processing.unregister(provider_info.id, not_fail=False)
    await anc_app.providers.task_processing.unregister(provider_info.id)
    await anc_app.providers.task_processing.register(provider_info)
    assert not await anc_app.providers.task_processing.next_task(["test_id"], ["core:text2image"])
    assert not await anc_app.providers.task_processing.set_progress(9999, 0.5)
    assert not await anc_app.providers.task_processing.report_result(9999, error_message="no such task")
    with pytest.raises(NextcloudException):
        await anc_app.providers.task_processing.upload_result_file(9999, b"00")
    await anc_app.providers.task_processing.unregister(provider_info.id, not_fail=False)


@pytest.mark.require_nc(major=30)
def test_task_processing_provider_fail_report(nc_app):
    nc_app.providers.task_processing.report_result(999999)


@pytest.mark.asyncio(scope="session")
@pytest.mark.require_nc(major=30)
async def test_task_processing_provider_fail_report_async(anc_app):
    await anc_app.providers.task_processing.report_result(999999)
