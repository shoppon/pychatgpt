import asyncio
import json
import random
import re
import time
import xml
from functools import partial
from requests import Session as RequestsSession
from requests import Response
from requests.exceptions import RequestException

from oslo_config import cfg
from oslo_log import log as logging

from pychatgpt import exception
from pychatgpt import utils
from pychatgpt.message import handlers
from pychatgpt.message.handlers import BaseHandler
from pychatgpt.models.webwx import Contacts
from pychatgpt.models.webwx import Credential
from pychatgpt.models.webwx import Message
from pychatgpt.models.webwx import Request
from pychatgpt.models.webwx import Session
from pychatgpt.models.webwx import Uri

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


BASE_URL = 'https://login.wx2.qq.com/'


class WechatClient:
    def __init__(self, appid, lang):
        self.appid = appid
        self.lang = lang
        self.session = RequestsSession()
        self.working = False
        self.should_stop = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        return False

    @utils.retry((exception.BadResponse, RequestException), retries=3)
    def _request(self, method: str, url: str,
                 params: dict = None,  # query string
                 form: dict = None,  # form data
                 body: dict = None,  # json body
                 headers: dict = None,
                 cookies: dict = None,
                 timeout: int = 10,
                 ) -> Response:
        headers = headers or {}
        headers['User-Agent'] = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/108.0.0.0 Safari/537.36')

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
            content = json.dumps(body, ensure_ascii=False).encode('utf-8')

        LOG.info(f"Request: {method}, {url}, params: {params}, "
                 f"data: {content}, headers, {headers}")
        resp = self.session.request(method, url,
                                    params=params,
                                    data=content,
                                    cookies=cookies,
                                    headers=headers,
                                    timeout=timeout)
        LOG.info(f"Response code: {resp.status_code}.")
        LOG.debug(f"Response content: {resp.text}.")
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
        LOG.info(f"Login code: {code}.")

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
        resp = self._request('POST', url, body=body)
        decoded = json.loads(resp.content.decode('utf-8'))
        if decoded['BaseResponse']['Ret'] != 0:
            raise exception.BadResponse(f"Bad response: {decoded}")

        contacts = Contacts()
        for member in decoded['MemberList']:
            user_id = member['UserName']
            if member['VerifyFlag'] & 8 != 0:
                contacts.publics[user_id] = member
            elif "@@" in user_id:
                contacts.groups[user_id] = member
            else:
                contacts.friends[user_id] = member
        return contacts

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
                     for g in contacts.groups.values()]
        }
        resp = self._request('POST', url, body=body)
        decoded = json.loads(resp.content.decode('utf-8'))
        LOG.info(f'Read batch contact, resp: {decoded}')

    def read_group(self, userid, uri: Uri, request: Request,
                   credential: Credential):
        now = int(time.time())
        url = (f'{uri.base_uri}/webwxbatchgetcontact?type=ex&r={now}&'
               f'pass_ticket={credential.pass_ticket}')

        body = {
            'BaseRequest': request.to_dict(),
            "Count": 1,
            "List": [{"UserName": userid, "EncryChatRoomId": ""}]
        }
        resp = self._request('POST', url, body=body)
        decoded = json.loads(resp.content.decode('utf-8'))
        return decoded['ContactList'][0]

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

    async def listen(self, uri: Uri, request: Request, session: Session,
                     credentials: Credential, contacts: Contacts):
        start_time = time.time()
        failures = 0
        host = self.select_host(request, session)
        self.working = True
        while True:
            if self.should_stop:
                LOG.info('Stop listen.')
                break

            try:
                retcode, selector = self.sync_check(host, request, session)
                if retcode in ('1100', '1101', '1102'):
                    LOG.warning(f'Receive retcode: {retcode}, Login out')
                    break

                if selector in ('2', "3", "4", "6", "7"):
                    resp = self.webwx_sync(uri, request, session, credentials)
                    if resp is not None:
                        self.handle_message(resp, contacts, uri, session,
                                            request, credentials)
                else:
                    LOG.info(f'Receive selector: {selector}.')
            except Exception as err:
                LOG.exception(f'Listen error: {err}')
                failures += 1
                now = time.time()
                # reset failures if period is over
                if (now - start_time) > CONF.wechat.period:
                    start_time = now
                    failures = 0
                # continue if failures is less than retries
                if failures <= CONF.wechat.retries:
                    continue
            finally:
                await asyncio.sleep(CONF.wechat.sync_interval)

        LOG.info('Listen stopped.')
        self.working = False

    def webwx_sync(self, uri: Uri, request: Request, session: Session,
                   credentials: Credential):
        url = (f'{uri.base_uri}/webwxsync?sid={request.sid}&skey={request.skey}'
               f'&pass_ticket={credentials.pass_ticket}')
        body = {
            'BaseRequest': request.to_dict(),
            'SyncKey': session.sync_key_origin,
            'rr': ~int(time.time())
        }
        resp = self._request('POST', url, body=body)
        decoded = json.loads(resp.content.decode('utf-8'))
        if decoded['BaseResponse']['Ret'] != 0:
            LOG.warning('Sync error')
            return None

        session.sync_key_origin = decoded['SyncKey']
        session.sync_key_parsed = '|'.join([str(kv['Key']) + '_' + str(kv['Val'])
                                            for kv in decoded['SyncKey']['List']])
        return decoded

    def parse_username(self, userid, contacts: Contacts,
                       uri, request, credentials):
        # get username from contact first
        username = contacts.get_username(userid)
        # group name
        if username.startswith('@@'):
            group = self.read_group(userid, uri, request, credentials)
            contacts.groups[userid] = group
            username = group['NickName']
        # group user name
        elif username.startswith('@'):
            username = contacts.get_group_username(userid)

        return username

    def handle_message(self, resp,
                       contacts: Contacts,
                       uri: Uri,
                       session: Session,
                       request: Request,
                       credentials: Credential):
        reply_fn = partial(self.send_message,
                           uri=uri, request=request,
                           session=session,
                           credentials=credentials)

        for msg in resp['AddMsgList']:
            msg_type = msg['MsgType']
            content = msg['Content'].replace('&lt;', '<').replace('&gt;', '>')

            from_userid = msg['FromUserName']
            from_username = self.parse_username(from_userid, contacts,
                                                uri, request, credentials)
            to_userid = msg['ToUserName']
            to_username = self.parse_username(to_userid, contacts,
                                              uri, request, credentials)

            group_userid = None
            group_username = None
            if content.startswith('@'):
                group_userid, content = content.split(':<br/>', 1)
                group_username = self.parse_username(group_userid,
                                                     contacts, uri,
                                                     request,
                                                     credentials)
            message = Message(msg_type=msg_type,
                              content=content,
                              from_userid=from_userid,
                              from_username=from_username,
                              to_userid=to_userid,
                              to_username=to_username,
                              group_userid=group_userid,
                              group_username=group_username,
                              )
            handler: BaseHandler = handlers.find_handler(msg_type, 'webwx')
            me = session.user['UserName']
            if handler:
                handler(me, reply_fn).handle(message)

    def send_message(self, content, to,
                     uri: Uri,
                     request: Request,
                     session: Session,
                     credentials: Credential):
        url = (f'{uri.base_uri}/webwxsendmsg?'
               f'pass_ticket={credentials.pass_ticket}')
        now = int(time.time() * 1000)
        rand = str(random.random())[:5].replace('.', '')
        client_msg_id = f'{now}{rand}'
        params = {
            'BaseRequest': request.to_dict(),
            'Msg': {
                "Type": 1,
                "Content": content,
                "FromUserName": session.user['UserName'],
                "ToUserName": to,
                "LocalID": client_msg_id,
                "ClientMsgId": client_msg_id
            }
        }
        resp = self._request('POST', url, body=params)
        decoded = json.loads(resp.content.decode('utf-8'))
        sent = decoded['BaseResponse']['Ret'] == 0
        LOG.info(f'Send message to {to}, content: {content}, sent: {sent}.')

    def stop(self):
        self.should_stop = True
