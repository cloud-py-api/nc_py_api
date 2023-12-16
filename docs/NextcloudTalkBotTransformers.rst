Talk Bot App with Transformers
==============================

`Transformers provides thousands of pretrained models to perform tasks on different modalities such as text, vision, and audio.`

In this article, we'll demonstrate how straightforward it is to leverage the extensive capabilities
of the `Transformers <https://github.com/huggingface/transformers>`_ library in your Nextcloud application.

Specifically, we'll cover:

* Setting the models cache path for the Transformers library
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

`You're free to use TensorFlow instead of PyTorch.`

Next, we integrate the latest version of `nc_py_api` to minimize code redundancy and focus on the application's logic.

Prepare of Language Model
"""""""""""""""""""""""""

.. code-block::

    MODEL_NAME = "MBZUAI/LaMini-Flan-T5-77M"

We specify the model name globally so that we can easily change the model name if necessary.

**When Should We Download the Language Model?**

To make process of initializing applications more robust, separate logic was introduced, with an ``/init`` endpoint.

This library also provides an additional functionality over this endpoint for easy downloading of models from the `huggingface <https://huggingface.co>`_.

.. code-block::

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        set_handlers(APP, enabled_handler, models_to_fetch={MODEL_NAME:{}})
        yield

This will automatically download models specified in ``models_to_fetch`` parameter to the application persistent storage.

If you want write your own logic, you can always pass your own defined ``init_handler`` callback to ``set_handlers``.

Working with Language Models
""""""""""""""""""""""""""""

Finally, we arrive at the core aspect of the application, where we interact with the **Language Model**:

.. code-block::

    def ai_talk_bot_process_request(message: talk_bot.TalkBotMessage):
        # Process only messages started with "@ai"
        r = re.search(r"@ai\s(.*)", message.object_content["message"], re.IGNORECASE)
        if r is None:
            return
        model = pipeline(
            "text2text-generation",
            model=snapshot_download(MODEL_NAME, local_files_only=True, cache_dir=persistent_storage()),
        )
        # Pass all text after "@ai" we to the Language model.
        response_text = model(r.group(1), max_length=64, do_sample=True)[0]["generated_text"]
        AI_BOT.send_message(response_text, message)


Simply put, AI logic is a few lines of code when using Transformers, which is incredibly efficient and cool.

Messages from the AI model are then sent back to Talk Chat as you would expect from a typical chatbot.

`Full source code is here <https://github.com/cloud-py-api/nc_py_api/tree/main/examples/as_app/talk_bot_ai>`_

That's it for now! Stay tuned—this is merely the start of an exciting journey into the integration of AI and chat functionality in Nextcloud.
