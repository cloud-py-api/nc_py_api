from os import environ

import pytest

from nc_py_api import Nextcloud, talk, talk_bot


def test_conversation_create_delete(nc):
    if nc.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")
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


def test_get_conversations_modified_since(nc):
    if nc.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")
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


def test_get_conversations_include_status(nc, nc_client):
    if nc.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")
    nc_second_user = Nextcloud(nc_auth_user=environ["TEST_USER_ID"], nc_auth_pass=environ["TEST_USER_PASS"])
    nc_second_user.user_status.set_status_type("away")
    conversation = nc.talk.create_conversation(talk.ConversationType.ONE_TO_ONE, environ["TEST_USER_ID"])
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


def test_rename_description_favorite_get_conversation(nc_any):
    if nc_any.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")
    conversation = nc_any.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        nc_any.talk.rename_conversation(conversation, "new era")
        assert conversation.is_favorite is False
        nc_any.talk.set_conversation_description(conversation, "the description")
        nc_any.talk.set_conversation_fav(conversation, True)
        nc_any.talk.set_conversation_readonly(conversation, True)
        nc_any.talk.set_conversation_public(conversation, True)
        nc_any.talk.set_conversation_notify_lvl(conversation, talk.NotificationLevel.NEVER_NOTIFY)
        nc_any.talk.set_conversation_password(conversation, "zJf4aLafv8941nvs")
        conversation = nc_any.talk.get_conversation_by_token(conversation)
        assert conversation.display_name == "new era"
        assert conversation.description == "the description"
        assert conversation.is_favorite is True
        assert conversation.read_only is True
        assert conversation.notification_level == talk.NotificationLevel.NEVER_NOTIFY
        assert conversation.has_password is True
        nc_any.talk.set_conversation_fav(conversation, False)
        nc_any.talk.set_conversation_readonly(conversation, False)
        nc_any.talk.set_conversation_password(conversation, "")
        nc_any.talk.set_conversation_public(conversation, False)
        conversation = nc_any.talk.get_conversation_by_token(conversation)
        assert conversation.is_favorite is False
        assert conversation.read_only is False
        assert conversation.has_password is False
    finally:
        nc_any.talk.delete_conversation(conversation)


@pytest.mark.require_nc(major=27)
def test_message_send_delete_reactions(nc_any):
    if nc_any.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")
    conversation = nc_any.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        msg = nc_any.talk.send_message("yo yo yo!", conversation)
        reactions = nc_any.talk.react_to_message(msg, "❤️")
        assert "❤️" in reactions
        assert len(reactions["❤️"]) == 1
        reaction = reactions["❤️"][0]
        assert reaction.actor_id == nc_any.user
        assert reaction.actor_type == "users"
        assert reaction.actor_display_name
        assert isinstance(reaction.timestamp, int)
        reactions2 = nc_any.talk.get_message_reactions(msg)
        assert reactions == reactions2
        nc_any.talk.react_to_message(msg, "☝️️")
        assert nc_any.talk.delete_reaction(msg, "❤️")
        assert not nc_any.talk.delete_reaction(msg, "☝️️")
        assert not nc_any.talk.get_message_reactions(msg)
        result = nc_any.talk.delete_message(msg)
        assert result.system_message == "message_deleted"
        messages = nc_any.talk.receive_messages(conversation)
        deleted = [i for i in messages if i.system_message == "message_deleted"]
        assert deleted
    finally:
        nc_any.talk.delete_conversation(conversation)


@pytest.mark.require_nc(major=27, minor=1)
def test_register_unregister_talk_bot(nc_app):
    if nc_app.talk.bots_available is False:
        pytest.skip("Need Talk bots support")
    nc_app.unregister_talk_bot("/talk_bot_coverage")
    list_of_bots = nc_app.talk.list_bots()
    nc_app.register_talk_bot("/talk_bot_coverage", "Coverage bot", "Desc")
    assert len(list_of_bots) + 1 == len(nc_app.talk.list_bots())
    nc_app.register_talk_bot("/talk_bot_coverage", "Coverage bot", "Desc")
    assert len(list_of_bots) + 1 == len(nc_app.talk.list_bots())
    assert nc_app.unregister_talk_bot("/talk_bot_coverage") is True
    assert len(list_of_bots) == len(nc_app.talk.list_bots())
    assert nc_app.unregister_talk_bot("/talk_bot_coverage") is False
    assert len(list_of_bots) == len(nc_app.talk.list_bots())


@pytest.mark.require_nc(major=27, minor=1)
def test_list_bots(nc, nc_app):
    if nc_app.talk.bots_available is False:
        pytest.skip("Need Talk bots support")
    nc_app.register_talk_bot("/some_url", "some bot name", "some desc")
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


@pytest.mark.require_nc(major=27, minor=1)
def test_chat_bot_receive_message(nc_app):
    if nc_app.talk.bots_available is False:
        pytest.skip("Need Talk bots support")
    talk_bot_inst = talk_bot.TalkBot("/talk_bot_coverage", "Coverage bot", "Desc")
    talk_bot_inst.enabled_handler(True, nc_app)
    conversation = nc_app.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        coverage_bot = [i for i in nc_app.talk.list_bots() if i.url.endswith("/talk_bot_coverage")][0]
        c_bot_info = [i for i in nc_app.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id][0]
        assert c_bot_info.state == 0
        nc_app.talk.enable_bot(conversation, coverage_bot)
        c_bot_info = [i for i in nc_app.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id][0]
        assert c_bot_info.state == 1
        with pytest.raises(ValueError):
            nc_app.talk.send_message("Here are the msg!")
        nc_app.talk.send_message("Here are the msg!", conversation)
        msg_from_bot = None
        for _ in range(40):
            messages = nc_app.talk.receive_messages(conversation, look_in_future=True, timeout=1)
            if messages[-1].message == "Hello from bot!":
                msg_from_bot = messages[-1]
                break
        assert msg_from_bot
        c_bot_info = [i for i in nc_app.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id][0]
        assert c_bot_info.state == 1
        nc_app.talk.disable_bot(conversation, coverage_bot)
        c_bot_info = [i for i in nc_app.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id][0]
        assert c_bot_info.state == 0
    finally:
        nc_app.talk.delete_conversation(conversation.token)
        talk_bot_inst.enabled_handler(False, nc_app)
    talk_bot_inst.callback_url = "invalid_url"
    with pytest.raises(RuntimeError):
        talk_bot_inst.send_message("message", 999999, token="sometoken")