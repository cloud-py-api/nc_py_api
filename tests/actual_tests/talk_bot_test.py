from os import environ

import httpx
import pytest

from nc_py_api import talk, talk_bot


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


@pytest.mark.asyncio(scope="session")
@pytest.mark.require_nc(major=27, minor=1)
async def test_register_unregister_talk_bot_async(anc_app):
    if await anc_app.talk.bots_available is False:
        pytest.skip("Need Talk bots support")
    await anc_app.unregister_talk_bot("/talk_bot_coverage")
    list_of_bots = await anc_app.talk.list_bots()
    await anc_app.register_talk_bot("/talk_bot_coverage", "Coverage bot", "Desc")
    assert len(list_of_bots) + 1 == len(await anc_app.talk.list_bots())
    await anc_app.register_talk_bot("/talk_bot_coverage", "Coverage bot", "Desc")
    assert len(list_of_bots) + 1 == len(await anc_app.talk.list_bots())
    assert await anc_app.unregister_talk_bot("/talk_bot_coverage") is True
    assert len(list_of_bots) == len(await anc_app.talk.list_bots())
    assert await anc_app.unregister_talk_bot("/talk_bot_coverage") is False
    assert len(list_of_bots) == len(await anc_app.talk.list_bots())


def _test_list_bots(registered_bot: talk.BotInfo):
    assert isinstance(registered_bot.bot_id, int)
    assert registered_bot.url.find("/some_url") != -1
    assert registered_bot.description == "some desc"
    assert registered_bot.state == 1
    assert not registered_bot.error_count
    assert registered_bot.last_error_date == 0
    assert registered_bot.last_error_message is None
    assert isinstance(registered_bot.url_hash, str)


@pytest.mark.require_nc(major=27, minor=1)
def test_list_bots(nc, nc_app):
    if nc_app.talk.bots_available is False:
        pytest.skip("Need Talk bots support")
    nc_app.register_talk_bot("/some_url", "some bot name", "some desc")
    registered_bot = next(i for i in nc.talk.list_bots() if i.bot_name == "some bot name")
    _test_list_bots(registered_bot)
    conversation = nc.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        conversation_bots = nc.talk.conversation_list_bots(conversation)
        assert conversation_bots
        assert str(conversation_bots[0]).find("name=") != -1
    finally:
        nc.talk.delete_conversation(conversation.token)


@pytest.mark.asyncio(scope="session")
@pytest.mark.require_nc(major=27, minor=1)
async def test_list_bots_async(anc, anc_app):
    if await anc_app.talk.bots_available is False:
        pytest.skip("Need Talk bots support")
    await anc_app.register_talk_bot("/some_url", "some bot name", "some desc")
    registered_bot = next(i for i in await anc.talk.list_bots() if i.bot_name == "some bot name")
    _test_list_bots(registered_bot)
    conversation = await anc.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        conversation_bots = await anc.talk.conversation_list_bots(conversation)
        assert conversation_bots
        assert str(conversation_bots[0]).find("name=") != -1
    finally:
        await anc.talk.delete_conversation(conversation.token)


# We're testing the async bot first, since it doesn't have invalid auth tests that triggers brute-force protection.
@pytest.mark.asyncio(scope="session")
@pytest.mark.skipif(environ.get("CI", None) is None, reason="run only on GitHub")
@pytest.mark.require_nc(major=27, minor=1)
async def test_chat_bot_receive_message_async(anc_app):
    if await anc_app.talk.bots_available is False:
        pytest.skip("Need Talk bots support")
    httpx.delete(f"{'http'}://{environ.get('APP_HOST', '127.0.0.1')}:{environ['APP_PORT']}/reset_bot_secret")
    talk_bot_inst = talk_bot.AsyncTalkBot("/talk_bot_coverage", "Coverage bot", "Desc")
    await talk_bot_inst.enabled_handler(True, anc_app)
    conversation = await anc_app.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        coverage_bot = next(i for i in await anc_app.talk.list_bots() if i.url.endswith("/talk_bot_coverage"))
        c_bot_info = next(
            i for i in await anc_app.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id
        )
        assert c_bot_info.state == 0
        await anc_app.talk.enable_bot(conversation, coverage_bot)
        c_bot_info = next(
            i for i in await anc_app.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id
        )
        assert c_bot_info.state == 1
        with pytest.raises(ValueError):
            await anc_app.talk.send_message("Here are the msg!")
        await anc_app.talk.send_message("Here are the msg!", conversation)
        msg_from_bot = None
        for _ in range(40):
            messages = await anc_app.talk.receive_messages(conversation, look_in_future=True, timeout=1)
            if messages[-1].message == "Hello from bot!":
                msg_from_bot = messages[-1]
                break
        assert msg_from_bot
        c_bot_info = next(
            i for i in await anc_app.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id
        )
        assert c_bot_info.state == 1
        await anc_app.talk.disable_bot(conversation, coverage_bot)
        c_bot_info = next(
            i for i in await anc_app.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id
        )
        assert c_bot_info.state == 0
    finally:
        await anc_app.talk.delete_conversation(conversation.token)
        await talk_bot_inst.enabled_handler(False, anc_app)
    talk_bot_inst.callback_url = "invalid_url"
    with pytest.raises(RuntimeError):
        await talk_bot_inst.send_message("message", 999999, token="sometoken")


@pytest.mark.skipif(environ.get("CI", None) is None, reason="run only on GitHub")
@pytest.mark.require_nc(major=27, minor=1)
def test_chat_bot_receive_message(nc_app):
    if nc_app.talk.bots_available is False:
        pytest.skip("Need Talk bots support")
    httpx.delete(f"{'http'}://{environ.get('APP_HOST', '127.0.0.1')}:{environ['APP_PORT']}/reset_bot_secret")
    talk_bot_inst = talk_bot.TalkBot("/talk_bot_coverage", "Coverage bot", "Desc")
    talk_bot_inst.enabled_handler(True, nc_app)
    conversation = nc_app.talk.create_conversation(talk.ConversationType.GROUP, "admin")
    try:
        coverage_bot = next(i for i in nc_app.talk.list_bots() if i.url.endswith("/talk_bot_coverage"))
        c_bot_info = next(
            i for i in nc_app.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id
        )
        assert c_bot_info.state == 0
        nc_app.talk.enable_bot(conversation, coverage_bot)
        c_bot_info = next(
            i for i in nc_app.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id
        )
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
        c_bot_info = next(
            i for i in nc_app.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id
        )
        assert c_bot_info.state == 1
        nc_app.talk.disable_bot(conversation, coverage_bot)
        c_bot_info = next(
            i for i in nc_app.talk.conversation_list_bots(conversation) if i.bot_id == coverage_bot.bot_id
        )
        assert c_bot_info.state == 0
    finally:
        nc_app.talk.delete_conversation(conversation.token)
        talk_bot_inst.enabled_handler(False, nc_app)
    talk_bot_inst.callback_url = "invalid_url"
    with pytest.raises(RuntimeError):
        talk_bot_inst.send_message("message", 999999, token="sometoken")
