"""Nextcloud Talk API definitions."""

import dataclasses
import datetime
import enum
import os

from . import files as _files


class ConversationType(enum.IntEnum):
    """Talk conversation types."""

    ONE_TO_ONE = 1
    """Direct One to One"""
    GROUP = 2
    """Group conversation(group chat)"""
    PUBLIC = 3
    """Group conversation opened to all"""
    CHANGELOG = 4
    """Conversation that some App start to inform about new features, changes, e.g. changelog."""
    FORMER = 5
    """Former "One to one"
    (When a user is deleted from the server or removed from all their conversations,
    "One to one" rooms are converted to this type)"""


class ParticipantType(enum.IntEnum):
    """Permissions level of the current user."""

    OWNER = 1
    """Creator of the conversation"""
    MODERATOR = 2
    """Moderator of the conversation"""
    USER = 3
    """Conversation participant"""
    GUEST = 4
    """Conversation participant, with no account on NC instance"""
    USER_SELF_JOINED = 5
    """User following a public link"""
    GUEST_MODERATOR = 6
    """Conversation moderator, with no account on NC instance"""


class AttendeePermissions(enum.IntFlag):
    """Final permissions for the current participant.

    .. note:: Permissions are picked in order of attendee then call, then default,
        and the first which is ``Custom`` will apply.
    """

    DEFAULT = 0
    """Default permissions (will pick the one from the next level of: ``user``, ``call``, ``conversation``)"""
    CUSTOM = 1
    """Custom permissions (this is required to be able to remove all other permissions)"""
    START_CALL = 2
    """Start call"""
    JOIN_CALL = 4
    """Join call"""
    IGNORE = 8
    """Can ignore lobby"""
    AUDIO = 16
    """Can publish audio stream"""
    VIDEO = 32
    """Can publish video stream"""
    SHARE_SCREEN = 64
    """Can publish screen sharing stream"""
    OTHER = 128
    """Can post chat message, share items and do reactions"""


class InCallFlags(enum.IntFlag):
    """Participant in-call flags."""

    DISCONNECTED = 0
    IN_CALL = 1
    PROVIDES_AUDIO = 2
    PROVIDES_VIDEO = 4
    USES_SIP_DIAL_IN = 8


class ListableScope(enum.IntEnum):
    """Listable scope for the room."""

    PARTICIPANTS_ONLY = 0
    ONLY_REGULAR_USERS = 1
    EVERYONE = 2


class NotificationLevel(enum.IntEnum):
    """The notification level for the user.

    .. note:: Default: ``1`` for ``one-to-one`` conversations, ``2`` for other conversations.
    """

    DEFAULT = 0
    ALWAYS_NOTIFY = 1
    NOTIFY_ON_MENTION = 2
    NEVER_NOTIFY = 3


class WebinarLobbyStates(enum.IntEnum):
    """Webinar lobby restriction (0-1), if the participant is a moderator, they can always join the conversation."""

    NO_LOBBY = 0
    NON_MODERATORS = 1


class SipEnabledStatus(enum.IntEnum):
    """SIP enable status."""

    DISABLED = 0
    ENABLED = 1
    """Each participant needs a unique PIN."""
    ENABLED_NO_PIN = 2
    """Only the conversation token is required."""


class CallRecordingStatus(enum.IntEnum):
    """Type of call recording."""

    NO_RECORDING = 0
    VIDEO = 1
    AUDIO = 2
    STARTING_VIDEO = 3
    STARTING_AUDIO = 4
    RECORDING_FAILED = 5


class BreakoutRoomMode(enum.IntEnum):
    """Breakout room modes."""

    NOT_CONFIGURED = 0
    AUTOMATIC = 1
    """ Attendees are unsorted and then distributed over the rooms, so they all have the same participant count."""
    MANUAL = 2
    """A map with attendee to room number specifies the participants."""
    FREE = 3
    """Each attendee picks their own breakout room."""


class BreakoutRoomStatus(enum.IntEnum):
    """Breakout room status."""

    STOPPED = 0
    """Breakout rooms lobbies are disabled."""
    STARTED = 1
    """Breakout rooms lobbies are enabled."""


