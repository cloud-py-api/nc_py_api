from typing import Annotated

import gfixture_set_env  # noqa
import requests
from fastapi import BackgroundTasks, Depends, FastAPI

from nc_py_api import talk_bot
from nc_py_api.ex_app import run_app, talk_bot_app

APP = FastAPI()
COVERAGE_BOT = talk_bot.TalkBot("/talk_bot_coverage", "Coverage bot", "Desc")


def coverage_talk_bot_process_request(message: talk_bot.TalkBotMessage):
    COVERAGE_BOT.react_to_message(message, "🥳")
    COVERAGE_BOT.react_to_message(message, "🫡")
    COVERAGE_BOT.delete_reaction(message, "🫡")
    COVERAGE_BOT.send_message("Hello from bot!", message)


@APP.post("/talk_bot_coverage")
async def currency_talk_bot(
    message: Annotated[talk_bot.TalkBotMessage, Depends(talk_bot_app)],
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(coverage_talk_bot_process_request, message)
    return requests.Response()


if __name__ == "__main__":
    run_app("_talk_bot:APP", log_level="trace")
