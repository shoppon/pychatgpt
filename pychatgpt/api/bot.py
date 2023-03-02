"""bot api."""
from contextlib import contextmanager

from oslo_config import cfg
from oslo_log import log as logging

from pychatgpt.clients import openai
from pychatgpt.exception import PyChatGPTException

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

CC = None


def start_chatgpt():
    return openai.OpenAIClient(CONF.openai.api_key)


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
