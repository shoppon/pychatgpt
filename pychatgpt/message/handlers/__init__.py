from oslo_log import log as logging

from pychatgpt import utils
from pychatgpt.message.handlers.base import BaseHandler
from pychatgpt.message.handlers.at_text import AtTextHandler  # noqa
from pychatgpt.message.handlers.contact import ContactHandler  # noqa
from pychatgpt.message.handlers.heartbeat import HeartbeatHandler  # noqa
from pychatgpt.message.handlers.image import ImageHandler  # noqa
from pychatgpt.message.handlers.text_webwx import TextHandler  # noqa
from pychatgpt.message.handlers.text_winwx import TextHandler as WinwxTextHandler  # noqa
from pychatgpt.message.handlers.video import VideoHandler  # noqa
from pychatgpt.message.handlers.voice import VoiceHandler  # noqa

LOG = logging.getLogger(__name__)


def find_handler(msg_type, wx_type) -> BaseHandler:
    for handler in utils.walk_class_hierarchy(BaseHandler):
        if handler.msg_type == msg_type and handler.wx_type == wx_type:
            return handler
    LOG.warning(f"Unknown message type: {msg_type}")
