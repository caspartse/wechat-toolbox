#!/usr/bin/env python
# -*- coding:utf-8 -*
import redis
from wxCommon import WebChat
from wxUtils import *
from time import strftime, localtime, sleep
try:
    import simplejson as json
except ImportError:
    import json
import codecs

rd = redis.Redis()
w = WebChat(daemon=True, flush=True)


def handle(resp):
    try:
        ret = resp.json()['BaseResponse']['Ret']
    except:
        ret = -1
    return ret


if __name__ == '__main__':
    answer = u'hi，这是自动回复消息 [微笑]\n我现在不在线，无法及时回复你，你的留言我会在稍晚的时候回复。'
    expireTime = 600
    rd.delete('syncData', 'repliedMsg')
    w.accountLogin()
    w.accountInit()
    print '=== %s ===\n' % (w.nickName)
    firendsUserName = [contact['UserName']
                       for contact in w.wx_memberList if isPerson(contact)]
    rd.set('wx_daemon', 1)
    while rd.exists('wx_daemon'):
        resp = rd.rpop('syncData')
        if resp:
            resp = json.loads(resp)
            for msg in resp['AddMsgList']:
                timeStamp = genTimeStamp(10)
                if rd.hexists('repliedMsg', msg['MsgId']):
                    continue
                if msg['ToUserName'] != w.wx_params['user_name']:
                    continue
                fromUserName = msg['FromUserName']
                if (fromUserName in firendsUserName) and (not rd.get(fromUserName)):
                    ret = handle(w.sendTextMsg(fromUserName, answer))
                    rd.hset('repliedMsg', msg['MsgId'], 1)
                    rd.set(fromUserName, 1, ex=expireTime)
                    msgLog = '[%s] - %s - %s\n' % (
                        strftime('%d/%b/%Y %H:%M:%S', localtime()),
                        w.wx_memberDict[fromUserName]['NickName'],
                        ret
                    )
                    print msgLog.strip()
                    with codecs.open('msg.log', 'a+', 'utf-8') as f:
                        f.write(msgLog)
                    f.close()
                sleep(7)
