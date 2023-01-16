import re
import tls_client

from oslo_config import cfg
from oslo_log import log as logging

from pychatgpt import exception
from pychatgpt import utils
from pychatgpt.clients import chrome

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

BASE_URL = "https://chat.openai.com/"


class ChatgptClient:

    def __init__(self) -> None:
        self.session = tls_client.Session(
            client_identifier="chrome_108"
        )
        proxies = {
            "http": CONF.tls_client.http_proxy,
            "https": CONF.tls_client.https_proxy,
        }
        self.session.proxies.update(proxies)
        self.session.cookies.set(
            "__Secure-next-auth.session-token",
            CONF.chatgpt.session_token)

        self._user_agent = None
        self._cf_clearance = None

    def startup(self):
        self._user_agent = None
        self._cf_clearance = None
        cc = chrome.Chrome(self._detect_cookies,
                           self._detect_user_agent,
                           lambda: self._user_agent and self._cf_clearance)
        cc.start(f"{BASE_URL}chat", CONF.tls_client.http_proxy)
        self._refresh_headers(self._user_agent, self._cf_clearance)

    @utils.retry(exception.BadSession, retries=10)
    def refresh_session(self):
        url = BASE_URL + "api/auth/session"
        response = self.session.get(url, timeout_seconds=180)
        if response.status_code != 200:
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
            self._user_agent = message['params']['headers']['user-agent']
            LOG.info(f"User agent: {self._user_agent}")
        except KeyError:
            LOG.warning("Failed to detect user agent!")

    def _detect_cookies(self, message):
        try:
            cookie = message['params']['headers']['set-cookie']
            cf_clearance_cookie = re.search("cf_clearance=.*?;", cookie)
            session_cookie = re.search(
                "__Secure-next-auth.session-token=.*?;", cookie)
            if cf_clearance_cookie:
                raw_cf_cookie = cf_clearance_cookie.group(0)
                self._cf_clearance = raw_cf_cookie.split("=")[1][:-1]
                LOG.info(f"CF Clearance: {self._cf_clearance}")

            if session_cookie:
                raw_session_cookie = session_cookie.group(0)
                self.session_token = raw_session_cookie.split("=")[1][:-1]
                self.session.cookies.set(
                    "__Secure-next-auth.session-token", self.session_token)
                LOG.info(f"Session token: {self.session_token}")
        except KeyError:
            LOG.warning(f"Failed to detect cookies! Message: {message}")

    def _refresh_headers(self, user_agent, cf_clearance):
        if not cf_clearance or not user_agent:
            return

        del self.session.cookies["cf_clearance"]
        self.session.headers.clear()
        self.session.cookies.set("cf_clearance", cf_clearance)
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
