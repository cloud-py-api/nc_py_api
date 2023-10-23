"""Example of an application that uses Python Transformers library with Talk Bot APIs."""
import re
from contextlib import asynccontextmanager
from typing import Annotated

import requests
from fastapi import BackgroundTasks, Depends, FastAPI
from huggingface_hub import snapshot_download
from transformers import pipeline

from nc_py_api import NextcloudApp, talk_bot
from nc_py_api.ex_app import persistent_storage, run_app, set_handlers, talk_bot_app


@asynccontextmanager
async def lifespan(_app: FastAPI):
    set_handlers(APP, enabled_handler, models_to_fetch=[MODEL_NAME])
    yield


APP = FastAPI(lifespan=lifespan)
AI_BOT = talk_bot.TalkBot("/ai_talk_bot", "AI talk bot", "Usage: `@assistant What sounds do cats make?`")
MODEL_NAME = "MBZUAI/LaMini-Flan-T5-783M"


def ai_talk_bot_process_request(message: talk_bot.TalkBotMessage):
    r = re.search(r"@assistant\s(.*)", message.object_content["message"], re.IGNORECASE)
    if r is None:
        return
    model = pipeline(
        "text2text-generation",
        model=snapshot_download(MODEL_NAME, local_files_only=True, cache_dir=persistent_storage()),
    )
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


if __name__ == "__main__":
    run_app("main:APP", log_level="trace")
