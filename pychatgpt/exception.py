class PyChatGPTException(Exception):
    pass


class BadSession(PyChatGPTException):
    pass


class BadResponse(PyChatGPTException):
    pass
