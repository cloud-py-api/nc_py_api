from io import BytesIO
from os import environ

import pytest
from PIL import Image

from nc_py_api import AsyncNextcloud, Nextcloud, NextcloudException, files, talk


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
    assert isinstance(conversation.status_type, str)
    assert isinstance(conversation.status_message, str)
    assert isinstance(conversation.status_icon, str)
    assert isinstance(conversation.status_clear_at, int) or conversation.status_clear_at is None
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


@pytest.mark.asyncio(scope="session")
async def test_get_conversations_modified_since_async(anc):
    if await anc.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")
    conversation = await anc.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        conversations = await anc.talk.get_user_conversations()
        assert conversations
        anc.talk.modified_since += 2  # read notes for ``modified_since`` param in docs.
        conversations = await anc.talk.get_user_conversations(modified_since=True)
        assert not conversations
        conversations = await anc.talk.get_user_conversations(modified_since=9992708529, no_status_update=False)
        assert not conversations
    finally:
        await anc.talk.delete_conversation(conversation.token)


def _test_get_conversations_include_status(participants: list[talk.Participant]):
    assert len(participants) == 2
    second_participant = next(i for i in participants if i.actor_id == environ["TEST_USER_ID"])
    assert second_participant.actor_type == "users"
    assert isinstance(second_participant.attendee_id, int)
    assert isinstance(second_participant.display_name, str)
    assert isinstance(second_participant.participant_type, talk.ParticipantType)
    assert isinstance(second_participant.last_ping, int)
    assert second_participant.participant_flags == talk.InCallFlags.DISCONNECTED
    assert isinstance(second_participant.permissions, talk.AttendeePermissions)
    assert isinstance(second_participant.attendee_permissions, talk.AttendeePermissions)
    assert isinstance(second_participant.session_ids, list)
    assert isinstance(second_participant.breakout_token, str)
    assert second_participant.status_message == ""
    assert str(second_participant).find("last_ping=") != -1


@pytest.mark.asyncio(scope="session")
async def test_get_conversations_include_status_async(anc, anc_client):
    if await anc.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")
    nc_second_user = AsyncNextcloud(nc_auth_user=environ["TEST_USER_ID"], nc_auth_pass=environ["TEST_USER_PASS"])
    await nc_second_user.user_status.set_status_type("away")
    await nc_second_user.user_status.set_status("my status message-async", status_icon="😇")
    conversation = await anc.talk.create_conversation(talk.ConversationType.ONE_TO_ONE, environ["TEST_USER_ID"])
    try:
        conversations = await anc.talk.get_user_conversations(include_status=False)
        assert conversations
        first_conv = next(i for i in conversations if i.conversation_id == conversation.conversation_id)
        assert not first_conv.status_type
        conversations = await anc.talk.get_user_conversations(include_status=True)
        assert conversations
        first_conv = next(i for i in conversations if i.conversation_id == conversation.conversation_id)
        assert first_conv.status_type == "away"
        assert first_conv.status_message == "my status message-async"
        assert first_conv.status_icon == "😇"
        participants = await anc.talk.list_participants(first_conv)
        # 10 april 2025: something changed in Nextcloud 31+, and now here is "1" as result instead of 2
        if len(participants) == 1:
            return
        _test_get_conversations_include_status(participants)
        participants = await anc.talk.list_participants(first_conv, include_status=True)
        assert len(participants) == 2
        second_participant = next(i for i in participants if i.actor_id == environ["TEST_USER_ID"])
        assert second_participant.status_message == "my status message-async"
        assert str(conversation).find("type=") != -1
    finally:
        await anc.talk.leave_conversation(conversation.token)


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


