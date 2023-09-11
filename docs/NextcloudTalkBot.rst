Nextcloud Talk Bot API in Applications
======================================

The AppAPI is an excellent choice for developing and deploying bots for Nextcloud Talk.

Bots for Nextcloud Talk, in essence, don't differ significantly from regular external applications.
The functionality of an external application can include just the bot or provide additional functionalities as well.

Let's consider a simple example of how to transform the `skeleton` of an external application into a Nextcloud Talk bot.

The first step is to add the **TALK_BOT** and **TALK** scopes to your `info.xml` file:

.. code-block:: xml

    <scopes>
        <required>
            <value>TALK</value>
            <value>TALK_BOT</value>
        </required>
        <optional>
        </optional>
    </scopes>

The TALK_BOT scope enables your application to register the bot within the Nextcloud system, while the TALK scope permits access to Talk's endpoints.

In the global **enabled_handler**, you should include a call to your bot's enabled_handler, as shown in the bot example:

.. code-block:: python

    def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
        try:
            CURRENCY_BOT.enabled_handler(enabled, nc)  # registering/unregistering the bot's stuff.
        except Exception as e:
            return str(e)
        return ""

Afterward, using FastAPI, you can define endpoints that will be invoked by Talk:

.. code-block:: python

    @APP.post("/currency_talk_bot")
    async def currency_talk_bot(
        message: Annotated[talk_bot.TalkBotMessage, Depends(talk_bot_app)],
        background_tasks: BackgroundTasks,
    ):
        return requests.Response()

.. note::
    You must include to each endpoint your bot provides the **Depends(talk_bot_app)**.
    **message: Annotated[talk_bot.TalkBotMessage, Depends(talk_bot_app)]**

Depending on **talk_bot_app** serves as an automatic authentication handler for messages from the cloud, which returns the received message from Nextcloud upon successful authentication.

Additionally, if your bot can provide quick and fixed execution times, you may not need to create background tasks.
However, in most cases, it's recommended to segregate functionality and perform operations in the background, while promptly returning an empty response to Nextcloud.

An application can implement multiple bots concurrently, but each bot's endpoints must be unique.

All authentication is facilitated by the Python SDK, ensuring you needn't concern yourself with anything other than writing useful functionality.

Currently, bots have access only to three methods:

* :py:meth:`~nc_py_api.talk_bot.TalkBot.send_message`
* :py:meth:`~nc_py_api.talk_bot.TalkBot.react_to_message`
* :py:meth:`~nc_py_api.talk_bot.TalkBot.delete_reaction`

.. note:: **The usage of system application functionality for user impersonation in bot development is strongly discouraged**.
    All bot messages should only be sent using the ``send_message`` method!

All other rules and algorithms remain consistent with regular external applications.

Full source of bot example can be found here:
`TalkBot <https://github.com/cloud-py-api/nc_py_api/blob/main/examples/as_app/talk_bot/src/main.py>`_

Wishing success with your Nextcloud bot integration! May the force be with you!
