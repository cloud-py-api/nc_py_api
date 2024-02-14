"""Example of an application that uses Python Transformers library with Talk Bot APIs."""

import re
from contextlib import asynccontextmanager
from typing import Annotated

import requests
from fastapi import BackgroundTasks, Depends, FastAPI
from transformers import pipeline

from nc_py_api import NextcloudApp, talk_bot
from nc_py_api.ex_app import (
    AppAPIAuthMiddleware,
    atalk_bot_msg,
    get_model_path,
    run_app,
    set_handlers,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    set_handlers(APP, enabled_handler, models_to_fetch={MODEL_NAME: {}})
    yield


APP = FastAPI(lifespan=lifespan)
APP.add_middleware(AppAPIAuthMiddleware)
AI_BOT = talk_bot.TalkBot("/ai_talk_bot", "AI talk bot", "Usage: `@assistant What sounds do cats make?`")
MODEL_NAME = "MBZUAI/LaMini-Flan-T5-783M"


def ai_talk_bot_process_request(message: talk_bot.TalkBotMessage):
    r = re.search(r"@assistant\s(.*)", message.object_content["message"], re.IGNORECASE)
    if r is None:
        return
    model = pipeline("text2text-generation", model=get_model_path(MODEL_NAME))
    response_text = model(r.group(1), max_length=64, do_sample=True)[0]["generated_text"]
    AI_BOT.send_message(response_text, message)


@APP.post("/ai_talk_bot")
async def ai_talk_bot(
    message: Annotated[talk_bot.TalkBotMessage, Depends(atalk_bot_msg)],
    background_tasks: BackgroundTasks,
):
    if message.object_name == "message":
        background_tasks.add_task(ai_talk_bot_process_request, message)
    return requests.Response()


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    try:
        AI_BOT.enabled_handler(enabled, nc)
    except Exception as e:
        return str(e)
    return ""


if __name__ == "__main__":
    run_app("main:APP", log_level="trace")
