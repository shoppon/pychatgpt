from time import sleep

import undetected_chromedriver as uc
import tenacity
from oslo_config import cfg
from oslo_log import log as logging

from pychatgpt import utils

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Chrome:
    def __init__(self, on_response_received: callable,
                 on_request_will_be_sent: callable,
                 is_ready: callable = None):
        self.on_response_received = on_response_received
        self.on_request_will_be_sent = on_request_will_be_sent
        self.is_ready = is_ready

    @utils.retry(lambda x: x is False,
                 retries=3,
                 retry=tenacity.retry_if_result)
    def start(self, url, proxy=None, timeout=60):
        driver = None
        try:
            LOG.info(f"Starting Chrome, url: {url}, proxy: {proxy}")
            driver = uc.Chrome(
                enable_cdp_events=True, options=self._get_options(proxy),
                driver_executable_path=CONF.chrome.driver_exec_path,
                browser_executable_path=CONF.chrome.browser_exec_path)
            driver.add_cdp_listener(
                "Network.responseReceivedExtraInfo",
                self.on_response_received)
            driver.add_cdp_listener(
                "Network.requestWillBeSentExtraInfo",
                self.on_request_will_be_sent)
            driver.get("https://chat.openai.com/chat")
            while timeout:
                if self.is_ready():
                    return True
                LOG.warning(f"Chrome not ready, timeout: {timeout}")
                timeout -= 5
                sleep(5)
            LOG.error("Chrome startup timeout!")
            return False
        except Exception as err:
            LOG.exception(f"Unable to start Chrome, error: {err}")
            return False
        finally:
            if driver:
                driver.quit()

    def _get_options(self, proxy=None):
        options = uc.ChromeOptions()
        options.add_argument('--start_maximized')
        options.add_argument("--disable-extensions")
        options.add_argument('--disable-application-cache')
        options.add_argument('--disable-gpu')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")
        return options
