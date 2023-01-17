from contextlib import contextmanager
from oslo_log import log as logging
from pydantic import BaseModel

from pychatgpt.api import app
from pychatgpt.clients import chatgpt
from pychatgpt.exception import PyChatGPTException

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


@app.post("/chat")
async def chat(body: Chat):
    LOG.info(f"Create chat: {body}.")
    with ensure_chatgpt() as cc:
        resp = cc.ask(body.message)
        return resp
