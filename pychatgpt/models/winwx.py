import attr


@attr.s
class Contact:
    headimg = attr.ib(type=str)
    name = attr.ib(type=str)
    node = attr.ib(type=int)
    remarks = attr.ib(type=str)
    wxcode = attr.ib(type=str)
    wxid = attr.ib(type=str)


@attr.s
class Message:
    content = attr.ib(type=str)
    id = attr.ib(type=str)  # timestamp
    id1 = attr.ib(type=str)  # userid
    id2 = attr.ib(type=str)
    id3 = attr.ib(type=str)
    srvid = attr.ib(type=int)
    time = attr.ib(type=str)
    type = attr.ib(type=int)
    wxid = attr.ib(type=str)  # userid or groupid


@attr.s
class Group:
    pass