@dataclasses.dataclass
class MessageReactions:
    """One reaction for a message, retrieved with :py:meth:`~nc_py_api._talk_api._TalkAPI.get_message_reactions`."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def actor_type(self) -> str:
        """Actor types of the chat message: **users**, **guests**."""
        return self._raw_data["actorType"]

    @property
    def actor_id(self) -> str:
        """Actor id of the message author."""
        return self._raw_data["actorId"]

    @property
    def actor_display_name(self) -> str:
        """A display name of the message author."""
        return self._raw_data["actorDisplayName"]

    @property
    def timestamp(self) -> int:
        """Timestamp in seconds and UTC time zone."""
        return self._raw_data["timestamp"]


@dataclasses.dataclass
class TalkMessage:
    """Talk message."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def message_id(self) -> int:
        """Numeric identifier of the message. Most methods that require this should accept this class itself."""
        return self._raw_data["id"]

    @property
    def token(self) -> str:
        """Token identifier of the conversation which is used for further interaction."""
        return self._raw_data["token"]

    @property
    def actor_type(self) -> str:
        """Actor types of the chat message: **users**, **guests**, **bots**, **bridged**."""
        return self._raw_data["actorType"]

    @property
    def actor_id(self) -> str:
        """Actor id of the message author."""
        return self._raw_data["actorId"]

    @property
    def actor_display_name(self) -> str:
        """A display name of the message author."""
        return self._raw_data["actorDisplayName"]

    @property
    def timestamp(self) -> int:
        """Timestamp in seconds and UTC time zone."""
        return self._raw_data["timestamp"]

    @property
    def system_message(self) -> str:
        """Empty for the normal chat message or the type of the system message (untranslated)."""
        return self._raw_data["systemMessage"]

    @property
    def message_type(self) -> str:
        """Currently known types are "comment", "comment_deleted", "system" and "command"."""
        return self._raw_data["messageType"]

    @property
    def is_replyable(self) -> bool:
        """True if the user can post a reply to this message.

        .. note:: Only available with ``chat-replies`` capability.
        """
        return self._raw_data["isReplyable"]

    @property
    def reference_id(self) -> str:
        """A reference string that was given while posting the message to be able to identify the sent message again.

        .. note:: Only available with ``chat-reference-id`` capability.
        """
        return self._raw_data["referenceId"]

    @property
    def message(self) -> str:
        """Message string with placeholders.

        See `Rich Object String <https://nextcloud-talk.readthedocs.io/en/latest/chat/#parent-data>`_.
        """
        return self._raw_data["message"]

    @property
    def message_parameters(self) -> dict:
        """Message parameters for the ``message``."""
        return self._raw_data["messageParameters"]

    @property
    def expiration_timestamp(self) -> int:
        """Unix time stamp when the message expires and show be removed from the client's UI without further note.

        .. note:: Only available with ``message-expiration`` capability.
        """
        return self._raw_data["expirationTimestamp"]

    @property
    def parent(self) -> list:
        """To be refactored: `Description here <https://nextcloud-talk.readthedocs.io/en/latest/chat/#parent-data>`_."""
        return self._raw_data.get("parent", [])

    @property
    def reactions(self) -> dict:
        """An array map with relation between reaction emoji and total count of reactions with this emoji."""
        return self._raw_data.get("reactions", {})

    @property
    def reactions_self(self) -> list[str]:
        """When the user reacted, this is the list of emojis the user reacted with."""
        return self._raw_data.get("reactionsSelf", [])

    @property
    def markdown(self) -> bool:
        """Whether the message should be rendered as markdown or shown as plain text."""
        return self._raw_data.get("markdown", False)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} id={self.message_id}, author={self.actor_display_name},"
            f" time={datetime.datetime.utcfromtimestamp(self.timestamp).replace(tzinfo=datetime.timezone.utc)}>"
        )


class TalkFileMessage(TalkMessage):
    """Subclass of Talk Message representing message-containing file."""

    def __init__(self, raw_data: dict, user_id: str):
        super().__init__(raw_data)
        self._user_id = user_id

    def to_fs_node(self) -> _files.FsNode:
        """Returns usual :py:class:`~nc_py_api.files.FsNode` created from this class."""
        _file_params: dict = self.message_parameters["file"]
        user_path = _file_params["path"].rstrip("/")
        is_dir = bool(_file_params["mimetype"].lower() == "httpd/unix-directory")
        if is_dir:
            user_path += "/"
        full_path = os.path.join(f"files/{self._user_id}", user_path.lstrip("/"))
        permissions = _files.permissions_to_str(_file_params["permissions"], is_dir)
        return _files.FsNode(
            full_path,
            etag=_file_params["etag"],
            size=_file_params["size"],
            content_length=0 if is_dir else _file_params["size"],
            permissions=permissions,
            fileid=_file_params["id"],
            mimetype=_file_params["mimetype"],
        )


