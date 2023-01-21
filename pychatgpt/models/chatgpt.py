import attr


@attr.s
class Conversation:
    c_id = attr.ib(type=str)
    p_id = attr.ib(type=str)
    to = attr.ib(type=str)
