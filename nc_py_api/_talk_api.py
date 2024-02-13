"""Nextcloud Talk API implementation."""

import hashlib

from ._exceptions import check_error
from ._misc import (
    check_capabilities,
    clear_from_params_empty,
    random_string,
    require_capabilities,
)
from ._session import AsyncNcSessionBasic, NcSessionBasic
from .files import FsNode, Share, ShareType
from .talk import (
    BotInfo,
    BotInfoBasic,
    Conversation,
    ConversationType,
    MessageReactions,
    NotificationLevel,
    Participant,
    Poll,
    TalkFileMessage,
    TalkMessage,
)


class _TalkAPI:
    """Class provides API to work with Nextcloud Talk, avalaible as **nc.talk.<method>**."""

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
        self, no_status_update: bool = True, include_status: bool = False, modified_since: int | bool = 0
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
            params["includeStatus"] = 1
        if modified_since:
            params["modifiedSince"] = self.modified_since if modified_since is True else modified_since

        result = self._session.ocs("GET", self._ep_base + "/api/v4/room", params=params)
        self.modified_since = int(self._session.response_headers["X-Nextcloud-Talk-Modified-Before"])
        self._update_config_sha()
        return [Conversation(i) for i in result]

    def list_participants(self, conversation: Conversation | str, include_status: bool = False) -> list[Participant]:
        """Returns a list of conversation participants.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param include_status: Whether the user status information of all one-to-one conversations should be loaded.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        result = self._session.ocs(
            "GET", self._ep_base + f"/api/v4/room/{token}/participants", params={"includeStatus": int(include_status)}
        )
        return [Participant(i) for i in result]

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

    def rename_conversation(self, conversation: Conversation | str, new_name: str) -> None:
        """Renames a conversation."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("PUT", self._ep_base + f"/api/v4/room/{token}", params={"roomName": new_name})

    def set_conversation_description(self, conversation: Conversation | str, description: str) -> None:
        """Sets conversation description."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs(
            "PUT", self._ep_base + f"/api/v4/room/{token}/description", params={"description": description}
        )

    def set_conversation_fav(self, conversation: Conversation | str, favorite: bool) -> None:
        """Changes conversation **favorite** state."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("POST" if favorite else "DELETE", self._ep_base + f"/api/v4/room/{token}/favorite")

    def set_conversation_password(self, conversation: Conversation | str, password: str) -> None:
        """Sets password for a conversation.

        Currently, it is only allowed to have a password for ``public`` conversations.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param password: new password for the conversation.

        .. note:: Password should match the password policy.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("PUT", self._ep_base + f"/api/v4/room/{token}/password", params={"password": password})

    def set_conversation_readonly(self, conversation: Conversation | str, read_only: bool) -> None:
        """Changes conversation **read_only** state."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("PUT", self._ep_base + f"/api/v4/room/{token}/read-only", params={"state": int(read_only)})

    def set_conversation_public(self, conversation: Conversation | str, public: bool) -> None:
        """Changes conversation **public** state."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("POST" if public else "DELETE", self._ep_base + f"/api/v4/room/{token}/public")

    def set_conversation_notify_lvl(self, conversation: Conversation | str, new_lvl: NotificationLevel) -> None:
        """Sets new notification level for user in the conversation."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("POST", self._ep_base + f"/api/v4/room/{token}/notify", json={"level": int(new_lvl)})

    def get_conversation_by_token(self, conversation: Conversation | str) -> Conversation:
        """Gets conversation by token."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        result = self._session.ocs("GET", self._ep_base + f"/api/v4/room/{token}")
        self._update_config_sha()
        return Conversation(result)

    def delete_conversation(self, conversation: Conversation | str) -> None:
        """Deletes a conversation.

        .. note:: Deleting a conversation that is the parent of breakout rooms, will also delete them.
            ``ONE_TO_ONE`` conversations cannot be deleted for them
            :py:class:`~nc_py_api._talk_api._TalkAPI.leave_conversation` should be used.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("DELETE", self._ep_base + f"/api/v4/room/{token}")

    def leave_conversation(self, conversation: Conversation | str) -> None:
        """Removes yourself from the conversation.

        .. note:: When the participant is a moderator or owner and there are no other moderators or owners left,
            participant cannot leave conversation.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("DELETE", self._ep_base + f"/api/v4/room/{token}/participants/self")

    def send_message(
        self,
        message: str,
        conversation: Conversation | str = "",
        reply_to_message: int | TalkMessage = 0,
        silent: bool = False,
        actor_display_name: str = "",
    ) -> TalkMessage:
        """Send a message to the conversation.

        :param message: The message the user wants to say.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
            Need only if **reply_to_message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        :param reply_to_message: The message ID this message is a reply to.

            .. note:: Only allowed when the message type is not ``system`` or ``command``.
                The message you are replying to should be from the same conversation.
        :param silent: Flag controlling if the message should create a chat notifications for the users.
        :param actor_display_name: Guest display name (**ignored for the logged-in users**).
        :raises ValueError: in case of an invalid usage.
        """
        params = _send_message(message, actor_display_name, silent, reply_to_message)
        token = _get_token(message, conversation)
        r = self._session.ocs("POST", self._ep_base + f"/api/v1/chat/{token}", json=params)
        return TalkMessage(r)

    def send_file(self, path: str | FsNode, conversation: Conversation | str = "") -> tuple[Share, str]:
        """Sends a file to the conversation."""
        reference_id, params = _send_file(path, conversation)
        require_capabilities("files_sharing.api_enabled", self._session.capabilities)
        r = self._session.ocs("POST", "/ocs/v1.php/apps/files_sharing/api/v1/shares", json=params)
        return Share(r), reference_id

    def receive_messages(
        self,
        conversation: Conversation | str,
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
        r = self._session.ocs("GET", self._ep_base + f"/api/v1/chat/{token}", params=params)
        return [TalkFileMessage(i, self._session.user) if i["message"] == "{file}" else TalkMessage(i) for i in r]

    def delete_message(self, message: TalkMessage | str, conversation: Conversation | str = "") -> TalkMessage:
        """Delete a chat message.

        :param message: Message ID or :py:class:`~nc_py_api.talk.TalkMessage` to delete.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.

        .. note:: **Conversation** needed only if **message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        """
        token = _get_token(message, conversation)
        message_id = message.message_id if isinstance(message, TalkMessage) else message
        result = self._session.ocs("DELETE", self._ep_base + f"/api/v1/chat/{token}/{message_id}")
        return TalkMessage(result)

    def react_to_message(
        self, message: TalkMessage | str, reaction: str, conversation: Conversation | str = ""
    ) -> dict[str, list[MessageReactions]]:
        """React to a chat message.

        :param message: Message ID or :py:class:`~nc_py_api.talk.TalkMessage` to react to.
        :param reaction: A single emoji.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.

        .. note:: **Conversation** needed only if **message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        """
        token = _get_token(message, conversation)
        message_id = message.message_id if isinstance(message, TalkMessage) else message
        params = {
            "reaction": reaction,
        }
        r = self._session.ocs("POST", self._ep_base + f"/api/v1/reaction/{token}/{message_id}", params=params)
        return {k: [MessageReactions(i) for i in v] for k, v in r.items()} if r else {}

    def delete_reaction(
        self, message: TalkMessage | str, reaction: str, conversation: Conversation | str = ""
    ) -> dict[str, list[MessageReactions]]:
        """Remove reaction from a chat message.

        :param message: Message ID or :py:class:`~nc_py_api.talk.TalkMessage` to remove reaction from.
        :param reaction: A single emoji.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.

        .. note:: **Conversation** needed only if **message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        """
        token = _get_token(message, conversation)
        message_id = message.message_id if isinstance(message, TalkMessage) else message
        params = {
            "reaction": reaction,
        }
        r = self._session.ocs("DELETE", self._ep_base + f"/api/v1/reaction/{token}/{message_id}", params=params)
        return {k: [MessageReactions(i) for i in v] for k, v in r.items()} if r else {}

    def get_message_reactions(
        self, message: TalkMessage | str, reaction_filter: str = "", conversation: Conversation | str = ""
    ) -> dict[str, list[MessageReactions]]:
        """Get reactions information for a chat message.

        :param message: Message ID or :py:class:`~nc_py_api.talk.TalkMessage` to get reactions from.
        :param reaction_filter: A single emoji to get reaction information only for it.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.

        .. note:: **Conversation** needed only if **message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        """
        token = _get_token(message, conversation)
        message_id = message.message_id if isinstance(message, TalkMessage) else message
        params = {"reaction": reaction_filter} if reaction_filter else {}
        r = self._session.ocs("GET", self._ep_base + f"/api/v1/reaction/{token}/{message_id}", params=params)
        return {k: [MessageReactions(i) for i in v] for k, v in r.items()} if r else {}

    def list_bots(self) -> list[BotInfo]:
        """Lists the bots that are installed on the server."""
        require_capabilities("spreed.features.bots-v1", self._session.capabilities)
        return [BotInfo(i) for i in self._session.ocs("GET", self._ep_base + "/api/v1/bot/admin")]

    def conversation_list_bots(self, conversation: Conversation | str) -> list[BotInfoBasic]:
        """Lists the bots that are enabled and can be enabled for the conversation.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        require_capabilities("spreed.features.bots-v1", self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        return [BotInfoBasic(i) for i in self._session.ocs("GET", self._ep_base + f"/api/v1/bot/{token}")]

    def enable_bot(self, conversation: Conversation | str, bot: BotInfoBasic | int) -> None:
        """Enable a bot for a conversation as a moderator.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param bot: bot ID or :py:class:`~nc_py_api.talk.BotInfoBasic`.
        """
        require_capabilities("spreed.features.bots-v1", self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        bot_id = bot.bot_id if isinstance(bot, BotInfoBasic) else bot
        self._session.ocs("POST", self._ep_base + f"/api/v1/bot/{token}/{bot_id}")

    def disable_bot(self, conversation: Conversation | str, bot: BotInfoBasic | int) -> None:
        """Disable a bot for a conversation as a moderator.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param bot: bot ID or :py:class:`~nc_py_api.talk.BotInfoBasic`.
        """
        require_capabilities("spreed.features.bots-v1", self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        bot_id = bot.bot_id if isinstance(bot, BotInfoBasic) else bot
        self._session.ocs("DELETE", self._ep_base + f"/api/v1/bot/{token}/{bot_id}")

    def create_poll(
        self,
        conversation: Conversation | str,
        question: str,
        options: list[str],
        hidden_results: bool = True,
        max_votes: int = 1,
    ) -> Poll:
        """Creates a poll in a conversation.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param question: The question of the poll.
        :param options: Array of strings with the voting options.
        :param hidden_results: Should results be hidden until the poll is closed and then only the summary is published.
        :param max_votes: The maximum amount of options a participant can vote for.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        params = {
            "question": question,
            "options": options,
            "resultMode": int(hidden_results),
            "maxVotes": max_votes,
        }
        return Poll(self._session.ocs("POST", self._ep_base + f"/api/v1/poll/{token}", json=params), token)

    def get_poll(self, poll: Poll | int, conversation: Conversation | str = "") -> Poll:
        """Get state or result of a poll.

        :param poll: Poll ID or :py:class:`~nc_py_api.talk.Poll`.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        if isinstance(poll, Poll):
            poll_id = poll.poll_id
            token = poll.conversation_token
        else:
            poll_id = poll
            token = conversation.token if isinstance(conversation, Conversation) else conversation
        return Poll(self._session.ocs("GET", self._ep_base + f"/api/v1/poll/{token}/{poll_id}"), token)

    def vote_poll(self, options_ids: list[int], poll: Poll | int, conversation: Conversation | str = "") -> Poll:
        """Vote on a poll.

        :param options_ids: The option IDs the participant wants to vote for.
        :param poll: Poll ID or :py:class:`~nc_py_api.talk.Poll`.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        if isinstance(poll, Poll):
            poll_id = poll.poll_id
            token = poll.conversation_token
        else:
            poll_id = poll
            token = conversation.token if isinstance(conversation, Conversation) else conversation
        r = self._session.ocs(
            "POST", self._ep_base + f"/api/v1/poll/{token}/{poll_id}", json={"optionIds": options_ids}
        )
        return Poll(r, token)

    def close_poll(self, poll: Poll | int, conversation: Conversation | str = "") -> Poll:
        """Close a poll.

        :param poll: Poll ID or :py:class:`~nc_py_api.talk.Poll`.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        if isinstance(poll, Poll):
            poll_id = poll.poll_id
            token = poll.conversation_token
        else:
            poll_id = poll
            token = conversation.token if isinstance(conversation, Conversation) else conversation
        return Poll(self._session.ocs("DELETE", self._ep_base + f"/api/v1/poll/{token}/{poll_id}"), token)

    def set_conversation_avatar(
        self, conversation: Conversation | str, avatar: bytes | tuple[str, str | None]
    ) -> Conversation:
        """Set image or emoji as avatar for the conversation.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param avatar: Squared image with mimetype equal to PNG or JPEG or a tuple with emoji and optional
            HEX color code(6 times ``0-9A-F``) without the leading ``#`` character.

            .. note:: When color omitted, fallback will be to the default bright/dark mode icon background color.
        """
        require_capabilities("spreed.features.avatar", self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        if isinstance(avatar, bytes):
            r = self._session.ocs("POST", self._ep_base + f"/api/v1/room/{token}/avatar", files={"file": avatar})
        else:
            r = self._session.ocs(
                "POST",
                self._ep_base + f"/api/v1/room/{token}/avatar/emoji",
                json={
                    "emoji": avatar[0],
                    "color": avatar[1],
                },
            )
        return Conversation(r)

    def delete_conversation_avatar(self, conversation: Conversation | str) -> Conversation:
        """Delete conversation avatar.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        require_capabilities("spreed.features.avatar", self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        return Conversation(self._session.ocs("DELETE", self._ep_base + f"/api/v1/room/{token}/avatar"))

    def get_conversation_avatar(self, conversation: Conversation | str, dark=False) -> bytes:
        """Get conversation avatar (binary).

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param dark: boolean indicating should be or not avatar fetched for dark theme.
        """
        require_capabilities("spreed.features.avatar", self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        ep_suffix = "/dark" if dark else ""
        response = self._session.adapter.get(self._ep_base + f"/api/v1/room/{token}/avatar" + ep_suffix)
        check_error(response)
        return response.content

    def _update_config_sha(self):
        config_sha = self._session.response_headers["X-Nextcloud-Talk-Hash"]
        if self.config_sha != config_sha:
            self._session.update_server_info()
            self.config_sha = config_sha


class _AsyncTalkAPI:
    """Class provides API to work with Nextcloud Talk."""

    _ep_base: str = "/ocs/v2.php/apps/spreed"
    config_sha: str
    """Sha1 value over Talk config. After receiving a different value on subsequent requests, settings got refreshed."""
    modified_since: int
    """Used by ``get_user_conversations``, when **modified_since** param is ``True``."""

    def __init__(self, session: AsyncNcSessionBasic):
        self._session = session
        self.config_sha = ""
        self.modified_since = 0

    @property
    async def available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("spreed", await self._session.capabilities)

    @property
    async def bots_available(self) -> bool:
        """Returns True if the Nextcloud instance supports this feature, False otherwise."""
        return not check_capabilities("spreed.features.bots-v1", await self._session.capabilities)

    async def get_user_conversations(
        self, no_status_update: bool = True, include_status: bool = False, modified_since: int | bool = 0
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
            params["includeStatus"] = 1
        if modified_since:
            params["modifiedSince"] = self.modified_since if modified_since is True else modified_since

        result = await self._session.ocs("GET", self._ep_base + "/api/v4/room", params=params)
        self.modified_since = int(self._session.response_headers["X-Nextcloud-Talk-Modified-Before"])
        await self._update_config_sha()
        return [Conversation(i) for i in result]

    async def list_participants(
        self, conversation: Conversation | str, include_status: bool = False
    ) -> list[Participant]:
        """Returns a list of conversation participants.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param include_status: Whether the user status information of all one-to-one conversations should be loaded.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        result = await self._session.ocs(
            "GET", self._ep_base + f"/api/v4/room/{token}/participants", params={"includeStatus": int(include_status)}
        )
        return [Participant(i) for i in result]

    async def create_conversation(
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
        return Conversation(await self._session.ocs("POST", self._ep_base + "/api/v4/room", json=params))

    async def rename_conversation(self, conversation: Conversation | str, new_name: str) -> None:
        """Renames a conversation."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        await self._session.ocs("PUT", self._ep_base + f"/api/v4/room/{token}", params={"roomName": new_name})

    async def set_conversation_description(self, conversation: Conversation | str, description: str) -> None:
        """Sets conversation description."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        await self._session.ocs(
            "PUT", self._ep_base + f"/api/v4/room/{token}/description", params={"description": description}
        )

    async def set_conversation_fav(self, conversation: Conversation | str, favorite: bool) -> None:
        """Changes conversation **favorite** state."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        await self._session.ocs("POST" if favorite else "DELETE", self._ep_base + f"/api/v4/room/{token}/favorite")

    async def set_conversation_password(self, conversation: Conversation | str, password: str) -> None:
        """Sets password for a conversation.

        Currently, it is only allowed to have a password for ``public`` conversations.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param password: new password for the conversation.

        .. note:: Password should match the password policy.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        await self._session.ocs("PUT", self._ep_base + f"/api/v4/room/{token}/password", params={"password": password})

    async def set_conversation_readonly(self, conversation: Conversation | str, read_only: bool) -> None:
        """Changes conversation **read_only** state."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        await self._session.ocs(
            "PUT", self._ep_base + f"/api/v4/room/{token}/read-only", params={"state": int(read_only)}
        )

    async def set_conversation_public(self, conversation: Conversation | str, public: bool) -> None:
        """Changes conversation **public** state."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        await self._session.ocs("POST" if public else "DELETE", self._ep_base + f"/api/v4/room/{token}/public")

    async def set_conversation_notify_lvl(self, conversation: Conversation | str, new_lvl: NotificationLevel) -> None:
        """Sets new notification level for user in the conversation."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        await self._session.ocs("POST", self._ep_base + f"/api/v4/room/{token}/notify", json={"level": int(new_lvl)})

    async def get_conversation_by_token(self, conversation: Conversation | str) -> Conversation:
        """Gets conversation by token."""
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        result = await self._session.ocs("GET", self._ep_base + f"/api/v4/room/{token}")
        await self._update_config_sha()
        return Conversation(result)

    async def delete_conversation(self, conversation: Conversation | str) -> None:
        """Deletes a conversation.

        .. note:: Deleting a conversation that is the parent of breakout rooms, will also delete them.
            ``ONE_TO_ONE`` conversations cannot be deleted for them
            :py:class:`~nc_py_api._talk_api._TalkAPI.leave_conversation` should be used.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        await self._session.ocs("DELETE", self._ep_base + f"/api/v4/room/{token}")

    async def leave_conversation(self, conversation: Conversation | str) -> None:
        """Removes yourself from the conversation.

        .. note:: When the participant is a moderator or owner and there are no other moderators or owners left,
            participant cannot leave conversation.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        await self._session.ocs("DELETE", self._ep_base + f"/api/v4/room/{token}/participants/self")

    async def send_message(
        self,
        message: str,
        conversation: Conversation | str = "",
        reply_to_message: int | TalkMessage = 0,
        silent: bool = False,
        actor_display_name: str = "",
    ) -> TalkMessage:
        """Send a message to the conversation.

        :param message: The message the user wants to say.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
            Need only if **reply_to_message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        :param reply_to_message: The message ID this message is a reply to.

            .. note:: Only allowed when the message type is not ``system`` or ``command``.
                The message you are replying to should be from the same conversation.
        :param silent: Flag controlling if the message should create a chat notifications for the users.
        :param actor_display_name: Guest display name (**ignored for the logged-in users**).
        :raises ValueError: in case of an invalid usage.
        """
        params = _send_message(message, actor_display_name, silent, reply_to_message)
        token = _get_token(message, conversation)
        r = await self._session.ocs("POST", self._ep_base + f"/api/v1/chat/{token}", json=params)
        return TalkMessage(r)

    async def send_file(self, path: str | FsNode, conversation: Conversation | str = "") -> tuple[Share, str]:
        """Sends a file to the conversation."""
        reference_id, params = _send_file(path, conversation)
        require_capabilities("files_sharing.api_enabled", await self._session.capabilities)
        r = await self._session.ocs("POST", "/ocs/v1.php/apps/files_sharing/api/v1/shares", json=params)
        return Share(r), reference_id

    async def receive_messages(
        self,
        conversation: Conversation | str,
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
        r = await self._session.ocs("GET", self._ep_base + f"/api/v1/chat/{token}", params=params)
        return [TalkFileMessage(i, await self._session.user) if i["message"] == "{file}" else TalkMessage(i) for i in r]

    async def delete_message(self, message: TalkMessage | str, conversation: Conversation | str = "") -> TalkMessage:
        """Delete a chat message.

        :param message: Message ID or :py:class:`~nc_py_api.talk.TalkMessage` to delete.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.

        .. note:: **Conversation** needed only if **message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        """
        token = _get_token(message, conversation)
        message_id = message.message_id if isinstance(message, TalkMessage) else message
        result = await self._session.ocs("DELETE", self._ep_base + f"/api/v1/chat/{token}/{message_id}")
        return TalkMessage(result)

    async def react_to_message(
        self, message: TalkMessage | str, reaction: str, conversation: Conversation | str = ""
    ) -> dict[str, list[MessageReactions]]:
        """React to a chat message.

        :param message: Message ID or :py:class:`~nc_py_api.talk.TalkMessage` to react to.
        :param reaction: A single emoji.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.

        .. note:: **Conversation** needed only if **message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        """
        token = _get_token(message, conversation)
        message_id = message.message_id if isinstance(message, TalkMessage) else message
        params = {
            "reaction": reaction,
        }
        r = await self._session.ocs("POST", self._ep_base + f"/api/v1/reaction/{token}/{message_id}", params=params)
        return {k: [MessageReactions(i) for i in v] for k, v in r.items()} if r else {}

    async def delete_reaction(
        self, message: TalkMessage | str, reaction: str, conversation: Conversation | str = ""
    ) -> dict[str, list[MessageReactions]]:
        """Remove reaction from a chat message.

        :param message: Message ID or :py:class:`~nc_py_api.talk.TalkMessage` to remove reaction from.
        :param reaction: A single emoji.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.

        .. note:: **Conversation** needed only if **message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        """
        token = _get_token(message, conversation)
        message_id = message.message_id if isinstance(message, TalkMessage) else message
        params = {
            "reaction": reaction,
        }
        r = await self._session.ocs("DELETE", self._ep_base + f"/api/v1/reaction/{token}/{message_id}", params=params)
        return {k: [MessageReactions(i) for i in v] for k, v in r.items()} if r else {}

    async def get_message_reactions(
        self, message: TalkMessage | str, reaction_filter: str = "", conversation: Conversation | str = ""
    ) -> dict[str, list[MessageReactions]]:
        """Get reactions information for a chat message.

        :param message: Message ID or :py:class:`~nc_py_api.talk.TalkMessage` to get reactions from.
        :param reaction_filter: A single emoji to get reaction information only for it.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.

        .. note:: **Conversation** needed only if **message** is not :py:class:`~nc_py_api.talk.TalkMessage`
        """
        token = _get_token(message, conversation)
        message_id = message.message_id if isinstance(message, TalkMessage) else message
        params = {"reaction": reaction_filter} if reaction_filter else {}
        r = await self._session.ocs("GET", self._ep_base + f"/api/v1/reaction/{token}/{message_id}", params=params)
        return {k: [MessageReactions(i) for i in v] for k, v in r.items()} if r else {}

    async def list_bots(self) -> list[BotInfo]:
        """Lists the bots that are installed on the server."""
        require_capabilities("spreed.features.bots-v1", await self._session.capabilities)
        return [BotInfo(i) for i in await self._session.ocs("GET", self._ep_base + "/api/v1/bot/admin")]

    async def conversation_list_bots(self, conversation: Conversation | str) -> list[BotInfoBasic]:
        """Lists the bots that are enabled and can be enabled for the conversation.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        require_capabilities("spreed.features.bots-v1", await self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        return [BotInfoBasic(i) for i in await self._session.ocs("GET", self._ep_base + f"/api/v1/bot/{token}")]

    async def enable_bot(self, conversation: Conversation | str, bot: BotInfoBasic | int) -> None:
        """Enable a bot for a conversation as a moderator.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param bot: bot ID or :py:class:`~nc_py_api.talk.BotInfoBasic`.
        """
        require_capabilities("spreed.features.bots-v1", await self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        bot_id = bot.bot_id if isinstance(bot, BotInfoBasic) else bot
        await self._session.ocs("POST", self._ep_base + f"/api/v1/bot/{token}/{bot_id}")

    async def disable_bot(self, conversation: Conversation | str, bot: BotInfoBasic | int) -> None:
        """Disable a bot for a conversation as a moderator.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param bot: bot ID or :py:class:`~nc_py_api.talk.BotInfoBasic`.
        """
        require_capabilities("spreed.features.bots-v1", await self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        bot_id = bot.bot_id if isinstance(bot, BotInfoBasic) else bot
        await self._session.ocs("DELETE", self._ep_base + f"/api/v1/bot/{token}/{bot_id}")

    async def create_poll(
        self,
        conversation: Conversation | str,
        question: str,
        options: list[str],
        hidden_results: bool = True,
        max_votes: int = 1,
    ) -> Poll:
        """Creates a poll in a conversation.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param question: The question of the poll.
        :param options: Array of strings with the voting options.
        :param hidden_results: Should results be hidden until the poll is closed and then only the summary is published.
        :param max_votes: The maximum amount of options a participant can vote for.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        params = {
            "question": question,
            "options": options,
            "resultMode": int(hidden_results),
            "maxVotes": max_votes,
        }
        return Poll(await self._session.ocs("POST", self._ep_base + f"/api/v1/poll/{token}", json=params), token)

    async def get_poll(self, poll: Poll | int, conversation: Conversation | str = "") -> Poll:
        """Get state or result of a poll.

        :param poll: Poll ID or :py:class:`~nc_py_api.talk.Poll`.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        if isinstance(poll, Poll):
            poll_id = poll.poll_id
            token = poll.conversation_token
        else:
            poll_id = poll
            token = conversation.token if isinstance(conversation, Conversation) else conversation
        return Poll(await self._session.ocs("GET", self._ep_base + f"/api/v1/poll/{token}/{poll_id}"), token)

    async def vote_poll(self, options_ids: list[int], poll: Poll | int, conversation: Conversation | str = "") -> Poll:
        """Vote on a poll.

        :param options_ids: The option IDs the participant wants to vote for.
        :param poll: Poll ID or :py:class:`~nc_py_api.talk.Poll`.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        if isinstance(poll, Poll):
            poll_id = poll.poll_id
            token = poll.conversation_token
        else:
            poll_id = poll
            token = conversation.token if isinstance(conversation, Conversation) else conversation
        r = await self._session.ocs(
            "POST", self._ep_base + f"/api/v1/poll/{token}/{poll_id}", json={"optionIds": options_ids}
        )
        return Poll(r, token)

    async def close_poll(self, poll: Poll | int, conversation: Conversation | str = "") -> Poll:
        """Close a poll.

        :param poll: Poll ID or :py:class:`~nc_py_api.talk.Poll`.
        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        if isinstance(poll, Poll):
            poll_id = poll.poll_id
            token = poll.conversation_token
        else:
            poll_id = poll
            token = conversation.token if isinstance(conversation, Conversation) else conversation
        return Poll(await self._session.ocs("DELETE", self._ep_base + f"/api/v1/poll/{token}/{poll_id}"), token)

    async def set_conversation_avatar(
        self, conversation: Conversation | str, avatar: bytes | tuple[str, str | None]
    ) -> Conversation:
        """Set image or emoji as avatar for the conversation.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param avatar: Squared image with mimetype equal to PNG or JPEG or a tuple with emoji and optional
            HEX color code(6 times ``0-9A-F``) without the leading ``#`` character.

            .. note:: When color omitted, fallback will be to the default bright/dark mode icon background color.
        """
        require_capabilities("spreed.features.avatar", await self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        if isinstance(avatar, bytes):
            r = await self._session.ocs("POST", self._ep_base + f"/api/v1/room/{token}/avatar", files={"file": avatar})
        else:
            r = await self._session.ocs(
                "POST",
                self._ep_base + f"/api/v1/room/{token}/avatar/emoji",
                json={
                    "emoji": avatar[0],
                    "color": avatar[1],
                },
            )
        return Conversation(r)

    async def delete_conversation_avatar(self, conversation: Conversation | str) -> Conversation:
        """Delete conversation avatar.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        require_capabilities("spreed.features.avatar", await self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        return Conversation(await self._session.ocs("DELETE", self._ep_base + f"/api/v1/room/{token}/avatar"))

    async def get_conversation_avatar(self, conversation: Conversation | str, dark=False) -> bytes:
        """Get conversation avatar (binary).

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        :param dark: boolean indicating should be or not avatar fetched for dark theme.
        """
        require_capabilities("spreed.features.avatar", await self._session.capabilities)
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        ep_suffix = "/dark" if dark else ""
        response = await self._session.adapter.get(self._ep_base + f"/api/v1/room/{token}/avatar" + ep_suffix)
        check_error(response)
        return response.content

    async def _update_config_sha(self):
        config_sha = self._session.response_headers["X-Nextcloud-Talk-Hash"]
        if self.config_sha != config_sha:
            await self._session.update_server_info()
            self.config_sha = config_sha


def _send_message(message: str, actor_display_name: str, silent: bool, reply_to_message: int | TalkMessage):
    return {
        "message": message,
        "actorDisplayName": actor_display_name,
        "replyTo": reply_to_message.message_id if isinstance(reply_to_message, TalkMessage) else reply_to_message,
        "referenceId": hashlib.sha256(random_string(32).encode("UTF-8")).hexdigest(),
        "silent": silent,
    }


def _send_file(path: str | FsNode, conversation: Conversation | str):
    token = conversation.token if isinstance(conversation, Conversation) else conversation
    reference_id = hashlib.sha256(random_string(32).encode("UTF-8")).hexdigest()
    params = {
        "shareType": ShareType.TYPE_ROOM,
        "shareWith": token,
        "path": path.user_path if isinstance(path, FsNode) else path,
        "referenceId": reference_id,
    }
    return reference_id, params


def _get_token(message: TalkMessage | str, conversation: Conversation | str) -> str:
    if not conversation and not isinstance(message, TalkMessage):
        raise ValueError("Either specify 'conversation' or provide 'TalkMessage'.")

    return (
        message.token
        if isinstance(message, TalkMessage)
        else conversation.token if isinstance(conversation, Conversation) else conversation
    )
