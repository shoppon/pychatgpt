from oslo_config import cfg


google_group = cfg.OptGroup('google', title='Google Options')
google_opts = [
    cfg.StrOpt('username', help='Username'),
    cfg.StrOpt('password', help='Password'),
]


def register_opts(conf):
    conf.register_group(google_group)
    conf.register_opts(google_opts, group='google')