@pytest.mark.asyncio(scope="session")
async def test_rename_description_favorite_get_conversation_async(anc_any):
    if await anc_any.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")
    conversation = await anc_any.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        await anc_any.talk.rename_conversation(conversation, "new era")
        assert conversation.is_favorite is False
        await anc_any.talk.set_conversation_description(conversation, "the description")
        await anc_any.talk.set_conversation_fav(conversation, True)
        await anc_any.talk.set_conversation_readonly(conversation, True)
        await anc_any.talk.set_conversation_public(conversation, True)
        await anc_any.talk.set_conversation_notify_lvl(conversation, talk.NotificationLevel.NEVER_NOTIFY)
        await anc_any.talk.set_conversation_password(conversation, "zJf4aLafv8941nvs")
        conversation = await anc_any.talk.get_conversation_by_token(conversation)
        assert conversation.display_name == "new era"
        assert conversation.description == "the description"
        assert conversation.is_favorite is True
        assert conversation.read_only is True
        assert conversation.notification_level == talk.NotificationLevel.NEVER_NOTIFY
        assert conversation.has_password is True
        await anc_any.talk.set_conversation_fav(conversation, False)
        await anc_any.talk.set_conversation_readonly(conversation, False)
        await anc_any.talk.set_conversation_password(conversation, "")
        await anc_any.talk.set_conversation_public(conversation, False)
        conversation = await anc_any.talk.get_conversation_by_token(conversation)
        assert conversation.is_favorite is False
        assert conversation.read_only is False
        assert conversation.has_password is False
    finally:
        await anc_any.talk.delete_conversation(conversation)


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
        assert str(deleted[0]).find("time=") != -1
    finally:
        nc_any.talk.delete_conversation(conversation)


@pytest.mark.asyncio(scope="session")
async def test_message_send_delete_reactions_async(anc_any):
    if await anc_any.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")
    conversation = await anc_any.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        msg = await anc_any.talk.send_message("yo yo yo!", conversation)
        reactions = await anc_any.talk.react_to_message(msg, "❤️")
        assert "❤️" in reactions
        assert len(reactions["❤️"]) == 1
        reaction = reactions["❤️"][0]
        assert reaction.actor_id == await anc_any.user
        assert reaction.actor_type == "users"
        assert reaction.actor_display_name
        assert isinstance(reaction.timestamp, int)
        reactions2 = await anc_any.talk.get_message_reactions(msg)
        assert reactions == reactions2
        await anc_any.talk.react_to_message(msg, "☝️️")
        assert await anc_any.talk.delete_reaction(msg, "❤️")
        assert not await anc_any.talk.delete_reaction(msg, "☝️️")
        assert not await anc_any.talk.get_message_reactions(msg)
        result = await anc_any.talk.delete_message(msg)
        assert result.system_message == "message_deleted"
        messages = await anc_any.talk.receive_messages(conversation)
        deleted = [i for i in messages if i.system_message == "message_deleted"]
        assert deleted
        assert str(deleted[0]).find("time=") != -1
    finally:
        await anc_any.talk.delete_conversation(conversation)


def _test_create_close_poll(poll: talk.Poll, closed: bool, user: str, conversation_token: str):
    assert isinstance(poll.poll_id, int)
    assert poll.question == "When was this test written?"
    assert poll.options == ["2000", "2023", "2030"]
    assert poll.max_votes == 1
    assert poll.num_voters == 0
    assert poll.hidden_results is True
    assert poll.details == []
    assert poll.closed is closed
    assert poll.conversation_token == conversation_token
    assert poll.actor_type == "users"
    assert poll.actor_id == user
    assert isinstance(poll.actor_display_name, str)
    assert poll.voted_self == []
    assert poll.votes == []


def test_create_close_poll(nc_any):
    if nc_any.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")

    conversation = nc_any.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        poll = nc_any.talk.create_poll(conversation, "When was this test written?", ["2000", "2023", "2030"])
        assert str(poll).find("author=") != -1
        _test_create_close_poll(poll, False, nc_any.user, conversation.token)
        poll = nc_any.talk.get_poll(poll)
        _test_create_close_poll(poll, False, nc_any.user, conversation.token)
        poll = nc_any.talk.get_poll(poll.poll_id, conversation.token)
        _test_create_close_poll(poll, False, nc_any.user, conversation.token)
        poll = nc_any.talk.close_poll(poll.poll_id, conversation.token)
        _test_create_close_poll(poll, True, nc_any.user, conversation.token)
    finally:
        nc_any.talk.delete_conversation(conversation)


@pytest.mark.asyncio(scope="session")
async def test_create_close_poll_async(anc_any):
    if await anc_any.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")

    conversation = await anc_any.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        poll = await anc_any.talk.create_poll(conversation, "When was this test written?", ["2000", "2023", "2030"])
        assert str(poll).find("author=") != -1
        _test_create_close_poll(poll, False, await anc_any.user, conversation.token)
        poll = await anc_any.talk.get_poll(poll)
        _test_create_close_poll(poll, False, await anc_any.user, conversation.token)
        poll = await anc_any.talk.get_poll(poll.poll_id, conversation.token)
        _test_create_close_poll(poll, False, await anc_any.user, conversation.token)
        poll = await anc_any.talk.close_poll(poll.poll_id, conversation.token)
        _test_create_close_poll(poll, True, await anc_any.user, conversation.token)
    finally:
        await anc_any.talk.delete_conversation(conversation)


