from oslo_log import log as logging

from pychatgpt import utils
from pychatgpt.message.handlers.base import BaseHandler
from pychatgpt.message.handlers.image import ImageHandler
from pychatgpt.message.handlers.text import TextHandler
from pychatgpt.message.handlers.video import VideoHandler
from pychatgpt.message.handlers.voice import VoiceHandler

LOG = logging.getLogger(__name__)


def find_handler(msg_type) -> BaseHandler:
    for handler in utils.walk_class_hierarchy(BaseHandler):
        if handler.msg_type == msg_type:
            return handler
    LOG.warning(f"Unknown message type: {msg_type}")
