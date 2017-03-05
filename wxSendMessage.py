#!/usr/bin/env python
# -*- coding: utf-8 -*
from wxCommon import WebChat
from wxUtils import *
from time import time, sleep


w = WebChat(daemon=True)


def handle(resp):
    try:
        ret = resp.json()['BaseResponse']['Ret']
    except:
        print 'Error.'
    if ret == 0:
        print 'OK.'
    elif ret == 1205:
        endTime = time() + 720
        while time() < endTime:
            print 'Sleep...'
            sleep(30)
    else:
        print 'Error.'
    return


if __name__ == '__main__':
    w.accountLogin()
    w.accountInit()
    print '=== %s ===\n' % (w.nickName)
    # Send to Friends
    firends = [contact for contact in w.wx_memberList if isPerson(contact)]
    total = len(firends)
    for index, firend in enumerate(firends):
        print '[%d/%d] %s' % (index + 1, total, removeEmoji(firend['NickName']))
        handle(w.sendTextMsg(firend['UserName'], u'转发这条锦鲤'))
        handle(w.sendImage(firend['UserName'], 'Koi.jpg'))
        sleep(7)
    # Send to Groups
    groups = [contact for contact in w.wx_memberList if '@@' in contact['UserName']]
    total = len(groups)
    for index, group in enumerate(groups):
        print '[%d/%d] %s' % (index + 1, total, removeEmoji(group['NickName']))
        handle(w.sendTextMsg(group['UserName'], u'转发这条锦鲤'))
        handle(w.sendImage(group['UserName'], 'Koi.jpg'))
        sleep(7)
