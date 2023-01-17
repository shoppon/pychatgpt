from contextlib import contextmanager

from pychatgpt.api import app
from pychatgpt.clients import wechat
from pychatgpt.exception import PyChatGPTException

APP_ID = "wx782c26e4c19acffb"
wc = None


@contextmanager
def ensure_wechat():
    try:
        global wc
        if wc is None:
            wc = wechat.WechatClient(APP_ID, "zh_CN")
        yield wc
    finally:
        if wc is None:
            raise PyChatGPTException("Wechat client is not started.")


@app.get("/wechat/uuid")
def get_uuid():
    with ensure_wechat() as wc:
        resp = wc.get_login_uuid()
        return resp
