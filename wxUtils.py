#!/usr/bin/env python
# -*- coding:utf-8 -*
from time import time
from random import randint
from PIL import Image
from StringIO import StringIO
import re


def genTimeStamp(length):
    t = '%d' % (time() * 10 ** (length - 10))
    return t


def genRandint(length):
    r = randint(10 ** (length - 1), 10 ** length - 1)
    return r


def displayImage(content):
    Image.open(StringIO(content)).show()
    return


def isPerson(contact):
    if '@@' in contact['UserName']:
        return False
    elif contact['UserName'] in ['filehelper', 'fmessage', 'mphelper',  'weixin', 'weixingongzhong', 'wxzhifu']:
        return False
    elif contact['VerifyFlag'] & 8 != 0:
        return False
    elif contact['KeyWord'] == 'gh_':
        return False
    else:
        return True


def removeEmoji(content):
    content = re.sub(r'</?span[^>]*>|[\r\n\t]', ' ', content)
    content = content.replace('&amp;', '&').strip()
    return content


def convertGender(sex):
    if sex == 1:
        gender = u'男'
    elif sex == 2:
        gender = u'女'
    else:
        gender = ''
    return gender


def isFriend(friendsUserName, userName):
    try:
        if userName in friendsUserName:
            val = u'是'
        else:
            val = u'否'
    except:
        val = ''
    return val


def pickScreenName(NickName, RemarkName):
    if RemarkName:
        return removeEmoji(RemarkName)
    else:
        return removeEmoji(NickName)


def formatQuanPin(PYQuanPin, RemarkPYQuanPin):
    PYQuanPin = re.sub(r'spanclassemojiemoji\w{5}span|\?', '~', PYQuanPin.strip())
    PYQuanPin = re.sub(r'~+', '~', PYQuanPin)
    RemarkPYQuanPin = re.sub(r'spanclassemojiemoji\w{5}span|\?', '~', RemarkPYQuanPin.strip())
    RemarkPYQuanPin = re.sub(r'~+', '~', RemarkPYQuanPin)
    if RemarkPYQuanPin:
        return RemarkPYQuanPin.lower()
    elif PYQuanPin:
        return PYQuanPin.lower()
    else:
        return '~'


if __name__ == '__main__':
    pass
