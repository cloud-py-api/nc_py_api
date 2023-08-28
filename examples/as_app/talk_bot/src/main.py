"""Example of an application(currency convertor) that uses Talk Bot APIs."""

import re
from typing import Annotated

import requests
from fastapi import BackgroundTasks, Depends, FastAPI

from nc_py_api import NextcloudApp, talk_bot
from nc_py_api.ex_app import run_app, set_handlers, talk_bot_app

APP = FastAPI()
# We define bot globally, so if no `multiprocessing` module is used, it can be reused by calls.
# All stuff in it works only with local variables, so in the case of multithreading, there should not be problems.
CURRENCY_BOT = talk_bot.TalkBot("/currency_talk_bot", "Currency convertor", "Usage: `@currency convert 100 EUR to USD`")


def convert_currency(amount, from_currency, to_currency):
    """Payload of bot, simplest currency convertor."""
    base_url = "https://api.exchangerate-api.com/v4/latest/"

    # Fetch latest exchange rates
    response = requests.get(base_url + from_currency)
    data = response.json()

    if "rates" in data:
        rates = data["rates"]
        if from_currency == to_currency:
            return amount

        if from_currency in rates and to_currency in rates:
            conversion_rate = rates[to_currency] / rates[from_currency]
            converted_amount = amount * conversion_rate
            return converted_amount
        else:
            raise ValueError("Invalid currency!")
    else:
        raise ValueError("Unable to fetch exchange rates!")


def currency_talk_bot_process_request(message: talk_bot.TalkBotMessage):
    try:
        # Ignore `system` messages
        if message.object_name != "message":
            return
        # We use a wildcard search to only respond to messages sent to us.
        r = re.search(
            r"@currency\s(convert\s)?(\d*)\s(\w*)\sto\s(\w*)\s?", message.object_content["message"], re.IGNORECASE
        )
        if r is None:
            return
        converted_amount = convert_currency(int(r.group(2)), r.group(3), r.group(4))
        converted_amount = round(converted_amount, 2)
        # Send reply to chat
        CURRENCY_BOT.send_message(f"{r.group(2)} {r.group(3)} is equal to {converted_amount} {r.group(4)}", message)
    except Exception as e:
        # In production, it is better to write to log, than in the chat ;)
        CURRENCY_BOT.send_message(f"Exception: {str(e)}", message)


@APP.post("/currency_talk_bot")
async def currency_talk_bot(
    message: Annotated[talk_bot.TalkBotMessage, Depends(talk_bot_app)],
    background_tasks: BackgroundTasks,
):
    # As during converting, we do not process converting locally, we perform this in background, in the background task.
    background_tasks.add_task(currency_talk_bot_process_request, message)
    # Return Response immediately for Nextcloud, that we are ok.
    return requests.Response()


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    try:
        # `enabled_handler` will install or uninstall bot on the server, depending on ``enabled`` parameter.
        CURRENCY_BOT.enabled_handler(enabled, nc)
    except Exception as e:
        return str(e)
    return ""


# The same stuff as for usual External Applications
@APP.on_event("startup")
def initialization():
    set_handlers(APP, enabled_handler)


if __name__ == "__main__":
    run_app("main:APP", log_level="trace")
