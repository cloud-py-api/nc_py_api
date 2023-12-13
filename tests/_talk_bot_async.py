from typing import Annotated

import gfixture_set_env  # noqa
import pytest
import requests
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from starlette.datastructures import URL

from nc_py_api import talk_bot
from nc_py_api.ex_app import atalk_bot_app, run_app

APP = FastAPI()
COVERAGE_BOT = talk_bot.AsyncTalkBot("/talk_bot_coverage", "Coverage bot", "Desc")


async def coverage_talk_bot_process_request(message: talk_bot.TalkBotMessage, request: Request):
    await COVERAGE_BOT.react_to_message(message, "🥳")
    await COVERAGE_BOT.react_to_message(message, "🫡")
    await COVERAGE_BOT.delete_reaction(message, "🫡")
    await COVERAGE_BOT.send_message("Hello from async bot!", message)
    assert isinstance(message.actor_id, str)
    assert isinstance(message.actor_display_name, str)
    assert isinstance(message.object_name, str)
    assert isinstance(message.object_content, dict)
    assert message.object_media_type in ("text/markdown", "text/plain")
    assert isinstance(message.conversation_name, str)
    with pytest.raises(ValueError):
        await COVERAGE_BOT.react_to_message(message.object_id, "🥳")
    with pytest.raises(ValueError):
        await COVERAGE_BOT.delete_reaction(message.object_id, "🥳")
    with pytest.raises(ValueError):
        await COVERAGE_BOT.send_message("🥳", message.object_id)
    with pytest.raises(HTTPException) as e:
        headers = dict(request.scope["headers"])
        headers[b"x-nextcloud-talk-signature"] = b"122112442412"
        request.scope["headers"] = list(headers.items())
        del request._headers  # noqa
        await atalk_bot_app(request)
    assert e.value.status_code == 401
    with pytest.raises(HTTPException) as e:
        request._url = URL("sample_url")
        await atalk_bot_app(request)
    assert e.value.status_code == 500
    assert str(message).find("conversation=") != -1


@APP.post("/talk_bot_coverage")
async def currency_talk_bot(
    request: Request,
    message: Annotated[talk_bot.TalkBotMessage, Depends(atalk_bot_app)],
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(coverage_talk_bot_process_request, message, request)
    return requests.Response()


if __name__ == "__main__":
    run_app("_talk_bot:APP", log_level="trace")