@dataclasses.dataclass
class _TalkUserStatus:
    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def status_message(self) -> str:
        """Message of the status."""
        return str(self._raw_data.get("statusMessage", "") or "")

    @property
    def status_icon(self) -> str:
        """The icon picked by the user (must be one emoji)."""
        return str(self._raw_data.get("statusIcon", "") or "")

    @property
    def status_type(self) -> str:
        """Status type, on of the: online, away, dnd, invisible, offline."""
        return str(self._raw_data.get("status", "") or "")


@dataclasses.dataclass(init=False)
class Conversation(_TalkUserStatus):
    """Talk conversation."""

    @property
    def conversation_id(self) -> int:
        """Numeric identifier of the conversation. Most methods that require this should accept this class itself."""
        return self._raw_data["id"]

    @property
    def token(self) -> str:
        """Token identifier of the conversation which is used for further interaction."""
        return self._raw_data["token"]

    @property
    def conversation_type(self) -> ConversationType:
        """Type of the conversation, see: :py:class:`~nc_py_api.talk.ConversationType`."""
        return ConversationType(self._raw_data["type"])

    @property
    def name(self) -> str:
        """Name of the conversation (can also be empty)."""
        return self._raw_data.get("name", "")

    @property
    def display_name(self) -> str:
        """``name`` if non-empty, otherwise it falls back to a list of participants."""
        return self._raw_data["displayName"]

    @property
    def description(self) -> str:
        """Description of the conversation (can also be empty) (only available with ``room-description`` capability)."""
        return self._raw_data.get("description", "")

    @property
    def participant_type(self) -> ParticipantType:
        """Permissions level of the current user, see: :py:class:`~nc_py_api.talk.ParticipantType`."""
        return ParticipantType(self._raw_data["participantType"])

    @property
    def attendee_id(self) -> int:
        """Unique attendee id."""
        return self._raw_data["attendeeId"]

    @property
    def attendee_pin(self) -> str:
        """Unique dial-in authentication code for this user when the conversation has SIP enabled."""
        return self._raw_data["attendeePin"]

    @property
    def actor_type(self) -> str:
        """Actor types of chat messages: **users**, **guests**, **bots**, **bridged**."""
        return self._raw_data["actorType"]

    @property
    def actor_id(self) -> str:
        """The unique identifier for the given actor type."""
        return self._raw_data["actorId"]

    @property
    def permissions(self) -> AttendeePermissions:
        """Final permissions, combined :py:class:`~nc_py_api.talk.AttendeePermissions` values."""
        return AttendeePermissions(self._raw_data["permissions"])

    @property
    def attendee_permissions(self) -> AttendeePermissions:
        """Dedicated permissions for the current participant, if not ``Custom``, they are not the resulting ones."""
        return AttendeePermissions(self._raw_data["attendeePermissions"])

    @property
    def call_permissions(self) -> AttendeePermissions:
        """Call permissions, if not ``Custom``, these are not the resulting permissions.

        .. note:: If set, they will reset after the end of the call.
        """
        return AttendeePermissions(self._raw_data["callPermissions"])

    @property
    def default_permissions(self) -> AttendeePermissions:
        """Default permissions for new participants."""
        return AttendeePermissions(self._raw_data["defaultPermissions"])

    @property
    def participant_flags(self) -> InCallFlags:
        """``In call`` flags of the user's session making the request.

        .. note:: Available with ``in-call-flags`` capability.
        """
        return InCallFlags(self._raw_data.get("participantFlags", InCallFlags.DISCONNECTED))

    @property
    def read_only(self) -> bool:
        """Read-only state for the current user (only available with ``read-only-rooms`` capability)."""
        return bool(self._raw_data.get("readOnly", False))

    @property
    def listable(self) -> ListableScope:
        """Listable scope for the room (only available with ``listable-rooms`` capability)."""
        return ListableScope(self._raw_data.get("listable", ListableScope.PARTICIPANTS_ONLY))

    @property
    def message_expiration(self) -> int:
        """The message expiration time in seconds in this chat. Zero if disabled.

        .. note:: Only available with ``message-expiration`` capability.
        """
        return self._raw_data.get("messageExpiration", 0)

    @property
    def has_password(self) -> bool:
        """Flag if the conversation has a password."""
        return bool(self._raw_data["hasPassword"])

    @property
    def has_call(self) -> bool:
        """Flag if the conversation has call."""
        return bool(self._raw_data["hasCall"])

    @property
    def call_flag(self) -> InCallFlags:
        """Combined flag of all participants in the current call.

        .. note:: Only available with ``conversation-call-flags`` capability.
        """
        return InCallFlags(self._raw_data.get("callFlag", InCallFlags.DISCONNECTED))

    @property
    def can_start_call(self) -> bool:
        """Flag if the user can start a new call in this conversation (joining is always possible).

        .. note:: Only available with start-call-flag capability.
        """
        return bool(self._raw_data.get("canStartCall", False))

    @property
    def can_delete_conversation(self) -> bool:
        """Flag if the user can delete the conversation for everyone.

        .. note: Not possible without moderator permissions or in ``one-to-one`` conversations.
        """
        return bool(self._raw_data.get("canDeleteConversation", False))

    @property
    def can_leave_conversation(self) -> bool:
        """Flag if the user can leave the conversation (not possible for the last user with moderator permissions)."""
        return bool(self._raw_data.get("canLeaveConversation", False))

    @property
    def last_activity(self) -> int:
        """Timestamp of the last activity in the conversation, in seconds and UTC time zone."""
        return self._raw_data["lastActivity"]

    @property
    def is_favorite(self) -> bool:
        """Flag if the conversation is favorite for the user."""
        return self._raw_data["isFavorite"]

    @property
    def notification_level(self) -> NotificationLevel:
        """The notification level for the user."""
        return NotificationLevel(self._raw_data["notificationLevel"])

    @property
    def lobby_state(self) -> WebinarLobbyStates:
        """Webinar lobby restriction (0-1).

        .. note:: Only available with ``webinary-lobby`` capability.
        """
        return WebinarLobbyStates(self._raw_data["lobbyState"])

    @property
    def lobby_timer(self) -> int:
        """Timestamp when the lobby will be automatically disabled.

        .. note:: Only available with ``webinary-lobby`` capability.
        """
        return self._raw_data["lobbyTimer"]

    @property
    def sip_enabled(self) -> SipEnabledStatus:
        """Status of the SIP for the conversation."""
        return SipEnabledStatus(self._raw_data["sipEnabled"])

    @property
    def can_enable_sip(self) -> bool:
        """Whether the given user can enable SIP for this conversation.

        .. note:: When the token is not-numeric only, SIP can not be enabled even
            if the user is permitted and a moderator of the conversation.
        """
        return bool(self._raw_data["canEnableSIP"])

    @property
    def unread_messages_count(self) -> int:
        """Number of unread chat messages in the conversation.

        .. note: Only available with chat-v2 capability.
        """
        return self._raw_data["unreadMessages"]

    @property
    def unread_mention(self) -> bool:
        """Flag if the user was mentioned since their last visit."""
        return self._raw_data["unreadMention"]

    @property
    def unread_mention_direct(self) -> bool:
        """Flag if the user was mentioned directly (ignoring **@all** mentions) since their last visit.

        .. note:: Only available with ``direct-mention-flag`` capability.
        """
        return self._raw_data["unreadMentionDirect"]

    @property
    def last_read_message(self) -> int:
        """ID of the last read message in a room.

        .. note:: only available with ``chat-read-marker`` capability.
        """
        return self._raw_data["lastReadMessage"]

    @property
    def last_common_read_message(self) -> int:
        """``ID`` of the last message read by every user that has read privacy set to public in a room.

        When the user himself has it set to ``private`` the value is ``0``.

        .. note:: Only available with ``chat-read-status`` capability.
        """
        return self._raw_data["lastCommonReadMessage"]

    @property
    def last_message(self) -> TalkMessage | None:
        """Last message in a conversation if available, otherwise ``empty``.

        .. note:: Even when given, the message will not contain the ``parent`` or ``reactionsSelf``
            attribute due to performance reasons
        """
        return TalkMessage(self._raw_data["lastMessage"]) if self._raw_data["lastMessage"] else None

    @property
    def breakout_room_mode(self) -> BreakoutRoomMode:
        """Breakout room configuration mode.

        .. note:: Only available with ``breakout-rooms-v1`` capability.
        """
        return BreakoutRoomMode(self._raw_data.get("breakoutRoomMode", BreakoutRoomMode.NOT_CONFIGURED))

    @property
    def breakout_room_status(self) -> BreakoutRoomStatus:
        """Breakout room status.

        .. note:: Only available with ``breakout-rooms-v1`` capability.
        """
        return BreakoutRoomStatus(self._raw_data.get("breakoutRoomStatus", BreakoutRoomStatus.STOPPED))

    @property
    def avatar_version(self) -> str:
        """Version of conversation avatar used to easier expiration of the avatar in case a moderator updates it.

        .. note:: Only available with ``avatar`` capability.
        """
        return self._raw_data["avatarVersion"]

    @property
    def is_custom_avatar(self) -> bool:
        """Flag if the conversation has a custom avatar.

        .. note:: Only available with ``avatar`` capability.
        """
        return self._raw_data.get("isCustomAvatar", False)

    @property
    def call_start_time(self) -> int:
        """Timestamp when the call was started.

        .. note:: Only available with ``recording-v1`` capability.
        """
        return self._raw_data["callStartTime"]

    @property
    def recording_status(self) -> CallRecordingStatus:
        """Call recording status..

        .. note:: Only available with ``recording-v1`` capability.
        """
        return CallRecordingStatus(self._raw_data.get("callRecording", CallRecordingStatus.NO_RECORDING))

    @property
    def status_clear_at(self) -> int | None:
        """Unix Timestamp representing the time to clear the status.

        .. note:: Available only for ``one-to-one`` conversations.
        """
        return self._raw_data.get("statusClearAt", None)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} id={self.conversation_id}, name={self.display_name},"
            f" type={self.conversation_type.name}>"
        )


