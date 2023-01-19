import asyncio
import json
import qrcode
import re
import requests
import time
import urllib
import xml
from urllib.parse import urlencode

from oslo_log import log as logging

from pychatgpt import exception
from pychatgpt import utils
from pychatgpt.models.wechat import Contacts
from pychatgpt.models.wechat import Credential
from pychatgpt.models.wechat import Request
from pychatgpt.models.wechat import Session
from pychatgpt.models.wechat import Uri

LOG = logging.getLogger(__name__)


BASE_URL = 'https://login.wx2.qq.com/'


class WechatClient:
    def __init__(self, appid, lang):
        self.appid = appid
        self.lang = lang

    @utils.retry(exception.BadResponse, retries=3)
    def _request(self, method: str, url: str,
                 params: dict = None,  # query string
                 form: dict = None,  # form data
                 body: dict = None,  # json body
                 headers: dict = None,
                 cookies: dict = None,
                 ) -> requests.Response:
        headers = headers or {}

        if method == 'POST':
            headers['Content-Type'] = 'application/json; charset=UTF-8'

        if method == 'GET':
            headers['Referer'] = 'https://wx.qq.com/'

        content = None
        if form is not None:
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            content = form
        elif body is not None:
            headers['Content-Type'] = 'application/json; charset=UTF-8'
            content = json.dumps(body).encode()

        LOG.info(f"Request: {method}, {url}, params: {params}, "
                 f"data: {content}, headers, {headers}")
        resp = requests.request(method, url,
                                params=params,
                                data=content,
                                cookies=cookies,
                                headers=headers)
        LOG.debug(f"Response: {resp.status_code}, {resp.text}")
        if resp.status_code != 200:
            raise exception.BadResponse(f"Bad response: {resp.status_code}")
        return resp


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
        self._print_qrcode(f'https://login.weixin.qq.com/l/{uuid}')
        return uuid

    @utils.retry(exception.BadResponse, retries=5)
    def wait_for_login(self, uuid, tip=1):
        LOG.info(f"Waiting for login, uuid: {uuid}, tip: {tip}")
        now = int(time.time())
        url = (f'https://login.wx2.qq.com/cgi-bin/mmwebwx-bin/login?'
               f'tip={tip}&uuid={uuid}&_={now}')
        resp = self._request('GET', url).text
        match_obj = re.search(r"window.code=(\d+);", resp)
        code = match_obj.group(1)

        if code != '200':
            raise exception.BadResponse(f"Bad response: {code}")

        match_obj = re.search(r'window.redirect_uri="(\S+?)";', resp)
        redirect_uri = match_obj.group(1) + '&fun=new'
        base_uri = redirect_uri[:redirect_uri.rfind('/')]
        return Uri(redirect_uri=redirect_uri, base_uri=base_uri)

    def login(self, uri: Uri):
        LOG.info(f"Login, uri: {uri}")
        headers = {
            'extspam': ('Go8FCIkFEokFCggwMDAwMDAwMRAGGvAESySibk50w5Wb'
                        '3uTl2c2h64jVVrV7gNs06GFlWplHQbY/5FfiO++1yH4y'
                        'kCyNPWKXmco+wfQzK5R98D3so7rJ5LmGFvBLjGceleyS'
                        'rc3SOf2Pc1gVehzJgODeS0lDL3/I/0S2SSE98YgKleq6'
                        'Uqx6ndTy9yaL9qFxJL7eiA/R3SEfTaW1SBoSITIu+EEk'
                        'Xff+Pv8NHOk7N57rcGk1w0ZzRrQDkXTOXFN2iHYIzAAZ'
                        'PIOY45Lsh+A4slpgnDiaOvRtlQYCt97nmPLuTipOJ8Qc'
                        '5pM7ZsOsAPPrCQL7nK0I7aPrFDF0q4ziUUKettzW8MrA'
                        'aiVfmbD1/VkmLNVqqZVvBCtRblXb5FHmtS8FxnqCzYP4'
                        'WFvz3T0TcrOqwLX1M/DQvcHaGGw0B0y4bZMs7lVScGBF'
                        'xMj3vbFi2SRKbKhaitxHfYHAOAa0X7/MSS0RNAjdwoyG'
                        'HeOepXOKY+h3iHeqCvgOH6LOifdHf/1aaZNwSkGotYnY'
                        'ScW8Yx63LnSwba7+hESrtPa/huRmB9KWvMCKbDThL/nn'
                        'e14hnL277EDCSocPu3rOSYjuB9gKSOdVmWsj9Dxb/iZI'
                        'e+S6AiG29Esm+/eUacSba0k8wn5HhHg9d4tIcixrxvef'
                        'lc8vi2/wNQGVFNsGO6tB5WF0xf/plngOvQ1/ivGV/C1Q'
                        'pdhzznh0ExAVJ6dwzNg7qIEBaw+BzTJTUuRcPk92Sn6Q'
                        'Dn2Pu3mpONaEumacjW4w6ipPnPw+g2TfywJjeEcpSZaP'
                        '4Q3YV5HG8D6UjWA4GSkBKculWpdCMadx0usMomsSS/74'
                        'QgpYqcPkmamB4nVv1JxczYITIqItIKjD35IGKAUwAA=='),
            'client-version': '2.0.0',
        }
        resp = self._request('GET', uri.redirect_uri, headers=headers).text
        doc = xml.dom.minidom.parseString(resp)
        root = doc.documentElement

        for node in root.childNodes:
            if node.nodeName == 'skey':
                skey = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                sid = node.childNodes[0].data
            elif node.nodeName == 'wxuin':
                uin = node.childNodes[0].data
            elif node.nodeName == 'pass_ticket':
                pass_ticket = node.childNodes[0].data

        if not all((skey, sid, uin, pass_ticket)):
            raise exception.BadResponse(f"Bad response: {resp}")

        return Request(skey=skey, sid=sid, uin=int(uin)), Credential(pass_ticket)

    def webwx_init(self, uri: Uri, request: Request, credential: Credential):
        LOG.info(f'Webwx init, uri: {uri}, request: {request}, '
                 f'credential: {credential}')
        now = int(time.time())
        url = (f'{uri.base_uri}/webwxinit?pass_ticket={credential.pass_ticket}&'
               f'skey={request.skey}&r={now}')
        body = {
            'BaseRequest': request.to_dict(),
        }
        resp = self._request('POST', url, body=body)
        content = json.loads(resp.text)
        if content['BaseResponse']['Ret'] != 0:
            raise exception.BadResponse(f"Bad response: {content}")

        user = content['User']
        sync_key_origin = content['SyncKey']
        sync_key_parsed = '|'.join([str(kv['Key']) + '_' + str(kv['Val'])
                                    for kv in sync_key_origin['List']])

        return Session(user=user,
                       cookies=resp.cookies,
                       sync_key_origin=sync_key_origin,
                       sync_key_parsed=sync_key_parsed,
                       )

    def webwx_status_notify(self, uri: Uri, request: Request,
                            session: Session,
                            credential: Credential):
        url = (f'{uri.base_uri}/webwxstatusnotify?lang=zh_CN&'
               f'pass_ticket={credential.pass_ticket}')
        body = {
            'BaseRequest': request.to_dict(),
            "Code": 3,
            "FromUserName": session.user['UserName'],
            "ToUserName": session.user['UserName'],
            "ClientMsgId": int(time.time())
        }
        resp = json.loads(self._request('POST', url, body=body).text)
        if resp['BaseResponse']['Ret'] != 0:
            raise exception.BadResponse(f"Bad response: {resp}")

    def read_contacts(self, uri: Uri, request: Request,
                      credential: Credential):
        LOG.info(f'Read contacts, uri: {uri}, request: {request}.')
        now = int(time.time())
        url = (f'{uri.base_uri}/webwxgetcontact?pass_ticket='
               f'{credential.pass_ticket}&skey={request.skey}&r={now}')
        body = {
            'BaseRequest': request.to_dict(),
        }
        resp = json.loads(self._request('POST', url, body=body).text)
        if resp['BaseResponse']['Ret'] != 0:
            raise exception.BadResponse(f"Bad response: {resp}")

        publics = []
        groups = []
        for member in resp['MemberList']:
            if member['VerifyFlag'] & 8 != 0:
                publics.append(member)
            elif member['UserName'].startswith('@@'):
                groups.append(member)
        return Contacts(publics=publics, groups=groups)

    def read_batch_contacts(self, contacts: Contacts, uri: Uri,
                            request: Request, credential: Credential):
        LOG.info(f'Read batch contact, uri: {uri}, request: {request}.')
        now = int(time.time())
        url = (f'{uri.base_uri}/webwxbatchgetcontact?type=ex&r={now}&'
               f'pass_ticket={credential.pass_ticket}')
        body = {
            'BaseRequest': request.to_dict(),
            "Count": len(contacts.groups),
            "List": [{"UserName": g['UserName'], "EncryChatRoomId":""}
                     for g in contacts.groups]
        }
        resp = self._request('POST', url, body=body)
        LOG.info(f'Read batch contact, resp: {resp.text}')

    def sync_check(self, host, request: Request, session: Session):
        now = int(time.time())
        params = {
            'r': now,
            'sid': request.sid,
            'uin': request.uin,
            'skey': request.skey,
            'deviceid': request.device_id,
            'synckey': session.sync_key_parsed,
            '_': int(time.time()),
        }
        url = f'https://{host}/cgi-bin/mmwebwx-bin/synccheck'
        resp = self._request('GET', url, params=params,
                             cookies=session.cookies).text
        match_obj = re.search(
            r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}', resp)
        retcode = match_obj.group(1)
        selector = match_obj.group(2)
        return retcode, selector

    def select_host(self, request: Request, session: Session):
        hosts = ['wx.qq.com',
                 'wx2.qq.com',
                 'webpush.wx2.qq.com',
                 'wx8.qq.com',
                 'webpush.wx8.qq.com',
                 'webpush.wx.qq.com',
                 'web2.wechat.com',
                 'webpush.web2.wechat.com',
                 'webpush.web.wechat.com',
                 'webpush.weixin.qq.com',
                 'webpush.wechat.com',
                 'webpush1.wechat.com',
                 'webpush2.wechat.com',
                 'webpush.wx.qq.com',
                 'webpush2.wx.qq.com']
        for host in hosts:
            try:
                retcode, _ = self.sync_check(host, request, session)
                LOG.info(f'Check host {host}, retcode: {retcode}')
                if retcode == '0':
                    return host
            except Exception:
                LOG.error(f'Check host {host} error')
        raise exception.NoHostAvailable('No host available')

    def listen(self, request: Request, session: Session):
        host = self.select_host(request, session)
        while True:
            retcode, selector = self.sync_check(host, request, session)
            if retcode == '1100':
                LOG.warning('Login out')
                break
            if retcode == '1101':
                LOG.warning('Login on other device')
                break

            if retcode != '0':
                LOG.warning('Sync check error')
                continue

            if selector == '2':
                r = self.webwx_sync()
                if r is not None:
                    self.handle_msg(r)
            elif selector == '6':
                LOG.warning('New device login')
            elif selector == '7':
                r = self.webwx_sync()

            # await asyncio.sleep(1)

    def webwx_sync(self, uri: Uri, request: Request, session: Session):
        url = (f'{uri.base_uri}/webwxsync?sid={request.sid}&skey={request.skey}'
               f'&pass_ticket={session.pass_ticket}')
        body = {
            'BaseRequest': request.to_dict(),
            'SyncKey': session.sync_key_origin,
            'rr': ~int(time.time())
        }
        resp = self._request('POST', url, body=body).json()
        if resp['BaseResponse']['Ret'] != 0:
            LOG.warning('Sync error')
            return None

        session.sync_key_origin = resp['SyncKey']
        session.sync_key_parsed = '|'.join([str(kv['Key']) + '_' + str(kv['Val'])
                                            for kv in resp['SyncKey']['List']])
        return resp

    def handle_msg(self, r):
        for msg in r['AddMsgList']:
            LOG.info('New message')
            msg_type = msg['MsgType']
            content = msg['Content'].replace('&lt;', '<').replace('&gt;', '>')

            if msg_type == 1:
                LOG.info(f'Receive text: {content}')
            # image
            elif msg_type == 3:
                LOG.info('Receive image')
            # voice
            elif msg_type == 34:
                LOG.info('Receive voice')
            # card
            elif msg_type == 42:
                LOG.info('Receive card')
            # gif
            elif msg_type == 47:
                pass
            # share
            elif msg_type == 49:
                pass
            # contact
            elif msg_type == 51:
                pass
            # video
            elif msg_type == 62:
                pass
            elif msg_type == 10002:
                pass

    def _print_qrcode(self, value):
        qr = qrcode.QRCode()
        qr.border = 1
        qr.add_data(value)
        qr.make()
        qr.print_ascii(invert=True)
