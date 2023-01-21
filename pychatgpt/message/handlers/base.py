from pychatgpt.models.wechat import Message


class BaseHandler:
    msg_type = None

    def __init__(self, me:str, reply_fn: callable,) -> None:
        self.me = me
        self.reply_fn = reply_fn

    def handle(self, msg: Message) -> None:
        raise NotImplementedError
