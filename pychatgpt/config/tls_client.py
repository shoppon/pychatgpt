from oslo_config import cfg


tls_client_group = cfg.OptGroup('tls_client', title='TLS Client Options')

tls_client_opts = [
    cfg.StrOpt('http_proxy', default='', help='HTTP proxy'),
    cfg.StrOpt('https_proxy', default='', help='HTTPS proxy'),
]


def register_opts(conf):
    conf.register_group(tls_client_group)
    conf.register_opts(tls_client_opts, group='tls_client')
