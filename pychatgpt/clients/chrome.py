from time import sleep

import tenacity
import undetected_chromedriver as uc
from oslo_config import cfg
from oslo_log import log as logging
from pyvirtualdisplay import Display

from pychatgpt import utils

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Chrome:
    """chrome client
    """

    def __init__(self, on_response_received: callable = None,
                 on_request_will_be_sent: callable = None,
                 is_ready: callable = None,
                 proxy: str = None):
        self.on_response_received = on_response_received
        self.on_request_will_be_sent = on_request_will_be_sent
        self.is_ready = is_ready
        self.proxy = proxy

        self._driver = None

        display = Display()
        display.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()

    @property
    def driver(self):
        """get driver

        Returns:
            chrome: driver
        """
        if not self._driver:
            self._driver = uc.Chrome(
                version_main=109,
                enable_cdp_events=True, options=self._get_options(self.proxy),
                driver_executable_path=CONF.chrome.driver_exec_path,
                browser_executable_path=CONF.chrome.browser_exec_path)

            if self.on_response_received:
                self._driver.add_cdp_listener(
                    "Network.responseReceivedExtraInfo",
                    self.on_response_received)
            if self.on_request_will_be_sent:
                self._driver.add_cdp_listener(
                    "Network.requestWillBeSentExtraInfo",
                    self.on_request_will_be_sent)

        return self._driver

    @utils.retry(lambda x: x is False,
                 retries=3,
                 retry=tenacity.retry_if_result)
    def start(self, url, proxy=None, timeout=30):
        try:
            LOG.info(f"Starting Chrome, url: {url}, proxy: {proxy}")
            self.driver.get(url)
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

    def _get_options(self, proxy=None):
        options = uc.ChromeOptions()
        options.add_argument('--window-size=1024,768')
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
