from oslo_config import cfg

openai_group = cfg.OptGroup('openai', title='OpenAI Options')
openai_opts = [
    cfg.StrOpt('api_key', help='OpenAI API key'),
]


def register_opts(conf):
    conf.register_group(openai_group)
    conf.register_opts(openai_opts, group='openai')
