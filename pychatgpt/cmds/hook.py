import json
import websocket
import pytz
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

    def on_message(self, ws, message):
        LOG.info(message)
        msg = json.loads(message)
        msg_type = msg['type']
        handler: BaseHandler = handlers.find_handler(msg_type, 'winwx')
        if not handler:
            LOG.warning(f"Unknown message type: {msg_type}")
            return
        handler(self.me, self.reply_fn).handle(msg)

    def reply_fn(self, content, to):
        LOG.info(f'Replying to {to}: {content}')
        self.ws.send(json.dumps({
            'id': self.now(),
            'type': 555,
            'roomid': 'null',
            'content': content,
            'wxid': to,
            'nickname': 'null',
            'ext': 'null'
        }))
        LOG.info(f'Replied to {to}.')

    def on_error(self, ws, error):
        LOG.error(error)

    def on_close(self, ws):
        LOG.info("### closed ###")

    def now(self):
        utc = datetime.utcnow()
        tz = pytz.timezone('Asia/Shanghai')
        now = utc.replace(tzinfo=pytz.utc).astimezone(tz)
        return now.strftime('%Y%m%d%H%M%S')

    def on_open(self, ws):
        LOG.info("### opened ###")
        self.ws = ws
        ws.send(json.dumps({
            'id': self.now(),
            'type': 5000,
            'roomid': 'null',
            'content': 'null',
            'wxid': 'null',
            'nickname': 'null',
            'ext': 'null'
        }))

    def start(self):
        ws = websocket.WebSocketApp(CONF.hook.url,
                                    on_open=self.on_open,
                                    on_close=self.on_close,
                                    on_error=self.on_error,
                                    on_message=self.on_message)
        ws.run_forever()


if __name__ == "__main__":
    hook = Hook()
    hook.start()
