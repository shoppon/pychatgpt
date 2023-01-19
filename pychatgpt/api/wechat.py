import asyncio
from contextlib import contextmanager

from pychatgpt.api import app
from pychatgpt.clients.wechat import WechatClient
from pychatgpt.exception import PyChatGPTException

APP_ID = "wx782c26e4c19acffb"
wc = None


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


@app.get("/wechat/uuid")
def get_uuid():
    with ensure_wechat() as wc:
        uuid = wc.get_login_uuid()
        uri = wc.wait_for_login(uuid, tip=0)
        request, cred = wc.login(uri)
        session = wc.webwx_init(uri, request, cred)
        wc.webwx_status_notify(uri, request, session, cred)
        contacts = wc.read_contacts(uri, request, cred)
        wc.read_batch_contacts(contacts, uri, request, cred)
        asyncio.run(wc.listen(request, session))
        return uuid
