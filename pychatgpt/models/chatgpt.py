import attr


@attr.s
class Conversation:
    c_id = attr.ib(type=str) # conversation id
    p_id = attr.ib(type=str) # last message id
    to = attr.ib(type=str) # user id
