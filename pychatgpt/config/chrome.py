from oslo_config import cfg

chrome_group = cfg.OptGroup('chrome', title='Chrome Options')
chrome_opts = [
    cfg.StrOpt('driver_exec_path', help='User agent'),
    cfg.StrOpt('browser_exec_path', help='User agent'),
]


def register_opts(conf):
    conf.register_group(chrome_group)
    conf.register_opts(chrome_opts, group='chrome')
