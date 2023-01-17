import re
import json
import requests
import time

from pychatgpt import exception


class WechatClient:
    def __init__(self, appid, lang):
        self.appid = appid
        self.lang = lang

    def _request(self, method: str, url: str, body: dict):
        return requests.request(method, url, data=json.dumps(body))

    def get_login_uuid(self):
        url = 'https://login.wx2.qq.com/jslogin'
        params = {
            'appid': self.appid,
            'redirect_uri': 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?mod=desktop',
            'fun': 'new',
            'lang': self.lang,
            '_': int(time.time())
        }
        resp = self._request('POST', url, params)
        if resp.status_code != 200:
            raise exception.BadResponse(f"Bad response: {resp.status_code}")

        regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
        pm = re.search(regx, resp.text)
        if not pm:
            raise exception.BadResponse(f"Bad response: {resp.text}")

        code = pm.group(1)
        if code != '200':
            raise exception.BadResponse(f"Bad response: {code}")

        uuid = pm.group(2)
        return uuid

    def genQRCode(self):
        return self._str2qr('https://login.weixin.qq.com/l/' + self.uuid)
