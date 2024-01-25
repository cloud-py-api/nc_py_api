"""Nextcloud Talk API for bots."""

import dataclasses
import hashlib
import hmac
import json
import os
import typing

import httpx

from . import options
from ._misc import random_string
from ._session import BasicConfig
from .nextcloud import AsyncNextcloudApp, NextcloudApp


class ObjectContent(typing.TypedDict):
    """Object content of :py:class:`~nc_py_api.talk_bot.TalkBotMessage`."""

    message: str
    parameters: dict


@dataclasses.dataclass
class TalkBotMessage:
    """Talk message received by bots."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def actor_id(self) -> str:
        """One of the attendee types followed by the ``/`` character and a unique identifier within the given type.

        For the users it is the Nextcloud user ID, for guests a **sha1** value.
        """
        return self._raw_data["actor"]["id"]

    @property
    def actor_display_name(self) -> str:
        """The display name of the attendee sending the message."""
        return self._raw_data["actor"]["name"]

    @property
    def object_id(self) -> int:
        """The message ID of the given message on the origin server.

        It can be used to react or reply to the given message.
        """
        return self._raw_data["object"]["id"]

    @property
    def object_name(self) -> str:
        """For normal written messages ``message``, otherwise one of the known ``system message identifiers``."""
        return self._raw_data["object"]["name"]

    @property
    def object_content(self) -> ObjectContent:
        """Dictionary with a ``message`` and ``parameters`` keys."""
        return json.loads(self._raw_data["object"]["content"])

    @property
    def object_media_type(self) -> str:
        """``text/markdown`` when the message should be interpreted as **Markdown**, otherwise ``text/plain``."""
        return self._raw_data["object"]["mediaType"]

    @property
    def conversation_token(self) -> str:
        """The token of the conversation in which the message was posted.

        It can be used to react or reply to the given message.
        """
        return self._raw_data["target"]["id"]

    @property
    def conversation_name(self) -> str:
        """The name of the conversation in which the message was posted."""
        return self._raw_data["target"]["name"]

    def __repr__(self):
        return f"<{self.__class__.__name__} conversation={self.conversation_name}, actor={self.actor_display_name}>"


class TalkBot:
    """A class that implements the TalkBot functionality."""

    _ep_base: str = "/ocs/v2.php/apps/spreed/api/v1/bot"

    def __init__(self, callback_url: str, display_name: str, description: str = ""):
        """Class implementing Nextcloud Talk Bot functionality.

        :param callback_url: FastAPI endpoint which will be assigned to bot.
        :param display_name: The display name of the bot that is shown as author when it posts a message or reaction.
        :param description: Description of the bot helping moderators to decide if they want to enable this bot.
        """
        self.callback_url = callback_url.lstrip("/")
        self.display_name = display_name
        self.description = description

    def enabled_handler(self, enabled: bool, nc: NextcloudApp) -> None:
        """Handles the app ``on``/``off`` event in the context of the bot.

        :param enabled: Value that was passed to ``/enabled`` handler.
        :param nc: **NextcloudApp** class that was passed ``/enabled`` handler.
        """
        if enabled:
            bot_id, bot_secret = nc.register_talk_bot(self.callback_url, self.display_name, self.description)
            os.environ[bot_id] = bot_secret
        else:
            nc.unregister_talk_bot(self.callback_url)

    def send_message(
        self, message: str, reply_to_message: int | TalkBotMessage, silent: bool = False, token: str = ""
    ) -> tuple[httpx.Response, str]:
        """Send a message and returns a "reference string" to identify the message again in a "get messages" request.

        :param message: The message to say.
        :param reply_to_message: The message ID this message is a reply to.

            .. note:: Only allowed when the message type is not ``system`` or ``command``.
        :param silent: Flag controlling if the message should create a chat notifications for the users.
        :param token: Token of the conversation.
            Can be empty if ``reply_to_message`` is :py:class:`~nc_py_api.talk_bot.TalkBotMessage`.
        :returns: Tuple, where fist element is :py:class:`httpx.Response` and second is a "reference string".
        :raises ValueError: in case of an invalid usage.
        :raises RuntimeError: in case of a broken installation.
        """
        if not token and not isinstance(reply_to_message, TalkBotMessage):
            raise ValueError("Either specify 'token' value or provide 'TalkBotMessage'.")
        token = reply_to_message.conversation_token if isinstance(reply_to_message, TalkBotMessage) else token
        reference_id = hashlib.sha256(random_string(32).encode("UTF-8")).hexdigest()
        params = {
            "message": message,
            "replyTo": reply_to_message.object_id if isinstance(reply_to_message, TalkBotMessage) else reply_to_message,
            "referenceId": reference_id,
            "silent": silent,
        }
        return self._sign_send_request("POST", f"/{token}/message", params, message), reference_id

    def react_to_message(self, message: int | TalkBotMessage, reaction: str, token: str = "") -> httpx.Response:
        """React to a message.

        :param message: Message ID or :py:class:`~nc_py_api.talk_bot.TalkBotMessage` to react to.
        :param reaction: A single emoji.
        :param token: Token of the conversation.
            Can be empty if ``message`` is :py:class:`~nc_py_api.talk_bot.TalkBotMessage`.
        :raises ValueError: in case of an invalid usage.
        :raises RuntimeError: in case of a broken installation.
        """
        if not token and not isinstance(message, TalkBotMessage):
            raise ValueError("Either specify 'token' value or provide 'TalkBotMessage'.")
        message_id = message.object_id if isinstance(message, TalkBotMessage) else message
        token = message.conversation_token if isinstance(message, TalkBotMessage) else token
        params = {
            "reaction": reaction,
        }
        return self._sign_send_request("POST", f"/{token}/reaction/{message_id}", params, reaction)

    def delete_reaction(self, message: int | TalkBotMessage, reaction: str, token: str = "") -> httpx.Response:
        """Removes reaction from a message.

        :param message: Message ID or :py:class:`~nc_py_api.talk_bot.TalkBotMessage` to remove reaction from.
        :param reaction: A single emoji.
        :param token: Token of the conversation.
            Can be empty if ``message`` is :py:class:`~nc_py_api.talk_bot.TalkBotMessage`.
        :raises ValueError: in case of an invalid usage.
        :raises RuntimeError: in case of a broken installation.
        """
        if not token and not isinstance(message, TalkBotMessage):
            raise ValueError("Either specify 'token' value or provide 'TalkBotMessage'.")
        message_id = message.object_id if isinstance(message, TalkBotMessage) else message
        token = message.conversation_token if isinstance(message, TalkBotMessage) else token
        params = {
            "reaction": reaction,
        }
        return self._sign_send_request("DELETE", f"/{token}/reaction/{message_id}", params, reaction)

    def _sign_send_request(self, method: str, url_suffix: str, data: dict, data_to_sign: str) -> httpx.Response:
        secret = get_bot_secret(self.callback_url)
        if secret is None:
            raise RuntimeError("Can't find the 'secret' of the bot. Has the bot been installed?")
        talk_bot_random = random_string(32)
        hmac_sign = hmac.new(secret, talk_bot_random.encode("UTF-8"), digestmod=hashlib.sha256)
        hmac_sign.update(data_to_sign.encode("UTF-8"))
        nc_app_cfg = BasicConfig()
        with httpx.Client(verify=nc_app_cfg.options.nc_cert) as client:
            return client.request(
                method,
                url=nc_app_cfg.endpoint + "/ocs/v2.php/apps/spreed/api/v1/bot" + url_suffix,
                json=data,
                headers={
                    "X-Nextcloud-Talk-Bot-Random": talk_bot_random,
                    "X-Nextcloud-Talk-Bot-Signature": hmac_sign.hexdigest(),
                    "OCS-APIRequest": "true",
                },
                cookies={"XDEBUG_SESSION": options.XDEBUG_SESSION} if options.XDEBUG_SESSION else {},
                timeout=nc_app_cfg.options.timeout,
            )


class AsyncTalkBot:
    """A class that implements the async TalkBot functionality."""

    _ep_base: str = "/ocs/v2.php/apps/spreed/api/v1/bot"

    def __init__(self, callback_url: str, display_name: str, description: str = ""):
        """Class implementing Nextcloud Talk Bot functionality.

        :param callback_url: FastAPI endpoint which will be assigned to bot.
        :param display_name: The display name of the bot that is shown as author when it posts a message or reaction.
        :param description: Description of the bot helping moderators to decide if they want to enable this bot.
        """
        self.callback_url = callback_url.lstrip("/")
        self.display_name = display_name
        self.description = description

    async def enabled_handler(self, enabled: bool, nc: AsyncNextcloudApp) -> None:
        """Handles the app ``on``/``off`` event in the context of the bot.

        :param enabled: Value that was passed to ``/enabled`` handler.
        :param nc: **NextcloudApp** class that was passed ``/enabled`` handler.
        """
        if enabled:
            bot_id, bot_secret = await nc.register_talk_bot(self.callback_url, self.display_name, self.description)
            os.environ[bot_id] = bot_secret
        else:
            await nc.unregister_talk_bot(self.callback_url)

    async def send_message(
        self, message: str, reply_to_message: int | TalkBotMessage, silent: bool = False, token: str = ""
    ) -> tuple[httpx.Response, str]:
        """Send a message and returns a "reference string" to identify the message again in a "get messages" request.

        :param message: The message to say.
        :param reply_to_message: The message ID this message is a reply to.

            .. note:: Only allowed when the message type is not ``system`` or ``command``.
        :param silent: Flag controlling if the message should create a chat notifications for the users.
        :param token: Token of the conversation.
            Can be empty if ``reply_to_message`` is :py:class:`~nc_py_api.talk_bot.TalkBotMessage`.
        :returns: Tuple, where fist element is :py:class:`httpx.Response` and second is a "reference string".
        :raises ValueError: in case of an invalid usage.
        :raises RuntimeError: in case of a broken installation.
        """
        if not token and not isinstance(reply_to_message, TalkBotMessage):
            raise ValueError("Either specify 'token' value or provide 'TalkBotMessage'.")
        token = reply_to_message.conversation_token if isinstance(reply_to_message, TalkBotMessage) else token
        reference_id = hashlib.sha256(random_string(32).encode("UTF-8")).hexdigest()
        params = {
            "message": message,
            "replyTo": reply_to_message.object_id if isinstance(reply_to_message, TalkBotMessage) else reply_to_message,
            "referenceId": reference_id,
            "silent": silent,
        }
        return await self._sign_send_request("POST", f"/{token}/message", params, message), reference_id

    async def react_to_message(self, message: int | TalkBotMessage, reaction: str, token: str = "") -> httpx.Response:
        """React to a message.

        :param message: Message ID or :py:class:`~nc_py_api.talk_bot.TalkBotMessage` to react to.
        :param reaction: A single emoji.
        :param token: Token of the conversation.
            Can be empty if ``message`` is :py:class:`~nc_py_api.talk_bot.TalkBotMessage`.
        :raises ValueError: in case of an invalid usage.
        :raises RuntimeError: in case of a broken installation.
        """
        if not token and not isinstance(message, TalkBotMessage):
            raise ValueError("Either specify 'token' value or provide 'TalkBotMessage'.")
        message_id = message.object_id if isinstance(message, TalkBotMessage) else message
        token = message.conversation_token if isinstance(message, TalkBotMessage) else token
        params = {
            "reaction": reaction,
        }
        return await self._sign_send_request("POST", f"/{token}/reaction/{message_id}", params, reaction)

    async def delete_reaction(self, message: int | TalkBotMessage, reaction: str, token: str = "") -> httpx.Response:
        """Removes reaction from a message.

        :param message: Message ID or :py:class:`~nc_py_api.talk_bot.TalkBotMessage` to remove reaction from.
        :param reaction: A single emoji.
        :param token: Token of the conversation.
            Can be empty if ``message`` is :py:class:`~nc_py_api.talk_bot.TalkBotMessage`.
        :raises ValueError: in case of an invalid usage.
        :raises RuntimeError: in case of a broken installation.
        """
        if not token and not isinstance(message, TalkBotMessage):
            raise ValueError("Either specify 'token' value or provide 'TalkBotMessage'.")
        message_id = message.object_id if isinstance(message, TalkBotMessage) else message
        token = message.conversation_token if isinstance(message, TalkBotMessage) else token
        params = {
            "reaction": reaction,
        }
        return await self._sign_send_request("DELETE", f"/{token}/reaction/{message_id}", params, reaction)

    async def _sign_send_request(self, method: str, url_suffix: str, data: dict, data_to_sign: str) -> httpx.Response:
        secret = await aget_bot_secret(self.callback_url)
        if secret is None:
            raise RuntimeError("Can't find the 'secret' of the bot. Has the bot been installed?")
        talk_bot_random = random_string(32)
        hmac_sign = hmac.new(secret, talk_bot_random.encode("UTF-8"), digestmod=hashlib.sha256)
        hmac_sign.update(data_to_sign.encode("UTF-8"))
        nc_app_cfg = BasicConfig()
        async with httpx.AsyncClient(verify=nc_app_cfg.options.nc_cert) as aclient:
            return await aclient.request(
                method,
                url=nc_app_cfg.endpoint + "/ocs/v2.php/apps/spreed/api/v1/bot" + url_suffix,
                json=data,
                headers={
                    "X-Nextcloud-Talk-Bot-Random": talk_bot_random,
                    "X-Nextcloud-Talk-Bot-Signature": hmac_sign.hexdigest(),
                    "OCS-APIRequest": "true",
                },
                cookies={"XDEBUG_SESSION": options.XDEBUG_SESSION} if options.XDEBUG_SESSION else {},
                timeout=nc_app_cfg.options.timeout,
            )


def __get_bot_secret(callback_url: str) -> str:
    sha_1 = hashlib.sha1(usedforsecurity=False)
    string_to_hash = os.environ["APP_ID"] + "_" + callback_url.lstrip("/")
    sha_1.update(string_to_hash.encode("UTF-8"))
    return sha_1.hexdigest()


def get_bot_secret(callback_url: str) -> bytes | None:
    """Returns the bot's secret from an environment variable or from the application's configuration on the server."""
    secret_key = __get_bot_secret(callback_url)
    if secret_key in os.environ:
        return os.environ[secret_key].encode("UTF-8")
    secret_value = NextcloudApp().appconfig_ex.get_value(secret_key)
    if secret_value is not None:
        os.environ[secret_key] = secret_value
        return secret_value.encode("UTF-8")
    return None


async def aget_bot_secret(callback_url: str) -> bytes | None:
    """Returns the bot's secret from an environment variable or from the application's configuration on the server."""
    secret_key = __get_bot_secret(callback_url)
    if secret_key in os.environ:
        return os.environ[secret_key].encode("UTF-8")
    secret_value = await AsyncNextcloudApp().appconfig_ex.get_value(secret_key)
    if secret_value is not None:
        os.environ[secret_key] = secret_value
        return secret_value.encode("UTF-8")
    return None
