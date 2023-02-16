import asyncio
import json
import websockets
import pytz
import sys
from datetime import datetime
from oslo_log import log as logging

from pychatgpt import config  # noqa
from pychatgpt.message import handlers
from pychatgpt.message.handlers.base import BaseHandler

CONF = config.CONF
logging.register_options(CONF)
logging.setup(CONF, "chatgpt")
LOG = logging.getLogger(__name__)


class Hook:
    def __init__(self):
        self.ws = None
        self.me = None

    async def on_message(self, message):
        LOG.info(message)
        msg = json.loads(message)
        msg_type = msg['type']
        handler: BaseHandler = handlers.find_handler(msg_type, 'winwx')
        if not handler:
            LOG.warning(f"Unknown message type: {msg_type}")
            return
        await handler(self.me, self.reply_fn).handle(msg)

    async def reply_fn(self, content, to):
        LOG.info(f'Replying to {to}: {content}')
        await self.ws.send(json.dumps({
            'id': self.now(),
            'type': 555,
            'roomid': 'null',
            'content': content,
            'wxid': to,
            'nickname': 'null',
            'ext': 'null'
        }))
        LOG.info(f'Replied to {to}.')

    def now(self):
        utc = datetime.utcnow()
        tz = pytz.timezone('Asia/Shanghai')
        now = utc.replace(tzinfo=pytz.utc).astimezone(tz)
        return now.strftime('%Y%m%d%H%M%S')

    async def on_open(self, ws):
        LOG.info("### opened ###")
        self.ws = ws
        await ws.send(json.dumps({
            'id': self.now(),
            'type': 5000,
            'roomid': 'null',
            'content': 'null',
            'wxid': 'null',
            'nickname': 'null',
            'ext': 'null'
        }))

    async def listen(self):
        async with websockets.connect(CONF.hook.url) as websocket:
            self.ws = websocket
            await self.on_open(websocket)
            while True:
                message = await websocket.recv()
                await self.on_message(message)


def main():
    CONF(sys.argv[1:], project='chatgpt')
    hook = Hook()
    asyncio.get_event_loop().run_until_complete(hook.listen())


if __name__ == "__main__":
    main()
