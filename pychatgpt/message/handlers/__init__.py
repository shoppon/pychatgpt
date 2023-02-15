from oslo_log import log as logging

from pychatgpt import utils
from pychatgpt.message.handlers.base import BaseHandler
from pychatgpt.message.handlers.contact import ContactHandler
from pychatgpt.message.handlers.image import ImageHandler
from pychatgpt.message.handlers.text_webwx import TextHandler
from pychatgpt.message.handlers.text_winwx import TextHandler as WinwxTextHandler
from pychatgpt.message.handlers.video import VideoHandler
from pychatgpt.message.handlers.voice import VoiceHandler

LOG = logging.getLogger(__name__)


def find_handler(msg_type, wx_type) -> BaseHandler:
    for handler in utils.walk_class_hierarchy(BaseHandler):
        if handler.msg_type == msg_type and handler.wx_type == wx_type:
            return handler
    LOG.warning(f"Unknown message type: {msg_type}")