def test_vote_poll(nc_any):
    if nc_any.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")

    conversation = nc_any.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        poll = nc_any.talk.create_poll(
            conversation, "what color is the grass", ["red", "green", "blue"], hidden_results=False, max_votes=3
        )
        assert poll.hidden_results is False
        assert not poll.voted_self
        poll = nc_any.talk.vote_poll([0, 2], poll)
        assert poll.voted_self == [0, 2]
        assert poll.votes == {
            "option-0": 1,
            "option-2": 1,
        }
        assert poll.num_voters == 1
        poll = nc_any.talk.vote_poll([1], poll.poll_id, conversation)
        assert poll.voted_self == [1]
        assert poll.votes == {
            "option-1": 1,
        }
        poll = nc_any.talk.close_poll(poll)
        assert poll.closed is True
        assert len(poll.details) == 1
        assert poll.details[0].actor_id == nc_any.user
        assert poll.details[0].actor_type == "users"
        assert poll.details[0].option == 1
        assert isinstance(poll.details[0].actor_display_name, str)
        assert str(poll.details[0]).find("actor=") != -1
    finally:
        nc_any.talk.delete_conversation(conversation)


@pytest.mark.asyncio(scope="session")
async def test_vote_poll_async(anc_any):
    if await anc_any.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")

    conversation = await anc_any.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        poll = await anc_any.talk.create_poll(
            conversation, "what color is the grass", ["red", "green", "blue"], hidden_results=False, max_votes=3
        )
        assert poll.hidden_results is False
        assert not poll.voted_self
        poll = await anc_any.talk.vote_poll([0, 2], poll)
        assert poll.voted_self == [0, 2]
        assert poll.votes == {
            "option-0": 1,
            "option-2": 1,
        }
        assert poll.num_voters == 1
        poll = await anc_any.talk.vote_poll([1], poll.poll_id, conversation)
        assert poll.voted_self == [1]
        assert poll.votes == {
            "option-1": 1,
        }
        poll = await anc_any.talk.close_poll(poll)
        assert poll.closed is True
        assert len(poll.details) == 1
        assert poll.details[0].actor_id == await anc_any.user
        assert poll.details[0].actor_type == "users"
        assert poll.details[0].option == 1
        assert isinstance(poll.details[0].actor_display_name, str)
        assert str(poll.details[0]).find("actor=") != -1
    finally:
        await anc_any.talk.delete_conversation(conversation)


def test_conversation_avatar(nc_any):
    if nc_any.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")

    conversation = nc_any.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        assert conversation.is_custom_avatar is False
        r = nc_any.talk.get_conversation_avatar(conversation)
        assert isinstance(r, bytes)
        im = Image.effect_mandelbrot((512, 512), (-3, -2.5, 2, 2.5), 100)
        buffer = BytesIO()
        im.save(buffer, format="PNG")
        buffer.seek(0)
        r = nc_any.talk.set_conversation_avatar(conversation, buffer.read())
        assert r.is_custom_avatar is True
        r = nc_any.talk.get_conversation_avatar(conversation)
        assert isinstance(r, bytes)
        r = nc_any.talk.delete_conversation_avatar(conversation)
        assert r.is_custom_avatar is False
        r = nc_any.talk.set_conversation_avatar(conversation, ("🫡", None))
        assert r.is_custom_avatar is True
        r = nc_any.talk.get_conversation_avatar(conversation, dark=True)
        assert isinstance(r, bytes)
        with pytest.raises(NextcloudException):
            nc_any.talk.get_conversation_avatar("not_exist_conversation")
    finally:
        nc_any.talk.delete_conversation(conversation)


