#!/usr/bin/env python
# -*- coding:utf-8 -*
from time import time, strftime, localtime
from random import randint
from PIL import Image
from StringIO import StringIO
import re
import codecs


def genTimeStamp(length):
    t = '%d' % (time() * 10 ** (length - 10))
    return t


def genRString():
    r = str(~ int(bin(int(time() * 1000))[-32:], 2))
    return r


def genRandint(length):
    r = str(randint(10 ** (length - 1), 10 ** length - 1))
    return r


def genDeviceId():
    e = 'e%s' % (genRandint(15))
    return e


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
    PYQuanPin = re.sub(
        r'spanclassemojiemoji\w{5}span|\?', '`', PYQuanPin.strip())
    if re.match(r'^\d', PYQuanPin):
        PYQuanPin = '`' + PYQuanPin
    PYQuanPin = re.sub(r'`+', '`', PYQuanPin)
    RemarkPYQuanPin = re.sub(
        r'spanclassemojiemoji\w{5}span|\?', '`', RemarkPYQuanPin.strip())
    if re.match(r'^\d', RemarkPYQuanPin):
        RemarkPYQuanPin = '`' + RemarkPYQuanPin
    RemarkPYQuanPin = re.sub(r'`+', '`', RemarkPYQuanPin)
    if RemarkPYQuanPin:
        return RemarkPYQuanPin.lower()
    elif PYQuanPin:
        return PYQuanPin.lower()
    else:
        return '`'


def writeLog(nickName, status):
    wxLog = '[%s] - %s - %s\n' % (
        strftime('%d/%b/%Y %H:%M:%S', localtime()),
        nickName,
        status
    )
    with codecs.open('wx.log', 'a+', 'utf-8') as f:
        f.write(wxLog)
    f.close()


if __name__ == '__main__':
    pass
