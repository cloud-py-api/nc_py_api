from typing import Annotated

import requests
from fastapi import BackgroundTasks, Depends, FastAPI

from nc_py_api import NextcloudApp, talk_bot
from nc_py_api.ex_app import run_app, set_handlers, talk_bot_app

APP = FastAPI()
COVERAGE_BOT = talk_bot.TalkBot("/talk_bot_coverage", "Coverage bot", "Desc")


def coverage_talk_bot_process_request(message: talk_bot.TalkBotMessage):
    _ = message


@APP.post("/talk_bot_coverage")
async def currency_talk_bot(
    message: Annotated[talk_bot.TalkBotMessage, Depends(talk_bot_app)],
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(coverage_talk_bot_process_request, message)
    return requests.Response()


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    COVERAGE_BOT.enabled_handler(enabled, nc)
    return ""


@APP.on_event("startup")
def initialization():
    set_handlers(APP, enabled_handler)


if __name__ == "__main__":
    run_app("main:APP", log_level="trace")