@pytest.mark.asyncio(scope="session")
async def test_conversation_avatar_async(anc_any):
    if await anc_any.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")

    conversation = await anc_any.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        assert conversation.is_custom_avatar is False
        r = await anc_any.talk.get_conversation_avatar(conversation)
        assert isinstance(r, bytes)
        im = Image.effect_mandelbrot((512, 512), (-3, -2.5, 2, 2.5), 100)
        buffer = BytesIO()
        im.save(buffer, format="PNG")
        buffer.seek(0)
        r = await anc_any.talk.set_conversation_avatar(conversation, buffer.read())
        assert r.is_custom_avatar is True
        r = await anc_any.talk.get_conversation_avatar(conversation)
        assert isinstance(r, bytes)
        r = await anc_any.talk.delete_conversation_avatar(conversation)
        assert r.is_custom_avatar is False
        r = await anc_any.talk.set_conversation_avatar(conversation, ("🫡", None))
        assert r.is_custom_avatar is True
        r = await anc_any.talk.get_conversation_avatar(conversation, dark=True)
        assert isinstance(r, bytes)
        with pytest.raises(NextcloudException):
            await anc_any.talk.get_conversation_avatar("not_exist_conversation")
    finally:
        await anc_any.talk.delete_conversation(conversation)


def test_send_receive_file(nc_client):
    if nc_client.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")

    nc_second_user = Nextcloud(nc_auth_user=environ["TEST_USER_ID"], nc_auth_pass=environ["TEST_USER_PASS"])
    conversation = nc_client.talk.create_conversation(talk.ConversationType.ONE_TO_ONE, environ["TEST_USER_ID"])
    try:
        r, reference_id = nc_client.talk.send_file("/test_dir/subdir/test_12345_text.txt", conversation)
        assert isinstance(reference_id, str)
        assert isinstance(r, files.Share)
        for _ in range(10):
            m = nc_second_user.talk.receive_messages(conversation, limit=1)
            if m and isinstance(m[0], talk.TalkFileMessage):
                break
        m_t: talk.TalkFileMessage = m[0]  # noqa
        fs_node = m_t.to_fs_node()
        assert nc_second_user.files.download(fs_node) == b"12345"
        assert m_t.reference_id == reference_id
        assert fs_node.is_dir is False
        # test with directory
        directory = nc_client.files.by_path("/test_dir/subdir/")
        r, reference_id = nc_client.talk.send_file(directory, conversation)
        assert isinstance(reference_id, str)
        assert isinstance(r, files.Share)
        for _ in range(10):
            m = nc_second_user.talk.receive_messages(conversation, limit=1)
            if m and m[0].reference_id == reference_id:
                break
        m_t: talk.TalkFileMessage = m[0]  # noqa
        assert m_t.reference_id == reference_id
        fs_node = m_t.to_fs_node()
        assert fs_node.is_dir is True
    finally:
        nc_client.talk.leave_conversation(conversation.token)


@pytest.mark.asyncio(scope="session")
async def test_send_receive_file_async(anc_client):
    if await anc_client.talk.available is False:
        pytest.skip("Nextcloud Talk is not installed")

    nc_second_user = AsyncNextcloud(nc_auth_user=environ["TEST_USER_ID"], nc_auth_pass=environ["TEST_USER_PASS"])
    conversation = await anc_client.talk.create_conversation(talk.ConversationType.ONE_TO_ONE, environ["TEST_USER_ID"])
    try:
        r, reference_id = await anc_client.talk.send_file("/test_dir/test_12345_text.txt", conversation)
        assert isinstance(reference_id, str)
        assert isinstance(r, files.Share)
        for _ in range(10):
            m = await nc_second_user.talk.receive_messages(conversation, limit=1)
            if m and isinstance(m[0], talk.TalkFileMessage):
                break
        m_t: talk.TalkFileMessage = m[0]  # noqa
        fs_node = m_t.to_fs_node()
        assert await nc_second_user.files.download(fs_node) == b"12345"
        assert m_t.reference_id == reference_id
        assert fs_node.is_dir is False
        # test with directory
        directory = await anc_client.files.by_path("/test_dir/")
        r, reference_id = await anc_client.talk.send_file(directory, conversation)
        assert isinstance(reference_id, str)
        assert isinstance(r, files.Share)
        for _ in range(10):
            m = await nc_second_user.talk.receive_messages(conversation, limit=1)
            if m and m[0].reference_id == reference_id:
                break
        m_t: talk.TalkFileMessage = m[0]  # noqa
        assert m_t.reference_id == reference_id
        fs_node = m_t.to_fs_node()
        assert fs_node.is_dir is True
    finally:
        await anc_client.talk.leave_conversation(conversation.token)
