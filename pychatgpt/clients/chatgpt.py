"""A client for chatgpt
"""
import json
import uuid
import tls_client
from http.cookies import SimpleCookie

from oslo_config import cfg
from oslo_log import log as logging

from pychatgpt import exception
from pychatgpt import utils
from pychatgpt.clients import chrome

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

BASE_URL = "https://chat.openai.com/"


class ChatgptClient:
    """a client for chatgpt
    """

    def __init__(self, session_token) -> None:
        self.session = tls_client.Session(
            client_identifier="chrome_108"
        )
        self.session_token = session_token
        proxies = {
            "http": CONF.tls_client.http_proxy,
            "https": CONF.tls_client.https_proxy,
        }
        self.session.proxies.update(proxies)
        self.session.cookies.set(
            "__Secure-next-auth.session-token",
            self.session_token)

        self.user_agent = None

    def _is_ready(self):
        cookie_keys = self.session.cookies.keys()
        return all(k in cookie_keys for k in
                   ["__Secure-next-auth.session-token",
                    "cf_clearance",
                    "__cf_bm",
                    "_cfuvid"])

    def startup(self):
        """startup
        """
        self.user_agent = None
        self.session.cookies.clear()
        with chrome.Chrome(self._detect_cookies,
                           self._detect_user_agent,
                           self._is_ready,
                           proxy=CONF.tls_client.http_proxy) as cc:
            cc.start(f"{BASE_URL}chat", CONF.tls_client.http_proxy)
            self._refresh_headers(self.user_agent)

    @utils.retry(exception.BadSession, retries=10)
    def refresh_session(self):
        """refresh session

        Raises:
            exception.BadSession
        """
        LOG.info("Refreshing session...")
        url = BASE_URL + "api/auth/session"
        response = self.session.get(url, timeout_seconds=180)
        if response.status_code != 200:
            LOG.info(f'Failed to refresh session, '
                     f'status code: {response.status_code}.')
            self.startup()
            raise exception.BadSession(f"Bad resp: {response.status_code}!")

        resp_json = response.json()
        if "accessToken" not in resp_json:
            raise exception.BadSession(f"Unexpected resp: {resp_json}!")

        self.session.headers.update({
            "Authorization": "Bearer " + resp_json["accessToken"]
        })
        self.session_token = self.session.cookies._find(
            "__Secure-next-auth.session-token",)

    def _detect_user_agent(self, message):
        try:
            if self.user_agent:
                return
            self.user_agent = message['params']['headers']['user-agent']
            LOG.info(f"User agent: {self.user_agent}")
        except KeyError:
            LOG.debug("Failed to detect user agent!")

    def _detect_cookies(self, message):
        try:
            rawdata = message['params']['headers']['set-cookie']
            if rawdata:
                cookie = SimpleCookie()
                cookie.load(rawdata)
                self.session.cookies.update(cookie)
        except KeyError:
            LOG.debug("Failed to detect cookies!")

    def _refresh_headers(self, user_agent):
        self.session.headers.clear()
        self.session.headers.update({
            "Accept": "text/event-stream",
            "Authorization": "Bearer ",
            "Content-Type": "application/json",
            "User-Agent": user_agent,
            "X-Openai-Assistant-App-Id": "",
            "Connection": "close",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://chat.openai.com/chat",
        })

    @utils.retry(exception.BadResponse, retries=3)
    def _request(self, url, method, data=None, timeout_seconds=180, raw=False):
        LOG.info(f"Requesting {method} {url}, data: {data}.")
        if method == "GET":
            response = self.session.get(url, timeout_seconds=timeout_seconds)
        elif method == "POST":
            response = self.session.post(url, data=data,
                                         timeout_seconds=timeout_seconds)
        else:
            raise NotImplementedError(f"Method {method} not implemented!")

        # check response
        if response.status_code != 200:
            raise exception.BadResponse(f"Bad resp: {response.status_code}!")
        return response.text if raw else json.loads(response.text)

    def ask(self, prompt, conversation_id=None, parent_id=None):
        """Ask a question.
        """
        self.refresh_session()
        data = {
            "action": "next",
            "messages": [
                {
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "content": {"content_type": "text", "parts": [prompt]},
                },
            ],
            "conversation_id": conversation_id,
            "parent_message_id": parent_id or str(uuid.uuid4()),
            "model": "text-davinci-002-render",
        }
        response_text = self._request(
            url=BASE_URL + "backend-api/conversation",
            method="POST",
            data=json.dumps(data),
            raw=True,
            timeout_seconds=180
        )
        try:
            response = response_text.splitlines()[-4]
            response = response[6:]
        except Exception:
            raise exception.BadResponse(f"Bad response: {response}!")

        # Check if it is JSON
        if not response.startswith("{"):
            raise exception.BadResponse(f"Unexpected response {response}!")

        response = json.loads(response)
        message_id = response["message"]["id"]
        conv_id = response["conversation_id"]
        message = response["message"]["content"]["parts"][0]
        return {
            "message": message,
            "conversation_id": conv_id,
            "message_id": message_id,
        }
