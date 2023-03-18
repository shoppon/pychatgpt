from oslo_log import log as logging

from pychatgpt.message.handlers.text_webwx import TextHandler


LOG = logging.getLogger(__name__)


class AtTextHandler(TextHandler):
    msg_type = 49
    wx_type = 'winwx'

    async def handle(self, msg) -> None:
        LOG.info(f'Receive image from {msg}.')
