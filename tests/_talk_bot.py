import os
from typing import Annotated

import gfixture_set_env  # noqa
import pytest
from fastapi import BackgroundTasks, Depends, FastAPI, Request, Response

from nc_py_api import NextcloudApp, talk_bot
from nc_py_api.ex_app import AppAPIAuthMiddleware, nc_app, run_app, talk_bot_msg

APP = FastAPI()
APP.add_middleware(AppAPIAuthMiddleware, disable_for=["reset_bot_secret"])
COVERAGE_BOT = talk_bot.TalkBot("/talk_bot_coverage", "Coverage bot", "Desc")


def coverage_talk_bot_process_request(message: talk_bot.TalkBotMessage, request: Request):
    if message.object_name != "message":
        return
    COVERAGE_BOT.react_to_message(message, "🥳")
    COVERAGE_BOT.react_to_message(message, "🫡")
    COVERAGE_BOT.delete_reaction(message, "🫡")
    COVERAGE_BOT.send_message("Hello from bot!", message)
    assert isinstance(message.actor_id, str)
    assert isinstance(message.actor_display_name, str)
    assert isinstance(message.object_name, str)
    assert isinstance(message.object_content, dict)
    assert message.object_media_type in ("text/markdown", "text/plain")
    assert isinstance(message.conversation_name, str)
    assert str(message).find("conversation=") != -1
    with pytest.raises(ValueError):
        COVERAGE_BOT.react_to_message(message.object_id, "🥳")
    with pytest.raises(ValueError):
        COVERAGE_BOT.delete_reaction(message.object_id, "🥳")
    with pytest.raises(ValueError):
        COVERAGE_BOT.send_message("🥳", message.object_id)


@APP.post("/talk_bot_coverage")
def talk_bot_coverage(
    request: Request,
    _nc: Annotated[NextcloudApp, Depends(nc_app)],
    message: Annotated[talk_bot.TalkBotMessage, Depends(talk_bot_msg)],
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(coverage_talk_bot_process_request, message, request)
    return Response()


# in real program this is not needed, as bot enabling handler is called in the bots process itself and will reset it.
@APP.delete("/reset_bot_secret")
def reset_bot_secret():
    os.environ.pop(talk_bot.__get_bot_secret("/talk_bot_coverage"), None)
    return Response()


if __name__ == "__main__":
    run_app("_talk_bot:APP", log_level="trace")
