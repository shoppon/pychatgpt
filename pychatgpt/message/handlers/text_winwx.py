import asyncio

from oslo_config import cfg
from oslo_log import log as logging

from pychatgpt.message.handlers.base import BaseHandler
from pychatgpt.models.chatgpt import Conversation
from pychatgpt.models.winwx import Message
from pychatgpt.wechat import bot

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

# TODO(xp): use a better way to store conversation
CONVERSATIONS = {}


class TextHandler(BaseHandler):
    msg_type = 1
    wx_type = 'winwx'

    async def handle(self, msg: dict) -> None:
        msg = Message(**msg)
        try:
            from_user = msg.id1
            to_user = msg.wxid
            if msg.content.startswith('#hc'):
                await self.reply_fn(content=msg.content[3:].strip(),
                                    to=to_user)
                return

            if not msg.content.startswith(CONF.wechat.prefix):
                return

            conv: Conversation = CONVERSATIONS.get(to_user)
            if conv is None:
                LOG.info(f'Creating new conversation for {to_user}.')
                conv = Conversation(to=to_user)
                CONVERSATIONS[to_user] = conv

            keyword = msg.content[len(CONF.wechat.prefix):].strip()
            keyword_handle_fn = getattr(self, f'handle_{keyword}', None)
            if callable(keyword_handle_fn):
                keyword_handle_fn(conv, from_user)
                return

            if not conv.enabled:
                LOG.warning(f'Conversation {to_user} is disabled.')
                return

            # asyncronous reply
            LOG.info(f'Invoking chatgpt with conversation: {conv}.')
            asyncio.create_task(self.chatgpt_reply(keyword, conv))
        except Exception as err:
            LOG.error(f'Chatgpt error: {err}')

    async def chatgpt_reply(self, content, conv: Conversation):
        try:
            msg = f'「{content}」\n- - - - - - - - - - - - - - -\n'
            with bot.ensure_chatgpt() as chatgpt:
                try:
                    reply = chatgpt.ask(content, conv)
                except Exception as err:
                    LOG.error(f'Chatgpt error: {err}')
                    msg += 'An error occurred, please try again later.'
                    await self.reply_fn(content=msg, to=conv.to)
                else:
                    LOG.info(f'Chatgpt reply: {reply}.')
                    msg += reply

                    # store messages
                    conv.messages.append({
                        'role': 'user',
                        'content': content,
                    })
                    conv.messages.append({
                        'role': 'assistant',
                        'content': reply,
                    })

                    await self.reply_fn(msg, to=conv.to)
        except Exception as err:
            await self.reply_fn(content=(f'{msg}Failed to start AI, '
                                         'please try again later.'),
                                to=conv.to)
            LOG.error(f'Chatgpt error: {err}')

    def handle_start(self, conv: Conversation, from_user: str):
        # from_user is empty when the message is sent by myself
        if from_user != '':
            return
        LOG.info(f'Starting conversation for {conv.to}.')
        conv.enabled = True

    def handle_stop(self, conv: Conversation, from_user: str):
        # from_user is empty when the message is sent by myself
        if from_user != '':
            return
        LOG.info(f'Stopping conversation for {conv.to}.')
        conv.enabled = False

    def handle_clear(self, conv: Conversation, from_user: str):
        LOG.info(f'Clearing conversation for {conv.to}, from {from_user}.')
        conv.messages = []
