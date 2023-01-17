from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import PlainTextResponse
from oslo_log import log as logging

from pychatgpt.exception import PyChatGPTException

LOG = logging.getLogger(__name__)

app = FastAPI()


@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    LOG.error(f"Exception: {exc}")
    return PlainTextResponse(str(exc), status_code=500)


@app.exception_handler(PyChatGPTException)
async def exception_handler(request: Request, exc: PyChatGPTException):
    LOG.error(f"Exception: {exc}")
    return PlainTextResponse(str(exc), status_code=500)
