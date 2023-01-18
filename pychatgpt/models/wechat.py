import attr
import random


DEVICE_ID = 'e' + repr(random.random())[2:17]


@attr.s
class Uri:
    redirect_uri = attr.ib(type=str)
    base_uri = attr.ib(type=str)


@attr.s
class Request:
    uin = attr.ib(type=int)
    sid = attr.ib(type=str)
    skey = attr.ib(type=str)
    device_id = attr.ib(type=str, default=DEVICE_ID)

    def to_dict(self):
        return {
            'Uin': self.uin,
            'Sid': self.sid,
            'Skey': self.skey,
            'DeviceID': self.device_id,
        }


@attr.s
class Credential:
    pass_ticket = attr.ib(type=str)


@attr.s
class Session:
    user = attr.ib(type=dict)
    sync_key = attr.ib(type=str)


@attr.s
class Contacts:
    publics = attr.ib(type=list)
    groups = attr.ib(type=list)
