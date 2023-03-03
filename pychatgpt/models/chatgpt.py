import attr


@attr.s
class Conversation:
    to = attr.ib(type=str)  # user id
    messages = attr.ib(type=list, default=attr.Factory(list))
    enabled = attr.ib(type=bool, default=True)
