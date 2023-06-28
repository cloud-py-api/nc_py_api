"""
Simplest example.
"""

from os import path, environ
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Depends
from requests import Response
import urllib3

import tempfile
from pygifsicle import optimize
import imageio
import cv2
import numpy

from nc_py_api import UiFileActionHandlerInfo, LogLvl, NextcloudApp, nc_app, set_enabled_handler, ApiScope, set_scopes

APP = FastAPI()


@APP.post("/video_to_gif")
async def video_to_gif(
        file: UiFileActionHandlerInfo,
        nc: Annotated[NextcloudApp, Depends(nc_app)],
):
    source_path = path.join(file.actionFile.dir, file.actionFile.name)
    save_path = path.splitext(source_path)[0] + ".gif"
    nc.log(LogLvl.WARNING, f"Processing:{source_path} -> {save_path}")
    source_file = nc.files.download(source_path)
    nc.log(LogLvl.WARNING, f"File downloaded")
    try:
        with tempfile.NamedTemporaryFile(mode="w+b") as tmp_in:
            tmp_in.write(source_file)
            tmp_in.flush()
            cap = cv2.VideoCapture(tmp_in.name)
            with tempfile.NamedTemporaryFile(mode="w+b", suffix=".gif") as tmp_out:
                image_lst = []
                previous_frame = None
                while True:
                    ret, frame = cap.read()
                    if previous_frame is not None:
                        diff = numpy.mean(previous_frame != frame)
                        if diff < 0.91:
                            continue
                    if frame is None:
                        break
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image_lst.append(frame_rgb)
                    previous_frame = frame
                cap.release()
                imageio.mimsave(tmp_out.name, image_lst)
                optimize(tmp_out.name)
                nc.log(LogLvl.WARNING, f"GIF is ready")
                nc.files.upload(save_path, content=tmp_out.read())
                nc.log(LogLvl.WARNING, f"Result uploaded")
    except Exception as e:
        nc.log(LogLvl.ERROR, str(e))
    return Response()


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    try:
        if enabled:
            nc.ui_files_actions.register("to_gif", "TO GIF", "/video_to_gif", mime="video")
        else:
            nc.ui_files_actions.unregister("to_gif")
    except Exception as e:
        return str(e)
    return ""


@APP.on_event("startup")
def initialization():
    set_enabled_handler(APP, enabled_handler)
    set_scopes(APP, {
        "required": [ApiScope.DAV],
        "optional": [ApiScope.NOTIFICATIONS]
    })


if __name__ == "__main__":
    # This should be set by packaging step
    secret = "tC6vkwPhcppjMykD1r0n9NlI95uJMBYjs5blpIcA1PAdoPDmc5qoAjaBAkyocZ6E" \
             "X1T8Pi+T5papEolTLxz3fJSPS8ffC4204YmggxPsbJdCkXHWNPHKWS9B+vTj2SIV"
    if "app_name" not in environ:
        environ["app_name"] = "nc_py_api"
    if "app_version" not in environ:
        environ["app_version"] = "1.0.0"
    if "app_secret" not in environ:
        environ["app_secret"] = secret
    if "nextcloud_url" not in environ:
        environ["nextcloud_url"] = "http://nextcloud.local/index.php"
    # environ["app_name"] = "test_app"
    # ---------
    urllib3.disable_warnings()
    uvicorn.run("main:APP", host="0.0.0.0", port=9001, log_level='trace', reload=True)
