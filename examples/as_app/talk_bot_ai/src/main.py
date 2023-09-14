"""Example of an application that uses Python Transformers library with Talk Bot APIs."""

# This line should be on top before any import of the "Transformers" library.
from nc_py_api.ex_app import persist_transformers_cache  # noqa # isort:skip
import re
from threading import Thread
from typing import Annotated

import requests
from fastapi import BackgroundTasks, Depends, FastAPI
from transformers import pipeline

from nc_py_api import NextcloudApp, talk_bot
from nc_py_api.ex_app import run_app, set_handlers, talk_bot_app

APP = FastAPI()
AI_BOT = talk_bot.TalkBot("/ai_talk_bot", "AI talk bot", "Usage: `@ai What sounds do cats make?`")
MODEL_NAME = "MBZUAI/LaMini-Flan-T5-77M"
MODEL_INIT_THREAD = None


def ai_talk_bot_process_request(message: talk_bot.TalkBotMessage):
    r = re.search(r"@ai\s(.*)", message.object_content["message"], re.IGNORECASE)
    if r is None:
        return
    model = pipeline("text2text-generation", model=MODEL_NAME)
    response_text = model(r.group(1), max_length=64, do_sample=True)[0]["generated_text"]
    AI_BOT.send_message(response_text, message)


@APP.post("/ai_talk_bot")
async def ai_talk_bot(
    message: Annotated[talk_bot.TalkBotMessage, Depends(talk_bot_app)],
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


def download_models():
    pipeline("text2text-generation", model=MODEL_NAME)


def heartbeat_handler() -> str:
    global MODEL_INIT_THREAD
    print("heartbeat_handler: called")
    if MODEL_INIT_THREAD is None:
        MODEL_INIT_THREAD = Thread(target=download_models)
        MODEL_INIT_THREAD.start()
        print("heartbeat_handler: started initialization thread")
    r = "init" if MODEL_INIT_THREAD.is_alive() else "ok"
    print(f"heartbeat_handler: result={r}")
    return r


@APP.on_event("startup")
def initialization():
    set_handlers(APP, enabled_handler, heartbeat_handler)


if __name__ == "__main__":
    run_app("main:APP", log_level="trace")
