from oslo_config import cfg

from pychatgpt.config import chatgpt
from pychatgpt.config import chrome
from pychatgpt.config import hook
from pychatgpt.config import tls_client
from pychatgpt.config import wechat

CONF = cfg.CONF

chatgpt.register_opts(CONF)
chrome.register_opts(CONF)
hook.register_opts(CONF)
tls_client.register_opts(CONF)
wechat.register_opts(CONF)
