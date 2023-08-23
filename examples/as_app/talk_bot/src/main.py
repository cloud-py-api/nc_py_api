"""Example of an application that uses Talk Bot APIs."""

from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI

# from nltk import FreqDist
from requests import Response

from nc_py_api import NextcloudApp, talk_bot
from nc_py_api.ex_app import run_app, set_handlers, talk_bot_app

APP = FastAPI()
FREQ_BOT = talk_bot.TalkBot("/frequency_talk_conversation", "Frequency Count", "Calculates the frequency of words.")


def conversation_frequency_add_data(message: talk_bot.TalkBotMessage):
    try:
        print(message.object_content)
        # FREQ_BOT.react_to_message(message, "😢")
        # FREQ_BOT.react_to_message(message.object_id, "😭", token=message.target_id)
        # FREQ_BOT.react_to_message(message, "😢")
        # FREQ_BOT.react_to_message(message, "😢")
        FREQ_BOT.send_message("dont be so mad", message)
    except Exception as e:
        print(str(e))


@APP.post("/frequency_talk_conversation")
async def frequency_talk_conversation(
    message: Annotated[talk_bot.TalkBotMessage, Depends(talk_bot_app)],
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(conversation_frequency_add_data, message)
    return Response()


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    try:
        FREQ_BOT.enabled_handler(enabled, nc)
    except Exception as e:
        return str(e)
    return ""


@APP.on_event("startup")
def initialization():
    set_handlers(APP, enabled_handler)


if __name__ == "__main__":
    run_app(
        "main:APP",
        log_level="trace",
    )
