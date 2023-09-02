"""Nextcloud Talk API implementation."""

import hashlib
import typing

from ._misc import (
    check_capabilities,
    clear_from_params_empty,
    random_string,
    require_capabilities,
)
from ._session import NcSessionBasic
from .talk import (
    BotInfo,
    BotInfoBasic,
    Conversation,
    ConversationType,
    MessageReactions,
    NotificationLevel,
    TalkMessage,
)


class _TalkAPI:
    """Class that implements work with Nextcloud Talk."""

    _ep_base: str = "/ocs/v2.php/apps/spreed"
    config_sha: str
    """Sha1 value over Talk config. After receiving a different value on subsequent requests, settings got refreshed."""
    modified_since: int
    """Used by ``get_user_conversations``, when **modified_since** param is ``True``."""

    def __init__(self, session: NcSessionBasic):
        self._session = session
        self.config_sha = ""
        self.modified_since = 0

    @property
    def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("spreed", self._session.capabilities)

    @property
    def bots_available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("spreed.features.bots-v1", self._session.capabilities)

    def get_user_conversations(
        self, no_status_update: bool = True, include_status: bool = False, modified_since: typing.Union[int, bool] = 0
    ) -> list[Conversation]:
        """Returns the list of the user's conversations.

        :param no_status_update: When the user status should not be automatically set to the online.
        :param include_status: Whether the user status information of all one-to-one conversations should be loaded.
        :param modified_since: When provided only conversations with a newer **lastActivity**
            (and one-to-one conversations when includeStatus is provided) are returned.
            Can be set to ``True`` to automatically use last ``modified_since`` from previous calls. Default = **0**.

            .. note:: In rare cases, when a request arrives between seconds, it is possible that return data
                will contain part of the conversations from the last call that was not modified(
                their `last_activity` will be the same as ``talk.modified_since``).
        """
        params: dict = {}
        if no_status_update:
            params["noStatusUpdate"] = 1
        if include_status:
            params["includeStatus"] = True
        if modified_since:
            params["modifiedSince"] = self.modified_since if modified_since is True else modified_since

        result = self._session.ocs("GET", self._ep_base + "/api/v4/room", params=params)
        self.modified_since = int(self._session.response_headers["X-Nextcloud-Talk-Modified-Before"])
        self._update_config_sha()
        return [Conversation(i) for i in result]

    def create_conversation(
        self,
        conversation_type: ConversationType,
        invite: str = "",
        source: str = "",
        room_name: str = "",
        object_type: str = "",
        object_id: str = "",
    ) -> Conversation:
        """Creates a new conversation.

        .. note:: Creating a conversation as a child breakout room will automatically set the lobby when breakout
            rooms are not started and will always overwrite the room type with the parent room type.
            Also, moderators of the parent conversation will be automatically added as moderators.

        :param conversation_type: type of the conversation to create.
        :param invite: User ID(roomType=ONE_TO_ONE), Group ID(roomType=GROUP - optional),
            Circle ID(roomType=GROUP, source='circles', only available with the ``circles-support`` capability).
        :param source: The source for the invite, only supported on roomType = GROUP for groups and circles.
        :param room_name: Conversation name up to 255 characters(``not available for roomType=ONE_TO_ONE``).
        :param object_type: Type of object this room references, currently only allowed
            value is **"room"** to indicate the parent of a breakout room.
        :param object_id: ID of an object this room references, room token is used for the parent of a breakout room.
        """
        params: dict = {
            "roomType": int(conversation_type),
            "invite": invite,
            "source": source,
            "roomName": room_name,
            "objectType": object_type,
            "objectId": object_id,
        }
        clear_from_params_empty(["invite", "source", "roomName", "objectType", "objectId"], params)
        return Conversation(self._session.ocs("POST", self._ep_base + "/api/v4/room", json=params))

    def rename_conversation(self, conversation: typing.Union[Conversation, str], new_name: str) -> None:
        """Renames a conversation.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param new_name: new name for the conversation.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("PUT", self._ep_base + f"/api/v4/room/{token}", params={"roomName": new_name})

    def set_conversation_description(self, conversation: typing.Union[Conversation, str], description: str) -> None:
        """Sets conversation description.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param description: description for the conversation.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs(
            "PUT", self._ep_base + f"/api/v4/room/{token}/description", params={"description": description}
        )

    def set_conversation_fav(self, conversation: typing.Union[Conversation, str], favorite: bool) -> None:
        """Changes conversation **favorite** state.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param favorite: value to set for the ``favourite`` state.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("POST" if favorite else "DELETE", self._ep_base + f"/api/v4/room/{token}/favorite")

    def set_conversation_password(self, conversation: typing.Union[Conversation, str], password: str) -> None:
        """Sets password for a conversation.

        Currently, it is only allowed to have a password for ``public`` conversations.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param password: new password for the conversation.

        .. note:: Password should match the password policy.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("PUT", self._ep_base + f"/api/v4/room/{token}/password", {"password": password})

    def set_conversation_readonly(self, conversation: typing.Union[Conversation, str], read_only: bool) -> None:
        """Changes conversation **read_only** state.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param read_only: value to set for the ``read_only`` state.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("PUT", self._ep_base + f"/api/v4/room/{token}/read-only", {"state": int(read_only)})

    def set_conversation_public(self, conversation: typing.Union[Conversation, str], public: bool) -> None:
        """Changes conversation **public** state.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param public: the value to be set as the new ``public`` state.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("POST" if public else "DELETE", self._ep_base + f"/api/v4/room/{token}/public")

    def set_conversation_notify_lvl(
        self, conversation: typing.Union[Conversation, str], new_lvl: NotificationLevel
    ) -> None:
        """Sets new notification level for user in the conversation.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param new_lvl: new value for notification level for the current user.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("POST", self._ep_base + f"/api/v4/room/{token}/notify", {"level": int(new_lvl)})

    def get_conversation_by_token(self, conversation: typing.Union[Conversation, str]) -> Conversation:
        """Gets conversation by token."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        result = self._session.ocs("GET", self._ep_base + f"/api/v4/room/{token}")
        self._update_config_sha()
        return Conversation(result)

    def delete_conversation(self, conversation: typing.Union[Conversation, str]) -> None:
        """Deletes a conversation.

        .. note:: Deleting a conversation that is the parent of breakout rooms, will also delete them.
            ``ONE_TO_ONE`` conversations can not be deleted for them
            :py:class:`~nc_py_api._talk_api._TalkAPI.leave_conversation` should be used.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("DELETE", self._ep_base + f"/api/v4/room/{token}")

    def leave_conversation(self, conversation: typing.Union[Conversation, str]) -> None:
        """Removes yourself from the conversation.

        .. note:: When the participant is a moderator or owner and there are no other moderators or owners left,
            participant can not leave conversation.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("DELETE", self._ep_base + f"/api/v4/room/{token}/participants/self")

    def send_message(
        self,
        message: str,
        conversation: typing.Union[Conversation, str] = "",
        reply_to_message: typing.Union[int, TalkMessage] = 0,
        silent: bool = False,
        actor_display_name: str = "",
    ) -> TalkMessage:
        """Send a message and returns a "reference string" to identify the message again in a "get messages" request.

        :param message: The message the user wants to say.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
            Need only if **reply_to_message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        :param reply_to_message: The message ID this message is a reply to.

            .. note:: Only allowed when the message type is not ``system`` or ``command``.
                The message you are replying to should be from the same conversation.
        :param silent: Flag controlling if the message should create a chat notifications for the users.
        :param actor_display_name: Guest display name (**ignored for the logged-in users**).
        :returns: :py:class:`~nc_py_api.talk.TalkMessage` that describes the sent message.
        :raises ValueError: in case of an invalid usage.
        """
        token = self._get_token(message, conversation)
        reference_id = hashlib.sha256(random_string(32).encode("UTF-8")).hexdigest()
        params = {
            "message": message,
            "actorDisplayName": actor_display_name,
            "replyTo": reply_to_message.message_id if isinstance(reply_to_message, TalkMessage) else reply_to_message,
            "referenceId": reference_id,
            "silent": silent,
        }
        r = self._session.ocs("POST", self._ep_base + f"/api/v1/chat/{token}", json=params)
        return TalkMessage(r)

    def receive_messages(
        self,
        conversation: typing.Union[Conversation, str],
        look_in_future: bool = False,
        limit: int = 100,
        timeout: int = 30,
        no_status_update: bool = True,
    ) -> list[TalkMessage]:
        """Receive chat messages of a conversation.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param look_in_future: ``True`` to poll and wait for the new message or ``False`` to get history.
        :param limit: Number of chat messages to receive (``100`` by default, ``200`` at most).
        :param timeout: ``look_in_future=1`` only: seconds to wait for the new messages (60 secs at most).
        :param no_status_update: When the user status should not be automatically set to the online.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        params = {
            "lookIntoFuture": int(look_in_future),
            "limit": limit,
            "timeout": timeout,
            "noStatusUpdate": int(no_status_update),
        }
        result = self._session.ocs("GET", self._ep_base + f"/api/v1/chat/{token}", params=params)
        return [TalkMessage(i) for i in result]

    def delete_message(
        self, message: typing.Union[TalkMessage, str], conversation: typing.Union[Conversation, str] = ""
    ) -> TalkMessage:
        """Delete a chat message.

        :param message: Message ID or :py:class:`~nc_py_api.talk.TalkMessage` to delete.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.

        .. note:: **Conversation** needed only if **message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        """
        token = self._get_token(message, conversation)
        message_id = message.message_id if isinstance(message, TalkMessage) else message
        result = self._session.ocs("DELETE", self._ep_base + f"/api/v1/chat/{token}/{message_id}")
        return TalkMessage(result)

    def react_to_message(
        self,
        message: typing.Union[TalkMessage, str],
        reaction: str,
        conversation: typing.Union[Conversation, str] = "",
    ) -> dict[str, list[MessageReactions]]:
        """React to a chat message.

        :param message: Message ID or :py:class:`~nc_py_api.talk.TalkMessage` to react to.
        :param reaction: A single emoji.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.

        .. note:: **Conversation** needed only if **message** is not :py:class:`~nc_py_api.talk.TalkMessage`

        :returns: list of reactions to the message.
        """
        token = self._get_token(message, conversation)
        message_id = message.message_id if isinstance(message, TalkMessage) else message
        params = {
            "reaction": reaction,
        }
        r = self._session.ocs("POST", self._ep_base + f"/api/v1/reaction/{token}/{message_id}", params=params)
        return {k: [MessageReactions(i) for i in v] for k, v in r.items()} if r else {}

    def delete_reaction(
        self,
        message: typing.Union[TalkMessage, str],
        reaction: str,
        conversation: typing.Union[Conversation, str] = "",
    ) -> dict[str, list[MessageReactions]]:
        """Remove reaction from a chat message.

        :param message: Message ID or :py:class:`~nc_py_api.talk.TalkMessage` to remove reaction from.
        :param reaction: A single emoji.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.

        .. note:: **Conversation** needed only if **message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        """
        token = self._get_token(message, conversation)
        message_id = message.message_id if isinstance(message, TalkMessage) else message
        params = {
            "reaction": reaction,
        }
        r = self._session.ocs("DELETE", self._ep_base + f"/api/v1/reaction/{token}/{message_id}", params=params)
        return {k: [MessageReactions(i) for i in v] for k, v in r.items()} if r else {}

    def get_message_reactions(
        self,
        message: typing.Union[TalkMessage, str],
        reaction_filter: str = "",
        conversation: typing.Union[Conversation, str] = "",
    ) -> dict[str, list[MessageReactions]]:
        """Get reactions information for a chat message.

        :param message: Message ID or :py:class:`~nc_py_api.talk.TalkMessage` to get reactions from.
        :param reaction_filter: A single emoji to get reaction information only for it.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.

        .. note:: **Conversation** needed only if **message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        """
        token = self._get_token(message, conversation)
        message_id = message.message_id if isinstance(message, TalkMessage) else message
        params = {"reaction": reaction_filter} if reaction_filter else {}
        r = self._session.ocs("GET", self._ep_base + f"/api/v1/reaction/{token}/{message_id}", params=params)
        return {k: [MessageReactions(i) for i in v] for k, v in r.items()} if r else {}

    def list_bots(self) -> list[BotInfo]:
        """Lists the bots that are installed on the server."""
        require_capabilities("spreed.features.bots-v1", self._session.capabilities)
        return [BotInfo(i) for i in self._session.ocs("GET", self._ep_base + "/api/v1/bot/admin")]

    def conversation_list_bots(self, conversation: typing.Union[Conversation, str]) -> list[BotInfoBasic]:
        """Lists the bots that are enabled and can be enabled for the conversation.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        require_capabilities("spreed.features.bots-v1", self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        return [BotInfoBasic(i) for i in self._session.ocs("GET", self._ep_base + f"/api/v1/bot/{token}")]

    def enable_bot(self, conversation: typing.Union[Conversation, str], bot: typing.Union[BotInfoBasic, int]) -> None:
        """Enable a bot for a conversation as a moderator.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param bot: bot ID or :py:class:`~nc_py_api.talk.BotInfoBasic`.
        """
        require_capabilities("spreed.features.bots-v1", self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        bot_id = bot.bot_id if isinstance(bot, BotInfoBasic) else bot
        self._session.ocs("POST", self._ep_base + f"/api/v1/bot/{token}/{bot_id}")

    def disable_bot(self, conversation: typing.Union[Conversation, str], bot: typing.Union[BotInfoBasic, int]) -> None:
        """Disable a bot for a conversation as a moderator.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param bot: bot ID or :py:class:`~nc_py_api.talk.BotInfoBasic`.
        """
        require_capabilities("spreed.features.bots-v1", self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        bot_id = bot.bot_id if isinstance(bot, BotInfoBasic) else bot
        self._session.ocs("DELETE", self._ep_base + f"/api/v1/bot/{token}/{bot_id}")

    @staticmethod
    def _get_token(message: typing.Union[TalkMessage, str], conversation: typing.Union[Conversation, str]) -> str:
        if not conversation and not isinstance(message, TalkMessage):
            raise ValueError("Either specify 'conversation' or provide 'TalkMessage'.")

        return (
            message.token
            if isinstance(message, TalkMessage)
            else conversation.token if isinstance(conversation, Conversation) else conversation
        )

    def _update_config_sha(self):
        config_sha = self._session.response_headers["X-Nextcloud-Talk-Hash"]
        if self.config_sha != config_sha:
            self._session.update_server_info()
            self.config_sha = config_sha
