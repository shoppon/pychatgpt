import sys

from pychatgpt import config  # noqa
from pychatgpt.clients import chatgpt

CONF = config.CONF

if __name__ == "__main__":
    CONF(sys.argv[1:], project='manul')

    cc = chatgpt.ChatgptClient()
    cc.startup()
    cc.refresh_session()
