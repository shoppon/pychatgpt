from oslo_log import log as logging

from pychatgpt.message.handlers.base import BaseHandler

LOG = logging.getLogger(__name__)


class VoiceHandler(BaseHandler):
    msg_type = 34

    async def handle(self, msg) -> None:
        LOG.info(f'Receive voice from {msg.from_username}.')
