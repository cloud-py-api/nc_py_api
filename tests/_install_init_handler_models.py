from contextlib import asynccontextmanager

from fastapi import FastAPI
from huggingface_hub import snapshot_download

from nc_py_api import NextcloudApp, ex_app

MODEL_NAME = "MBZUAI/LaMini-T5-61M"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ex_app.set_handlers(APP, enabled_handler, models_to_fetch={MODEL_NAME: {}})
    yield


APP = FastAPI(lifespan=lifespan)


def enabled_handler(enabled: bool, _nc: NextcloudApp) -> str:
    if enabled:
        try:
            snapshot_download(MODEL_NAME, local_files_only=True, cache_dir=ex_app.persistent_storage())
        except Exception:  # noqa
            return "model not found"
    return ""


if __name__ == "__main__":
    ex_app.run_app("_install_init_handler_models:APP", log_level="warning")
