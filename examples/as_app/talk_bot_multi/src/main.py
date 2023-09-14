"""An example of two bots in one application.

Of course, everything can be done with one bot, and in most cases, this is more correct,
but this is just an example that the system is unlimited and an application can have more than one bot."""

import re
from typing import Annotated

import requests
from fastapi import Depends, FastAPI

from nc_py_api import NextcloudApp, talk_bot
from nc_py_api.ex_app import run_app, set_handlers, talk_bot_app

APP = FastAPI()
BOT1 = talk_bot.TalkBot("/bot1", "Test bot number One", "Usage: `@bot one | @bots`")
BOT2 = talk_bot.TalkBot("/bot2", "Test bot number Two", "Usage: `@bot two | @bots`")


@APP.post("/bot1")
async def bot1(message: Annotated[talk_bot.TalkBotMessage, Depends(talk_bot_app)]):
    if message.object_name != "message":
        return
    r = re.search(r"@bot\sone.*", message.object_content["message"], re.IGNORECASE)
    if r is None and re.search(r"@bots!", message.object_content["message"], re.IGNORECASE) is None:
        return
    BOT1.send_message("I am here, my Lord!", message)
    return requests.Response()


@APP.post("/bot2")
async def bot2(message: Annotated[talk_bot.TalkBotMessage, Depends(talk_bot_app)]):
    if message.object_name != "message":
        return
    r = re.search(r"@bot\stwo.*", message.object_content["message"], re.IGNORECASE)
    if r is None and re.search(r"@bots!", message.object_content["message"], re.IGNORECASE) is None:
        return
    BOT2.send_message("I am here, my Lord!", message)
    return requests.Response()


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    try:
        if enabled:
            """This is necessary because this example is used in the `AppAPI` tests to check the correctness of
            removing bots from the AppAPI database itself, if the bots are already turned off and cannot call
            **unregister_talk_bot** themselves."""
            BOT1.enabled_handler(enabled, nc)
            BOT2.enabled_handler(enabled, nc)
    except Exception as e:
        return str(e)
    return ""


@APP.on_event("startup")
def initialization():
    set_handlers(APP, enabled_handler)


if __name__ == "__main__":
    run_app("main:APP", log_level="trace")
