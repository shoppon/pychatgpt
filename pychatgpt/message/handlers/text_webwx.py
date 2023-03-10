import asyncio

from oslo_config import cfg
from oslo_log import log as logging

from pychatgpt.message.handlers.base import BaseHandler
from pychatgpt.models.chatgpt import Conversation
from pychatgpt.wechat import bot

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

# TODO(xp): use a better way to store conversation
CONVERSATIONS = {}


class TextHandler(BaseHandler):
    msg_type = 1
    wx_type = 'webwx'

    async def handle(self, msg) -> None:
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
            if msg.content.startswith('#hc'):
                self.reply_fn(content=msg.content[3:].strip(), to=to)

            if not msg.content.startswith(CONF.wechat.prefix):
                return

            conv: Conversation = CONVERSATIONS.get(to)
            if conv is None:
                LOG.info(f'Creating new conversation for {to}.')
                conv = Conversation(to=to)
                CONVERSATIONS[to] = conv
            # asyncronous reply
            LOG.info(f'Invoking chatgpt with conversation: {conv}.')
            asyncio.create_task(self.chatgpt_reply(msg.content[3:].strip(),
                                                   conv))
        except Exception as err:
            LOG.error(f'Chatgpt error: {err}')

    async def chatgpt_reply(self, content, conv: Conversation):
        try:
            msg = f'「{content}」\n- - - - - - - - - - - - - - - - - - -\n'
            with bot.ensure_chatgpt() as chatgpt:
                try:
                    reply = chatgpt.ask(content, conv)
                except Exception as err:
                    LOG.error(f'Chatgpt error: {err}')
                    msg += 'An error occurred, please try again later.'
                    self.reply_fn(content=msg, to=conv.to)
                else:
                    LOG.info(f'Chatgpt reply: {reply}.')
                    msg += reply
                    self.reply_fn(msg, to=conv.to)
        except Exception as err:
            LOG.error(f'Chatgpt error: {err}')
