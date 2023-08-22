"""Nextcloud Talk API."""

import dataclasses
import enum
import typing

from ._misc import check_capabilities, clear_from_params_empty
from ._session import NcSessionBasic
from .user_status import _UserStatus


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

    .. note:: Default: ``1`` for one-to-one conversations, ``2`` for other conversations.
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


@dataclasses.dataclass(init=False)
class Conversation(_UserStatus):
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

        .. note: Not possible without moderator permissions or in one-to-one conversations.
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
        return self._raw_data["isCustomAvatar"]

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


class _TalkAPI:
    """Class that implements work with Nextcloud Talk."""

    _ep_base: str = "/ocs/v2.php/apps/spreed/api/v4"
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

    def get_user_conversations(
        self, no_status_update: bool = True, include_status: bool = False, modified_since: typing.Union[int, bool] = 0
    ) -> list[Conversation]:
        """Returns the list of the user's conversations.

        :param no_status_update: When the user status should not be automatically set to the online. Default = **True**
        :param include_status: Whether the user status information of all one-to-one conversations should be loaded.
        :param modified_since: When provided only conversations with a newer **lastActivity**
            (and one-to-one conversations when includeStatus is provided) are returned.
            Can be set to ``True`` to automatically use last ``modified_since`` from previous calls. Default = **0**.
        """
        params: dict = {}
        if no_status_update:
            params["noStatusUpdate"] = True
        if include_status:
            params["includeStatus"] = True
        if modified_since:
            params["modifiedSince"] = self.modified_since if modified_since is True else modified_since

        result = self._session.ocs("GET", self._ep_base + "/room", params=params)
        self.modified_since = int(self._session.response_headers["X-Nextcloud-Talk-Modified-Before"])
        config_sha = self._session.response_headers["X-Nextcloud-Talk-Hash"]
        if self.config_sha != config_sha:
            self._session.update_server_info()
            self.config_sha = config_sha
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
        return Conversation(self._session.ocs("POST", self._ep_base + "/room", json=params))

    def delete_conversation(self, conversation: typing.Union[Conversation, str]) -> None:
        """Deletes a conversation.

        .. note:: Deleting a conversation that is the parent of breakout rooms, will also delete them.
            ``ONE_TO_ONE`` conversations can not be deleted, use :py:class:`~nc_py_api.talk.leave_conversation`.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("DELETE", self._ep_base + f"/room/{token}")

    def leave_conversation(self, conversation: typing.Union[Conversation, str]) -> None:
        """Removes yourself from the conversation.

        .. note:: When the participant is a moderator or owner and there are no other moderators or owners left,
            participant can not leave conversation.

        :param conversation: conversation token or :py:class:`~nc_py_api.talk.Conversation`.
        """
        token = conversation.token if isinstance(conversation, Conversation) else conversation
        self._session.ocs("DELETE", self._ep_base + f"/room/{token}/participants/self")
