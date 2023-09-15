Talk Bot App with Transformers
==============================

`Transformers provides thousands of pretrained models to perform tasks on different modalities such as text, vision, and audio.`

In this article, we'll demonstrate how straightforward it is to leverage the extensive capabilities
of the `Transformers <https://github.com/huggingface/transformers>`_ library in your Nextcloud application.

Specifically, we'll cover:

* Setting the cache path for the Transformers library
* Downloading AI models during the application initialization step
* Receiving messages from Nextcloud Talk Chat and sending them to a language model
* Sending the language model's reply back to the Nextcloud Talk Chat

Packaging the Application
"""""""""""""""""""""""""

Firstly, let's touch upon the somewhat mundane topic of application packaging.

For this example, we've chosen Debian as the base image because it simplifies the installation of required Python packages.

.. code-block::

    FROM python:3.11-bookworm


While Alpine might be a better choice in some situations, that's not the focus of this example.

.. note:: The selection of a suitable base image for an application is a complex topic that merits its own in-depth discussion.

Requirements
""""""""""""

.. literalinclude:: ../examples/as_app/talk_bot_ai/requirements.txt

We opt for the latest version of the Transformers library.
Because the example was developed on a Mac, we ended up using Torchvision.

`If you're working solely with Nvidia, you're free to use TensorFlow instead of PyTorch.`

Next, we integrate the latest version of `nc_py_api` to minimize code redundancy and focus on the application's logic.

Model Downloading
"""""""""""""""""

**When Should We Download the Language Model?**

Although the example uses the smallest model available, weighing in at 300 megabytes, it's common knowledge that larger language models can be substantially bigger.
Downloading such models should not begin when a processing request is already received.

So we have two options:

* Heartbeat
* enabled_handler

This can't be accomplished in the **app on/off handler** as Nextcloud expects an immediate response regarding the app's operability.

Thus, we place the model downloading within the Heartbeat:

.. code-block::

    # Thread that performs model download.
    def download_models():
        pipeline("text2text-generation", model=MODEL_NAME)  # this will download model


    def heartbeat_handler() -> str:
        global MODEL_INIT_THREAD
        print("heartbeat_handler: called")  # for debug
        # if it is the first heartbeat, then start background thread to download a model
        if MODEL_INIT_THREAD is None:
            MODEL_INIT_THREAD = Thread(target=download_models)
            MODEL_INIT_THREAD.start()
            print("heartbeat_handler: started initialization thread")  # for debug
        # if thread is finished then we will have "ok" in response, and AppAPI will consider that program is ready.
        r = "init" if MODEL_INIT_THREAD.is_alive() else "ok"
        print(f"heartbeat_handler: result={r}")  # for debug
        return r


    @APP.on_event("startup")
    def initialization():
        # Provide our custom **heartbeat_handler** to set_handlers
        set_handlers(APP, enabled_handler, heartbeat_handler)


.. note:: While this may not be the most ideal way to download models, it remains a viable method.
    In the future, a more efficient wrapper for model downloading is planned to make the process even more convenient.

Model Storage
"""""""""""""

By default, models will be downloaded to a directory that's removed when updating the app.
o persistently store the models even after updates, add the following line to your code:

.. code-block::

    from nc_py_api.ex_app import persist_transformers_cache  # noqa # isort:skip

This will set ``TRANSFORMERS_CACHE`` environment variable to point to the application persistent storage.
Import of this **must be** on top before importing any code that perform the import of the ``transformers`` library.

And that is all, ``transformers`` will automatically download all
models you use to the **Application Persistent Storage** and AppAPI will keep it between updates.

Working with Language Models
""""""""""""""""""""""""""""

Finally, we arrive at the core aspect of the application, where we interact with the **Language Model**:

.. code-block::

    def ai_talk_bot_process_request(message: talk_bot.TalkBotMessage):
        # Process only messages started with **@ai**
        r = re.search(r"@ai\s(.*)", message.object_content["message"], re.IGNORECASE)
        if r is None:
            return
        model = pipeline("text2text-generation", model=MODEL_NAME)
        # Pass all text after **@ai** we to the Language model.
        response_text = model(r.group(1), max_length=64, do_sample=True)[0]["generated_text"]
        AI_BOT.send_message(response_text, message)


Simply put, the AI logic is just two lines of code when using Transformers, which is incredibly efficient and cool.

Messages from the AI model are then sent back to Talk Chat as you would expect from a typical chatbot.

That's it for now! Stay tuned—this is merely the start of an exciting journey into the integration of AI and chat functionality in Nextcloud.
