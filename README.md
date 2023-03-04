# pychatgpt
python client for chatgpt

# environment
1. install windows wechat 3.6.18.0.
2. login windows wechat.
3. download wechat-bot from [here](https://github.com/cixingguangming55555/wechat-bot/tree/5.1.8.00).
4. double click `wechat-bot-5.1.8.00\wechat-bot-5.1.8.00\server\funtool_3.6.0.18-1.0.0013非注入版.exe` to run wechat-bot server.

# build
using docker to build cri image
```
docker build -t shoppon/pychatgpt .
```

# run
## kubernetes
### configure
1. fill in hook.url and openai.api_key in the `deploy/configmap-etc.yaml`
2. [optional] fill in tls_client.http_proxy in the `deploy/configmap-etc.yaml`

### deploy
deploy hook on kubernetes cluster
```
kubectl create ns pychatgpt
kubectl apply -f deploy/configmap-bin.yaml
kubectl apply -f deploy/configmap-etc.yaml
kubectl apply -f deploy/deployment-hook.yaml
```

## docker


## vscode
1. copy `pychatgpt.conf` to `/etc/pychatgpt/pychatgpt.conf`.
2. fill in hook.url and openai.api_key in `/etc/pychatgpt/pychatgpt.conf`.
3. open running/debug pannel.
4. click `wechat hook` to run.

## command line
1. install python 3.8 or later.
2. run `pip install -r requirments.txt` to install dependencies.
3. run `python setup.py install` to install pychatgpt.
4. fill in hook.url and openai.api_key in `/etc/pychatgpt/pychatgpt.conf`.
5. run `pychatgpt-hook --config-file /etc/pychatgpt/pychatgpt.conf` to start.

# usage
pychatgpt use group or contacts as the conversation unit.

## clear conversation
input `#ai clear` to clear a conversation context.

## stop conversation
input `#ai stop` to disable a conversation.

## start conversation
input `#ai start` to enable a conversation.
