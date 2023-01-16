from oslo_config import cfg


chatgpt_group = cfg.OptGroup('chatgpt', title='Chatgpt Options')

chatgpt_opts = [
    cfg.StrOpt('session_token', help='Session token'),
]


def register_opts(conf):
    conf.register_group(chatgpt_group)
    conf.register_opts(chatgpt_opts, group='chatgpt')
