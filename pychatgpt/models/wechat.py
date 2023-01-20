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
    cookies = attr.ib()
    sync_key_origin = attr.ib(type=list)
    sync_key_parsed = attr.ib(type=str)


@attr.s
class Contacts:
    publics = attr.ib(type=dict, default={})  # userid: contact
    groups = attr.ib(type=dict, default={})
    friends = attr.ib(type=dict, default={})

    def get_username(self, userid):
        for contact in self.publics.values():
            if contact['UserName'] == userid:
                return contact['NickName']
        for contact in self.groups.values():
            if contact['UserName'] == userid:
                return contact['NickName']
        for contact in self.friends.values():
            if contact['UserName'] == userid:
                return contact['NickName']
        return userid

    def get_group_username(self, userid):
        for group in self.groups.values():
            for member in group['MemberList']:
                if member['UserName'] == userid:
                    return member['NickName']
        return userid
