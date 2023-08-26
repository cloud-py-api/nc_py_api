import contextlib

import pytest
from gfixture import NC, NC_APP, NC_TO_TEST, NC_VERSION
from users_test import TEST_USER_NAME, TEST_USER_PASSWORD

from nc_py_api import Nextcloud, NextcloudException, talk, talk_bot

if NC is None or NC_APP is None:
    pytest.skip("Requires both Nextcloud Client and App modes.", allow_module_level=True)

if NC_TO_TEST[0].talk.available is False:
    pytest.skip("Nextcloud Talk is not installed.", allow_module_level=True)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_available(nc):
    assert nc.talk.available


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_bots_available(nc):
    assert isinstance(nc.talk.bots_available, bool)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_conversation_create_delete(nc):
    conversation = nc.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    nc.talk.delete_conversation(conversation)
    assert isinstance(conversation.conversation_id, int)
    assert isinstance(conversation.token, str) and conversation.token
    assert isinstance(conversation.name, str)
    assert isinstance(conversation.conversation_type, talk.ConversationType)
    assert isinstance(conversation.display_name, str)
    assert isinstance(conversation.description, str)
    assert isinstance(conversation.participant_type, talk.ParticipantType)
    assert isinstance(conversation.attendee_id, int)
    assert isinstance(conversation.attendee_pin, str)
    assert isinstance(conversation.actor_type, str)
    assert isinstance(conversation.actor_id, str)
    assert isinstance(conversation.permissions, talk.AttendeePermissions)
    assert isinstance(conversation.attendee_permissions, talk.AttendeePermissions)
    assert isinstance(conversation.call_permissions, talk.AttendeePermissions)
    assert isinstance(conversation.default_permissions, talk.AttendeePermissions)
    assert isinstance(conversation.participant_flags, talk.InCallFlags)
    assert isinstance(conversation.read_only, bool)
    assert isinstance(conversation.listable, talk.ListableScope)
    assert isinstance(conversation.message_expiration, int)
    assert isinstance(conversation.has_password, bool)
    assert isinstance(conversation.has_call, bool)
    assert isinstance(conversation.call_flag, talk.InCallFlags)
    assert isinstance(conversation.can_start_call, bool)
    assert isinstance(conversation.can_delete_conversation, bool)
    assert isinstance(conversation.can_leave_conversation, bool)
    assert isinstance(conversation.last_activity, int)
    assert isinstance(conversation.is_favorite, bool)
    assert isinstance(conversation.notification_level, talk.NotificationLevel)
    assert isinstance(conversation.lobby_state, talk.WebinarLobbyStates)
    assert isinstance(conversation.lobby_timer, int)
    assert isinstance(conversation.sip_enabled, talk.SipEnabledStatus)
    assert isinstance(conversation.can_enable_sip, bool)
    assert isinstance(conversation.unread_messages_count, int)
    assert isinstance(conversation.unread_mention, bool)
    assert isinstance(conversation.unread_mention_direct, bool)
    assert isinstance(conversation.last_read_message, int)
    assert isinstance(conversation.last_message, talk.TalkMessage) or conversation.last_message is None
    assert isinstance(conversation.last_common_read_message, int)
    assert isinstance(conversation.breakout_room_mode, talk.BreakoutRoomMode)
    assert isinstance(conversation.breakout_room_status, talk.BreakoutRoomStatus)
    assert isinstance(conversation.avatar_version, str)
    assert isinstance(conversation.is_custom_avatar, bool)
    assert isinstance(conversation.call_start_time, int)
    assert isinstance(conversation.recording_status, talk.CallRecordingStatus)
    if conversation.last_message is None:
        return
    talk_msg = conversation.last_message
    assert isinstance(talk_msg.message_id, int)
    assert isinstance(talk_msg.token, str)
    assert talk_msg.actor_type in ("users", "guests", "bots", "bridged")
    assert isinstance(talk_msg.actor_id, str)
    assert isinstance(talk_msg.actor_display_name, str)
    assert isinstance(talk_msg.timestamp, int)
    assert isinstance(talk_msg.system_message, str)
    assert talk_msg.message_type in ("comment", "comment_deleted", "system", "command")
    assert talk_msg.is_replyable is False
    assert isinstance(talk_msg.reference_id, str)
    assert isinstance(talk_msg.message, str)
    assert isinstance(talk_msg.message_parameters, dict)
    assert isinstance(talk_msg.expiration_timestamp, int)
    assert isinstance(talk_msg.parent, list)
    assert isinstance(talk_msg.reactions, dict)
    assert isinstance(talk_msg.reactions_self, list)
    assert isinstance(talk_msg.markdown, bool)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_conversations_modified_since(nc):
    conversation = nc.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        conversations = nc.talk.get_user_conversations()
        assert conversations
        nc.talk.modified_since += 2  # read notes for ``modified_since`` param in docs.
        conversations = nc.talk.get_user_conversations(modified_since=True)
        assert not conversations
        conversations = nc.talk.get_user_conversations(modified_since=9992708529, no_status_update=False)
        assert not conversations
    finally:
        nc.talk.delete_conversation(conversation.token)


