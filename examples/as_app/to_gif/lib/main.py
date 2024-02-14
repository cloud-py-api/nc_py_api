"""Simplest example of files_dropdown_menu + notification."""

import tempfile
from contextlib import asynccontextmanager
from os import path

import cv2
import imageio
import numpy
from fastapi import BackgroundTasks, FastAPI
from pygifsicle import optimize
from requests import Response

from nc_py_api import FsNode, NextcloudApp
from nc_py_api.ex_app import (
    AppAPIAuthMiddleware,
    LogLvl,
    UiActionFileInfo,
    run_app,
    set_handlers,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    set_handlers(app, enabled_handler)
    yield


APP = FastAPI(lifespan=lifespan)
APP.add_middleware(AppAPIAuthMiddleware)


def convert_video_to_gif(input_file: FsNode):
    nc = NextcloudApp()
    save_path = path.splitext(input_file.user_path)[0] + ".gif"
    nc.log(LogLvl.WARNING, f"Processing:{input_file.user_path} -> {save_path}")
    try:
        with tempfile.NamedTemporaryFile(mode="w+b") as tmp_in:
            nc.files.download2stream(input_file, tmp_in)
            nc.log(LogLvl.WARNING, "File downloaded")
            tmp_in.flush()
            cap = cv2.VideoCapture(tmp_in.name)
            with tempfile.NamedTemporaryFile(mode="w+b", suffix=".gif") as tmp_out:
                image_lst = []
                previous_frame = None
                skip = 0
                while True:
                    skip += 1
                    ret, frame = cap.read()
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
                imageio.mimsave(tmp_out.name, image_lst)
                optimize(tmp_out.name)
                nc.log(LogLvl.WARNING, "GIF is ready")
                nc.files.upload_stream(save_path, tmp_out)
                nc.log(LogLvl.WARNING, "Result uploaded")
                nc.notifications.create(f"{input_file.name} finished!", f"{save_path} is waiting for you!")
    except Exception as e:
        nc.log(LogLvl.ERROR, str(e))
        nc.notifications.create("Error occurred", "Error information was written to log file")


@APP.post("/video_to_gif")
async def video_to_gif(
    file: UiActionFileInfo,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(convert_video_to_gif, file.to_fs_node())
    return Response()


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    try:
        if enabled:
            nc.ui.files_dropdown_menu.register(
                "to_gif",
                "TO GIF",
                "/video_to_gif",
                mime="video",
                icon="img/icon.svg",
            )
    except Exception as e:
        return str(e)
    return ""


if __name__ == "__main__":
    run_app(
        "main:APP",
        log_level="trace",
    )
