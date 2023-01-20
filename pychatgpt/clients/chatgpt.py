import json
import re
import tls_client
import uuid

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
            LOG.warning(f"Failed to detect cookies!")

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

    def get_msg_history(self, id):
        url = f"{BASE_URL}backend-api/conversation/{id}"
        return self._request(url, "GET")

    def get_conversations(self, offset=0, limit=20):
        LOG.info(f"Getting conversations from {offset} to {offset + limit}")
        url = (f"{BASE_URL}backend-api/conversations?"
               f"offset={offset}&limit={limit}")
        response = self._request(url, "GET")
        return response['items']

    def gen_title(self, id, message_id):
        url = f"{BASE_URL}backend-api/conversation/gen_title/{id}"
        body = {"message_id": message_id, "model": "text-davinci-002-render"}
        return self._request(url, "POST", data=json.dumps(body))

    def ask(self, prompt, conversation_id=None, parent_id=None):
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
        response = self._request(
            url=BASE_URL + "backend-api/conversation",
            method="POST",
            data=json.dumps(data),
            raw=True,
            timeout_seconds=180
        )
        try:
            response = response.text.splitlines()[-4]
            response = response[6:]
        except Exception:
            raise exception.BadResponse("Bad response from OpenAI!")

        # Check if it is JSON
        if not response.startswith("{"):
            raise exception.BadResponse(f"Unexpected response {response}!")

        response = json.loads(response)
        parent_id = response["message"]["id"]
        conversation_id = response["conversation_id"]
        message = response["message"]["content"]["parts"][0]
        return {
            "message": message,
            "conversation_id": conversation_id,
            "parent_id": parent_id,
        }
