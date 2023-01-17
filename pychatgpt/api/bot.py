# Copyright 2022 EasyStack, Inc.

from contextlib import contextmanager
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import PlainTextResponse
from oslo_log import log as logging
from pydantic import BaseModel

from pychatgpt.clients import chatgpt
from pychatgpt.exception import PyChatGPTException

app = FastAPI()
LOG = logging.getLogger(__name__)

cc = None


def start_chatgpt():
    cc = chatgpt.ChatgptClient()
    cc.startup()
    cc.refresh_session()
    return cc


@contextmanager
def ensure_chatgpt():
    try:
        global cc
        if cc is None:
            cc = start_chatgpt()
        yield cc
    finally:
        if cc is None:
            raise PyChatGPTException("Chatgpt client is not started.")


class Chat(BaseModel):
    message: str


@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    LOG.error(f"Exception: {exc}")
    return PlainTextResponse(str(exc), status_code=500)


@app.exception_handler(PyChatGPTException)
async def exception_handler(request: Request, exc: PyChatGPTException):
    LOG.error(f"Exception: {exc}")
    return PlainTextResponse(str(exc), status_code=500)


@app.post("/chat")
async def chat(body: Chat):
    LOG.info(f"Create chat: {body}.")
    with ensure_chatgpt() as cc:
        resp = cc.ask(body.message)
        return resp
