from oslo_log import log as logging

from pychatgpt.message.handlers.base import BaseHandler

LOG = logging.getLogger(__name__)

CONTACTS = {}


class HeartbeatHandler(BaseHandler):
    msg_type = 5005
    wx_type = 'winwx'

    async def handle(self, msg) -> None:
        LOG.info(f'Receive heartbeat message: {msg}.')