@dataclasses.dataclass(init=False)
class Participant(_TalkUserStatus):
    """Conversation participant information."""

    @property
    def attendee_id(self) -> int:
        """Unique attendee id."""
        return self._raw_data["attendeeId"]

    @property
    def actor_type(self) -> str:
        """The actor type of the participant that voted: **users**, **groups**, **circles**, **guests**, **emails**."""
        return self._raw_data["actorType"]

    @property
    def actor_id(self) -> str:
        """The unique identifier for the given actor type."""
        return self._raw_data["actorId"]

    @property
    def display_name(self) -> str:
        """Can be empty for guests."""
        return self._raw_data["displayName"]

    @property
    def participant_type(self) -> ParticipantType:
        """Permissions level, see: :py:class:`~nc_py_api.talk.ParticipantType`."""
        return ParticipantType(self._raw_data["participantType"])

    @property
    def last_ping(self) -> int:
        """Timestamp of the last ping. Should be used for sorting."""
        return self._raw_data["lastPing"]

    @property
    def participant_flags(self) -> InCallFlags:
        """Current call flags."""
        return InCallFlags(self._raw_data.get("inCall", InCallFlags.DISCONNECTED))

    @property
    def permissions(self) -> AttendeePermissions:
        """Final permissions, combined :py:class:`~nc_py_api.talk.AttendeePermissions` values."""
        return AttendeePermissions(self._raw_data["permissions"])

    @property
    def attendee_permissions(self) -> AttendeePermissions:
        """Dedicated permissions for the current participant, if not ``Custom``, they are not the resulting ones."""
        return AttendeePermissions(self._raw_data["attendeePermissions"])

    @property
    def session_ids(self) -> list[str]:
        """A list of session IDs, each one 512 characters long, or empty if there is no session."""
        return self._raw_data["sessionIds"]

    @property
    def breakout_token(self) -> str:
        """Only available with breakout-rooms-v1 capability."""
        return self._raw_data.get("roomToken", "")

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} id={self.attendee_id}, name={self.display_name}, last_ping={self.last_ping}>"
        )


