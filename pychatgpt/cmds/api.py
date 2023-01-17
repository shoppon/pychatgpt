import sys
import uvicorn

from oslo_log import log as logging

from pychatgpt import config  # noqa
from pychatgpt.api import bot

CONF = config.CONF
LOG = logging.getLogger(__name__)

if __name__ == "__main__":
    CONF(sys.argv[1:], project='chatgpt')

    uvicorn.run(bot.app, host="127.0.0.1", port=6666, log_level="info")
    LOG.info("Server exited.")
