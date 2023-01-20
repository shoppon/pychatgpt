import asyncio
from contextlib import contextmanager

from oslo_log import log as logging

from pychatgpt.api import app
from pychatgpt.clients.wechat import WechatClient
from pychatgpt.exception import PyChatGPTException

APP_ID = "wx782c26e4c19acffb"
wc = None

LOG = logging.getLogger(__name__)


@contextmanager
def ensure_wechat():
    try:
        global wc
        if wc is None:
            wc = WechatClient(APP_ID, "zh_CN")
        yield wc
    finally:
        if wc is None:
            raise PyChatGPTException("Wechat client is not started.")


@app.get("/wechat/start")
async def start():
    with ensure_wechat() as wc:
        if wc.working:
            LOG.info("Wechat client is already working.")
            return {}

        wc.should_stop = False

        LOG.info("Starting wechat client.")
        uuid = wc.get_login_uuid()
        uri = wc.wait_for_login(uuid, tip=0)
        request, cred = wc.login(uri)
        session = wc.webwx_init(uri, request, cred)
        wc.webwx_status_notify(uri, request, session, cred)
        contacts = wc.read_contacts(uri, request, cred)
        wc.read_batch_contacts(contacts, uri, request, cred)
        LOG.info("Creating task for wechat client.")
        asyncio.create_task(wc.listen(uri, request, session, cred, contacts))
        return {}


@app.get("/wechat/stop")
def stop():
    with ensure_wechat() as wc:
        wc.stop()
        LOG.info("Wechat client is stopped.")


@app.get("/wechat/health")
def health():
    with ensure_wechat() as wc:
        if wc.working:
            return {}
        else:
            raise PyChatGPTException("Wechat client is not working.")
