"""Simplest example of files_dropdown_menu + notification."""

import tempfile
from os import environ, path
from typing import Annotated

import cv2
import imageio
import numpy
import urllib3
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI
from pygifsicle import optimize
from requests import Response

from nc_py_api import NextcloudApp
from nc_py_api.ex_app import (
    ApiScope,
    LogLvl,
    UiActionFileInfo,
    UiFileActionHandlerInfo,
    enable_heartbeat,
    nc_app,
    set_enabled_handler,
    set_scopes,
)

APP = FastAPI()


def convert_video_to_gif(input_params: UiActionFileInfo, nc: NextcloudApp):
    source_path = path.join(input_params.directory, input_params.name)
    save_path = path.splitext(source_path)[0] + ".gif"
    nc.log(LogLvl.WARNING, f"Processing:{source_path} -> {save_path}")
    try:
        with tempfile.NamedTemporaryFile(mode="w+b") as tmp_in:
            nc.files.download2stream(source_path, tmp_in)
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
                nc.users.notifications.create(f"{input_params.name} finished!", f"{save_path} is waiting for you!")
    except Exception as e:
        nc.log(LogLvl.ERROR, str(e))
        nc.users.notifications.create("Error occurred", "Error information was written to log file")


@APP.post("/video_to_gif")
async def video_to_gif(
    file: UiFileActionHandlerInfo,
    nc: Annotated[NextcloudApp, Depends(nc_app)],
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(convert_video_to_gif, file.actionFile, nc)
    return Response()


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    try:
        if enabled:
            nc.ui.files_dropdown_menu.register("to_gif", "TO GIF", "/video_to_gif", mime="video")
        else:
            nc.ui.files_dropdown_menu.unregister("to_gif")
    except Exception as e:
        return str(e)
    return ""


@APP.on_event("startup")
def initialization():
    set_enabled_handler(APP, enabled_handler)
    set_scopes(APP, {"required": [ApiScope.DAV], "optional": [ApiScope.NOTIFICATIONS]})
    enable_heartbeat(APP)


if __name__ == "__main__":
    urllib3.disable_warnings()
    uvicorn.run("main:APP", host=environ.get("APP_HOST", "127.0.0.1"), port=int(environ["APP_PORT"]), log_level="trace")
