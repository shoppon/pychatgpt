from oslo_config import cfg

hook_group = cfg.OptGroup('hook', title='Hook Options')
hook_opts = [
    cfg.StrOpt('url', default='ws://127.0.0.1:5555', help='Hook url'),
]


def register_opts(conf):
    conf.register_group(hook_group)
    conf.register_opts(hook_opts, group='hook')
