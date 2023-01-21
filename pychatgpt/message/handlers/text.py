import asyncio

from oslo_log import log as logging

from pychatgpt.api import bot
from pychatgpt.message.handlers.base import BaseHandler
from pychatgpt.models.chatgpt import Conversation

LOG = logging.getLogger(__name__)


class TextHandler(BaseHandler):
    msg_type = 1

    def __init__(self, me: str, reply_fn: callable) -> None:
        super().__init__(me, reply_fn)
        self.conversations = {}

    def handle(self, msg) -> None:
        if msg.group_userid:
            LOG.info(f'Receive text from {msg.from_username}/'
                     f'{msg.group_username}, '
                     f'content: {msg.content}')
        else:
            LOG.info(f'Receive text from {msg.from_username} '
                     f'to {msg.to_username}, '
                     f'content: {msg.content}')

        try:
            to = msg.from_userid if msg.to_userid == self.me else msg.to_userid
            if msg.content.startswith('#hc '):
                self.reply_fn(content=msg.content[4:], to=to)

            if not msg.content.startswith('#ai '):
                return

            conv: Conversation = self.conversations.get(to)
            if not conv:
                conv = Conversation(c_id=None, p_id=None, to=to)
                self.conversations[to] = conv
            # asyncronous reply
            asyncio.create_task(self.chatgpt_reply(msg.content[4:], conv))
        except Exception as err:
            LOG.error(f'Chatgpt error: {err}')

    async def chatgpt_reply(self, content, conv: Conversation):
        try:
            with bot.ensure_chatgpt() as chatgpt:
                reply = chatgpt.ask(content, conv.c_id, conv.p_id)
                conv.c_id = reply['conversation_id']
                conv.p_id = reply['parent_id']
                self.reply_fn(content=reply['message'], to=conv.to)
        except Exception as err:
            LOG.error(f'Chatgpt error: {err}')
