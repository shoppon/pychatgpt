from oslo_config import cfg

wechat_group = cfg.OptGroup('wechat', title='Wechat Options')
wechat_opts = [
    cfg.StrOpt('retries', default=5, help='Number of retries'),
]


def register_opts(conf):
    conf.register_group(wechat_group)
    conf.register_opts(wechat_opts, group='wechat')
