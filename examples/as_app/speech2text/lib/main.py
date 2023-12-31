"""Use the simplest model to just test speech recognition.

Example is not production ready, as probably in production app we want running requests in subprocesses with timeout or
run multiply workers to process requests simultaneously.
"""

import os
import tempfile
import typing
from contextlib import asynccontextmanager

import torch
from fastapi import Depends, FastAPI, UploadFile, responses
from huggingface_hub import snapshot_download
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from nc_py_api import NextcloudApp
from nc_py_api.ex_app import nc_app, persistent_storage, run_app, set_handlers

MODEL_NAME = "distil-whisper/distil-small.en"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    set_handlers(APP, enabled_handler, models_to_fetch={MODEL_NAME: {"ignore_patterns": ["*.bin", "*onnx*"]}})
    yield


APP = FastAPI(lifespan=lifespan)


@APP.post("/distil_whisper_small")
async def distil_whisper_small(
    _nc: typing.Annotated[NextcloudApp, Depends(nc_app)],
    data: UploadFile,
    max_execution_time: float = 0,
):
    print(max_execution_time)
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        snapshot_download(
            MODEL_NAME,
            local_files_only=True,
            cache_dir=persistent_storage(),
        ),
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
        use_safetensors=True,
    ).to("cpu")

    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        torch_dtype=torch.float32,
        device="cpu",
    )
    _, file_extension = os.path.splitext(data.filename)
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=f"{file_extension}") as tmp:
        tmp.write(await data.read())
        result = pipe(tmp.name)
    return responses.Response(content=result["text"])


# async
def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    print(f"enabled={enabled}")
    if enabled is True:
        nc.providers.speech_to_text.register("distil_whisper_small", "DistilWhisperSmall", "/distil_whisper_small")
    else:
        nc.providers.speech_to_text.unregister("distil_whisper_small")
    return ""


if __name__ == "__main__":
    run_app("main:APP", log_level="trace")
