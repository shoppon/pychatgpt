import sys
import uvicorn

from oslo_log import log as logging

from pychatgpt import config  # noqa
from pychatgpt.api import app
from pychatgpt.api import bot  # noqa
from pychatgpt.api import wechat  # noqa

CONF = config.CONF
logging.register_options(CONF)
logging.setup(CONF, "chatgpt")
LOG = logging.getLogger(__name__)


def main():
    CONF(sys.argv[1:], project='chatgpt')

    host = "0.0.0.0"
    port = 6666
    LOG.info(f"Server started at {host}:{port}.")
    uvicorn.run(app, host=host, port=port, log_level="info")
    LOG.info("Server exited.")


if __name__ == "__main__":
    main()
