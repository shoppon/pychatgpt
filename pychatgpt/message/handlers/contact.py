from oslo_log import log as logging

from pychatgpt.message.handlers.base import BaseHandler
from pychatgpt.models.winwx import Contact

LOG = logging.getLogger(__name__)

CONTACTS = {}


class ContactHandler(BaseHandler):
    msg_type = 5000
    wx_type = 'winwx'

    def handle(self, msg) -> None:
        LOG.info(f'Hanlding contact message: {msg}')
        for c in msg['content']:
            contact = Contact(**c)
            CONTACTS[contact.wxid] = contact
