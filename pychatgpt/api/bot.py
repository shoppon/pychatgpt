"""bot api."""
from contextlib import contextmanager

from oslo_config import cfg
from oslo_log import log as logging
from pydantic import BaseModel

from pychatgpt.api import app
from pychatgpt.clients import chatgpt
from pychatgpt.clients import chrome
from pychatgpt.clients import google
from pychatgpt.exception import PyChatGPTException

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

CC = None


def start_chatgpt():

    with chrome.Chrome(proxy=CONF.tls_client.http_proxy) as chrome_client:
        session_token = google.login(chrome_client.driver,
                                     CONF.google.username,
                                     CONF.google.password)
    chat_client = chatgpt.ChatgptClient(session_token)
    chat_client.startup()
    chat_client.refresh_session()
    return chat_client


@contextmanager
def ensure_chatgpt():
    try:
        global CC
        if CC is None:
            CC = start_chatgpt()
        yield CC
    finally:
        if CC is None:
            raise PyChatGPTException("Chatgpt client is not started.")


class Chat(BaseModel):
    message: str


@app.post("/chat")
async def chat(body: Chat):
    LOG.info(f"Create chat: {body}.")
    with ensure_chatgpt() as cc:
        resp = cc.ask(body.message)
        return resp
