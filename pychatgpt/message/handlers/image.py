from oslo_log import log as logging

from pychatgpt.message.handlers.base import BaseHandler

LOG = logging.getLogger(__name__)


class ImageHandler(BaseHandler):
    msg_type = 3

    def handle(self, msg) -> None:
        LOG.info(f'Receive image from {msg.from_username}.')
