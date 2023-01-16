from oslo_config import cfg

from pychatgpt.config import chatgpt
from pychatgpt.config import chrome
from pychatgpt.config import tls_client

CONF = cfg.CONF

chatgpt.register_opts(CONF)
chrome.register_opts(CONF)
tls_client.register_opts(CONF)