@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_get_conversations_include_status(nc):
    with contextlib.suppress(NextcloudException):
        NC.users.create(TEST_USER_NAME, password=TEST_USER_PASSWORD)
    nc_second_user = Nextcloud(nc_auth_user=TEST_USER_NAME, nc_auth_pass=TEST_USER_PASSWORD)
    nc_second_user.user_status.set_status_type("away")
    conversation = nc.talk.create_conversation(talk.ConversationType.ONE_TO_ONE, TEST_USER_NAME)
    try:
        conversations = nc.talk.get_user_conversations(include_status=False)
        assert conversations
        first_conv = [i for i in conversations if i.conversation_id == conversation.conversation_id][0]
        assert not first_conv.status_type
        conversations = nc.talk.get_user_conversations(include_status=True)
        assert conversations
        first_conv = [i for i in conversations if i.conversation_id == conversation.conversation_id][0]
        assert first_conv.status_type == "away"
    finally:
        nc.talk.leave_conversation(conversation.token)
        NC.users.delete(TEST_USER_NAME)


@pytest.mark.skipif(NC_VERSION["major"] < 27 and NC_VERSION["minor"] >= 1, reason="Run only on NC27.1+")
@pytest.mark.skipif(NC_APP.check_capabilities("spreed.features.bots-v1"), reason="Need Talk bots support.")
def test_register_unregister_talk_bot():
    NC_APP.unregister_talk_bot("/talk_bot_coverage")
    list_of_bots = NC_APP.talk.list_bots()
    NC_APP.register_talk_bot("/talk_bot_coverage", "Coverage bot", "Desc")
    assert len(list_of_bots) + 1 == len(NC_APP.talk.list_bots())
    NC_APP.register_talk_bot("/talk_bot_coverage", "Coverage bot", "Desc")
    assert len(list_of_bots) + 1 == len(NC_APP.talk.list_bots())
    assert NC_APP.unregister_talk_bot("/talk_bot_coverage") is True
    assert len(list_of_bots) == len(NC_APP.talk.list_bots())
    assert NC_APP.unregister_talk_bot("/talk_bot_coverage") is False
    assert len(list_of_bots) == len(NC_APP.talk.list_bots())


@pytest.mark.skipif(NC_VERSION["major"] < 27 and NC_VERSION["minor"] >= 1, reason="Run only on NC27.1+")
@pytest.mark.skipif(NC_APP.check_capabilities("spreed.features.bots-v1"), reason="Need Talk bots support.")
@pytest.mark.parametrize("nc", NC_TO_TEST)
def test_list_bots(nc):
    NC_APP.register_talk_bot("/some_url", "some bot name", "some desc")
    registered_bot = [i for i in nc.talk.list_bots() if i.bot_name == "some bot name"][0]
    assert isinstance(registered_bot.bot_id, int)
    assert registered_bot.url.find("/some_url") != -1
    assert registered_bot.description == "some desc"
    assert registered_bot.state == 1
    assert not registered_bot.error_count
    assert registered_bot.last_error_date == 0
    assert registered_bot.last_error_message is None
    assert isinstance(registered_bot.url_hash, str)
    conversation = nc.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        assert nc.talk.conversation_list_bots(conversation)
    finally:
        nc.talk.delete_conversation(conversation.token)


@pytest.mark.skipif(NC_VERSION["major"] < 27 and NC_VERSION["minor"] >= 1, reason="Run only on NC27.1+")
@pytest.mark.skipif(NC_APP.check_capabilities("spreed.features.bots-v1"), reason="Need Talk bots support.")
def test_chat_bot_receive_message():
    talk_bot_inst = talk_bot.TalkBot("/talk_bot_coverage", "Coverage bot", "Desc")
    talk_bot_inst.enabled_handler(True, NC_APP)
    conversation = NC_APP.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        coverage_bot = [i for i in NC_APP.talk.list_bots() if i.url.endswith("/talk_bot_coverage")][0]
        c_bot_info = [i for i in NC_APP.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id][0]
        assert c_bot_info.state == 0
        NC_APP.talk.enable_bot(conversation, coverage_bot)
        c_bot_info = [i for i in NC_APP.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id][0]
        assert c_bot_info.state == 1
        with pytest.raises(ValueError):
            NC_APP.talk.send_message("Here are the msg!")
        NC_APP.talk.send_message("Here are the msg!", conversation)
        msg_from_bot = None
        for _ in range(40):
            messages = NC_APP.talk.receive_messages(conversation, look_in_future=True, timeout=1)
            if messages[-1].message == "Hello from bot!":
                msg_from_bot = messages[-1]
                break
        assert msg_from_bot
        c_bot_info = [i for i in NC_APP.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id][0]
        assert c_bot_info.state == 1
        NC_APP.talk.disable_bot(conversation, coverage_bot)
        c_bot_info = [i for i in NC_APP.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id][0]
        assert c_bot_info.state == 0
    finally:
        NC_APP.talk.delete_conversation(conversation.token)
        talk_bot_inst.enabled_handler(False, NC_APP)
    talk_bot_inst.callback_url = "invalid_url"
    with pytest.raises(RuntimeError):
        talk_bot_inst.send_message("message", 999999, token="sometoken")