@dataclasses.dataclass
class BotInfoBasic:
    """Basic information about the Nextcloud Talk Bot."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def bot_id(self) -> int:
        """Unique numeric identifier of the bot on this server."""
        return self._raw_data["id"]

    @property
    def bot_name(self) -> str:
        """The display name of the bot shown as author when it posts a message or reaction."""
        return self._raw_data["name"]

    @property
    def description(self) -> str:
        """A longer description of the bot helping moderators to decide if they want to enable this bot."""
        return self._raw_data["description"]

    @property
    def state(self) -> int:
        """One of the Bot states: ``0`` - Disabled, ``1`` - enabled, ``2`` - **No setup**."""
        return self._raw_data["state"]

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.bot_id}, name={self.bot_name}>"


@dataclasses.dataclass(init=False)
class BotInfo(BotInfoBasic):
    """Full information about the Nextcloud Talk Bot."""

    @property
    def url(self) -> str:
        """URL endpoint that is triggered by this bot."""
        return self._raw_data["url"]

    @property
    def url_hash(self) -> str:
        """Hash of the URL prefixed with ``bot-`` serves as ``actor_id``."""
        return self._raw_data["url_hash"]

    @property
    def error_count(self) -> int:
        """Number of consecutive errors."""
        return self._raw_data["error_count"]

    @property
    def last_error_date(self) -> int:
        """UNIX timestamp of the last error."""
        return self._raw_data["last_error_date"]

    @property
    def last_error_message(self) -> str | None:
        """The last exception message or error response information when trying to reach the bot."""
        return self._raw_data["last_error_message"]


@dataclasses.dataclass
class PollDetail:
    """Detail about who voted for option."""

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data

    @property
    def actor_type(self) -> str:
        """The actor type of the participant that voted: **users**, **groups**, **circles**, **guests**, **emails**."""
        return self._raw_data["actorType"]

    @property
    def actor_id(self) -> str:
        """The actor id of the participant that voted."""
        return self._raw_data["actorId"]

    @property
    def actor_display_name(self) -> str:
        """The display name of the participant that voted."""
        return self._raw_data["actorDisplayName"]

    @property
    def option(self) -> int:
        """The option that was voted for."""
        return self._raw_data["optionId"]

    def __repr__(self):
        return f"<{self.__class__.__name__} actor={self.actor_display_name}, voted_for={self.option}>"


@dataclasses.dataclass
class Poll:
    """Conversation Poll information."""

    def __init__(self, raw_data: dict, conversation_token: str):
        self._raw_data = raw_data
        self._conversation_token = conversation_token

    @property
    def conversation_token(self) -> str:
        """Token identifier of the conversation to which poll belongs."""
        return self._conversation_token

    @property
    def poll_id(self) -> int:
        """ID of the poll."""
        return self._raw_data["id"]

    @property
    def question(self) -> str:
        """The question of the poll."""
        return self._raw_data["question"]

    @property
    def options(self) -> list[str]:
        """Options participants can vote for."""
        return self._raw_data["options"]

    @property
    def votes(self) -> dict[str, int]:
        """Map with 'option-' + optionId => number of votes.

        .. note:: Only available for when the actor voted on the public poll or the poll is closed.
        """
        return self._raw_data.get("votes", {})

    @property
    def actor_type(self) -> str:
        """Actor type of the poll author: **users**, **groups**, **circles**, **guests**, **emails**."""
        return self._raw_data["actorType"]

    @property
    def actor_id(self) -> str:
        """Actor ID identifying the poll author."""
        return self._raw_data["actorId"]

    @property
    def actor_display_name(self) -> str:
        """The display name of the poll author."""
        return self._raw_data["actorDisplayName"]

    @property
    def closed(self) -> bool:
        """Participants can no longer cast votes and the result is displayed."""
        return bool(self._raw_data["status"] == 1)

    @property
    def hidden_results(self) -> bool:
        """The results are hidden until the poll is closed."""
        return bool(self._raw_data["resultMode"] == 1)

    @property
    def max_votes(self) -> int:
        """The maximum amount of options a user can vote for, ``0`` means unlimited."""
        return self._raw_data["maxVotes"]

    @property
    def voted_self(self) -> list[int]:
        """Array of option ids the participant voted for."""
        return self._raw_data["votedSelf"]

    @property
    def num_voters(self) -> int:
        """The number of unique voters that voted.

        .. note:: only available when the actor voted on the public poll or the
            poll is closed unless for the creator and moderators.
        """
        return self._raw_data.get("numVoters", 0)

    @property
    def details(self) -> list[PollDetail]:
        """Detailed list who voted for which option (only available for public closed polls)."""
        return [PollDetail(i) for i in self._raw_data.get("details", [])]

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.poll_id}, author={self.actor_display_name}>"
