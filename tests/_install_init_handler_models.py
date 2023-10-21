from fastapi import FastAPI
from huggingface_hub import snapshot_download

from nc_py_api import NextcloudApp, ex_app

APP = FastAPI()
MODEL_NAME = "MBZUAI/LaMini-T5-61M"


def enabled_handler(enabled: bool, _nc: NextcloudApp) -> str:
    if enabled:
        try:
            snapshot_download(MODEL_NAME, local_files_only=True, cache_dir=ex_app.persistent_storage())
        except Exception:  # noqa
            return "model not found"
    return ""


def init_handler():
    NextcloudApp().set_init_status(100)


@APP.on_event("startup")
def initialization():
    ex_app.set_handlers(APP, enabled_handler, init_handler=init_handler, models_to_fetch=[MODEL_NAME])


if __name__ == "__main__":
    ex_app.run_app("_install_init_handler_models:APP", log_level="warning")
