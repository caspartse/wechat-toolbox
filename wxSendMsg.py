#!/usr/bin/env python
# -*- coding: utf-8 -*
from wxCommon import WebChat
import re
from time import time, sleep


def handle(self, resp):
    try:
        ret = resp.json()['BaseResponse']['Ret']
    except:
        print 'Error.'
    if ret == 0:
        print 'OK.'
    elif ret == 1205:
        endTime = time() + 600
        while time() < endTime:
            print 'Sleep...'
            sleep(30)
    else:
        print 'Error.'
    return


if __name__ == '__main__':
    w = WebChat(daemon=True)
    w.accountLogin()
    w.accountInit()
    print '=== %s ===\n' % (w.nickName)
    # Send to Friends
    firends = [contact for contact in w.contactList if '@@' not in contact['UserName']]
    total = len(firends)
    for index, firend in enumerate(firends):
        print '[%d/%d] %s' % (index + 1, total, re.sub(r'</?span[^>]*>', '', firend['NickName']))
        w.handle(w.sendTextMsg(firend['UserName'], u'转发这条锦鲤'))
        w.handle(w.sendImage(firend['UserName'], 'Koi.jpg'))
        sleep(7)
    # Send to Groups
    groups = [contact for contact in w.contactList if '@@' in contact['UserName']]
    total = len(groups)
    for index, group in enumerate(groups):
        print '[%d/%d] %s' % (index + 1, total, re.sub(r'</?span[^>]*>', '', group['NickName']))
        w.handle(w.sendTextMsg(group['UserName'], u'转发这条锦鲤'))
        w.handle(w.sendImage(group['UserName'], 'Koi.jpg'))
        sleep(7)
