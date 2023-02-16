from oslo_log import log as logging

from pychatgpt.message.handlers.base import BaseHandler

LOG = logging.getLogger(__name__)


class VideoHandler(BaseHandler):
    msg_type = 43

    async def handle(self, msg) -> None:
        LOG.info(f'Receive video from {msg.from_username}')
