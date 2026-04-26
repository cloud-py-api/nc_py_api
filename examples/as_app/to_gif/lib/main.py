"""Simplest example of files_dropdown_menu + notification."""

import asyncio
import tempfile
from contextlib import asynccontextmanager
from os import path
from typing import Annotated

import cv2
import imageio
import numpy
from fastapi import BackgroundTasks, Depends, FastAPI, responses
from pygifsicle import optimize

from nc_py_api import FsNode, NextcloudApp
from nc_py_api.ex_app import AppAPIAuthMiddleware, LogLvl, nc_app, run_app, set_handlers
from nc_py_api.files import ActionFileInfoEx


@asynccontextmanager
async def lifespan(app: FastAPI):
    set_handlers(app, enabled_handler)
    yield


APP = FastAPI(lifespan=lifespan)
APP.add_middleware(AppAPIAuthMiddleware)


def _build_gif(in_path: str, out_path: str) -> None:
    """Synchronous CPU/IO-heavy work — extracted so it can run via :func:`asyncio.to_thread`."""
    cap = cv2.VideoCapture(in_path)
    image_lst = []
    previous_frame = None
    skip = 0
    while True:
        skip += 1
        _ret, frame = cap.read()
        if frame is None:
            break
        if skip == 2:
            skip = 0
            continue
        if previous_frame is not None:
            diff = numpy.mean(previous_frame != frame)
            if diff < 0.91:
                continue
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_lst.append(frame_rgb)
        previous_frame = frame
        if len(image_lst) > 60:
            break
    cap.release()
    imageio.mimsave(out_path, image_lst)
    optimize(out_path)


async def convert_video_to_gif(input_file: FsNode, nc: NextcloudApp) -> None:
    save_path = path.splitext(input_file.user_path)[0] + ".gif"
    await nc.log(LogLvl.WARNING, f"Processing:{input_file.user_path} -> {save_path}")
    try:
        with tempfile.NamedTemporaryFile(mode="w+b") as tmp_in:
            await nc.files.download2stream(input_file, tmp_in)
            await nc.log(LogLvl.WARNING, "File downloaded")
            tmp_in.flush()
            with tempfile.NamedTemporaryFile(mode="w+b", suffix=".gif") as tmp_out:
                await asyncio.to_thread(_build_gif, tmp_in.name, tmp_out.name)
                await nc.log(LogLvl.WARNING, "GIF is ready")
                await nc.files.upload_stream(save_path, tmp_out)
                await nc.log(LogLvl.WARNING, "Result uploaded")
                await nc.notifications.create(f"{input_file.name} finished!", f"{save_path} is waiting for you!")
    except Exception as e:  # noqa: BLE001
        await nc.log(LogLvl.ERROR, str(e))
        await nc.notifications.create("Error occurred", "Error information was written to log file")


@APP.post("/video_to_gif")
async def video_to_gif(
    files: ActionFileInfoEx,
    nc: Annotated[NextcloudApp, Depends(nc_app)],
    background_tasks: BackgroundTasks,
):
    for one_file in files.files:
        background_tasks.add_task(convert_video_to_gif, one_file.to_fs_node(), nc)
    return responses.Response()


async def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    try:
        if enabled:
            await nc.ui.files_dropdown_menu.register_ex(
                "to_gif",
                "To GIF",
                "/video_to_gif",
                mime="video",
                icon="img/icon.svg",
            )
    except Exception as e:  # noqa: BLE001
        return str(e)
    return ""


if __name__ == "__main__":
    run_app(
        "main:APP",
        log_level="trace",
    )
