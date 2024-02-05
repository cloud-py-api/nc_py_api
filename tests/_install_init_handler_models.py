from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from nc_py_api import NextcloudApp, ex_app

MODEL_NAME1 = "MBZUAI/LaMini-T5-61M"
MODEL_NAME2 = "https://huggingface.co/MBZUAI/LaMini-T5-61M/resolve/main/pytorch_model.bin"
MODEL_NAME3 = "https://huggingface.co/invalid_path"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ex_app.set_handlers(APP, enabled_handler, models_to_fetch={MODEL_NAME1: {}, MODEL_NAME2: {}, MODEL_NAME3: {}})
    yield


APP = FastAPI(lifespan=lifespan)


def enabled_handler(enabled: bool, _nc: NextcloudApp) -> str:
    if enabled:
        try:
            assert ex_app.get_model_path(MODEL_NAME1)
        except Exception:  # noqa
            return "model1 not found"
        assert Path("pytorch_model.bin").is_file()
    return ""


if __name__ == "__main__":
    ex_app.run_app("_install_init_handler_models:APP", log_level="warning")
