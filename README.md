# description
a wechat bot for conversation with openai gpt-3.5

# requirements
1. install windows wechat 3.6.18.0.
2. login windows wechat.
3. download wechat-bot from [here](https://github.com/cixingguangming55555/wechat-bot/tree/5.1.8.00).
4. double click `wechat-bot-5.1.8.00\wechat-bot-5.1.8.00\server\funtool_3.6.0.18-1.0.0013非注入版.exe` to run wechat-bot server.

# build(optional when using docker or kubernetes)
using docker to build cri image
```
docker build -t shoppon/pychatgpt .
```

# configuration
the template of configuration file is `etc/pychatgpt.conf`.

| key | group| description | default |
| --- | --- | --- | --- |
| url | hook | hook url | ws://127.0.0.1:5555 |
| prefix | wechat | prefix for wechat message | #ai |
| api_key | openai | openai api key | |
| timeout | openai | openai api timeout | 60 |
| http_proxy | tls_client | http proxy for tls client | http://127.0.0.1:7890 |

# run
## kubernetes
deploy hook on kubernetes cluster
```
kubectl create ns pychatgpt
kubectl apply -f deploy/configmap-bin.yaml
kubectl apply -f deploy/configmap-etc.yaml
kubectl apply -f deploy/deployment-hook.yaml
```

## docker
TBD

## vscode
1. copy `pychatgpt.conf` to `/etc/pychatgpt/pychatgpt.conf`.
2. fill in hook.url and openai.api_key in `/etc/pychatgpt/pychatgpt.conf`.
3. open running/debug pannel.
4. click `wechat hook` to run.

## command line
1. install python 3.8 or later.
2. run `pip install -r requirements.txt` to install dependencies.
3. run `python setup.py install` to install pychatgpt.
4. run `pychatgpt-hook --config-file /etc/pychatgpt/pychatgpt.conf` to start.

## systemd
1. copy `bin/pychatgpt-hook.service` to `/etc/systemd/system/pychatgpt-hook.service`.
2. run `systemctl daemon-reload` to reload systemd.
3. run `systemctl enable pychatgpt-hook` to enable pychatgpt-hook.
4. run `systemctl start pychatgpt-hook` to start pychatgpt-hook.

# usage
pychatgpt use group or contacts as the conversation unit.

## clear conversation
input `#ai clear` to clear a conversation context.

## stop conversation
input `#ai stop` to disable a conversation.

## start conversation
input `#ai start` to enable a conversation.
