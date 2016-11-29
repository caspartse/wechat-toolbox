#!/usr/bin/env python
# -*- coding: utf-8 -*

import sys
import requests
from time import time, sleep, strftime, localtime
import re
from PIL import Image
from StringIO import StringIO
from multiprocessing import Process
from random import randint
import simplejson as json
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import imghdr
from hashlib import md5
from requests_toolbelt import MultipartEncoder


class WebChat(object):
    """docstring for WebChat"""

    def __init__(self):
        super(WebChat, self).__init__()
        self.sess = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
        }
        self.sess.headers.update(headers)
        self.params = {}
        self.wxInitVersion = 1
        self.mediaId = None
        #self.sess.verify = False

    def genTimeStamp(self, length):
        t = '%d' % (time() * 10 ** (length - 10))
        return t

    def genRandom(self, length):
        r = randint(10 ** (length - 1), 10 ** length - 1)
        return r

    def displayQRCode(self, content):
        Image.open(StringIO(content)).show()
        return

    def accountLogin(self):
        url = 'https://login.wx.qq.com/jslogin?appid=wx782c26e4c19acffb&redirect_uri=https%3A%2F%2Fwx.qq.com%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxnewloginpage&fun=new&lang=en_US&_=' + \
            self.genTimeStamp(13)
        resp = self.sess.get(url, timeout=1000)
        content = resp.content
        pattern = r'window\.QRLogin\.code\s?=\s?200;\s*window\.QRLogin\.uuid\s?=\s?"([^\s]{12})";'
        uuid = re.search(pattern, content).group(1)
        url = 'https://login.weixin.qq.com/qrcode/%s' % (uuid)
        resp = self.sess.get(url, timeout=1000)
        content = resp.content
        p = Process(target=self.displayQRCode(content))
        p.start()
        while True:
            sleep(0.25)
            url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?loginicon=true&uuid=%s&tip=0&r=-%s&_=%s' % (
                uuid, self.genRandom(9), self.genTimeStamp(13))
            resp = self.sess.get(url, timeout=1000)
            content = resp.content
            if ('window.code=200;' in content):
                p.terminate()
                break
            elif ('window.code=400;' in content):
                sys.exit(1)
        pattern = r'window\.code=200;\s+window\.redirect_uri="([^\s]+)";'
        url = re.search(pattern, content).group(1)
        if 'wx2.qq.com' in url:
            self.wxInitVersion = 2
        else:
            self.wxInitVersion = 1
        try:
            newUrl = url + '&fun=new&version=v2'
            resp = self.sess.get(newUrl, timeout=1000)
            content = resp.content
            root = ET.fromstring(content)
            self.params.update(
                {
                    'skey': root.find('skey').text,
                    'uin': root.find('wxuin').text,
                    'sid': root.find('wxsid').text,
                    'pass_ticket': root.find('pass_ticket').text,
                    'device_id': 'e%s' % (self.genRandom(15))
                }
            )
            self.params.update(self.sess.cookies.get_dict())
        except:
            resp = self.sess.get(url, timeout=1000)
            content = resp.content
            cookies = self.sess.cookies.get_dict()
            self.params.update(
                {
                    'uin': cookies.get('wxuin'),
                    'sid': cookies.get('wxsid'),
                    'device_id': 'e%s' % (self.genRandom(15)),
                    'skey': '',
                    'pass_ticket': ''
                }
            )
        return

    def accountInit(self):
        if self.wxInitVersion == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=-%s&pass_ticket=%s' % (
                self.genRandom(9), self.params.get('pass_ticket', ''))
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=-%s' % (
                self.genRandom(9))
        payload = {
            'BaseRequest':
            {
                'Uin': self.params['uin'],
                'Sid': self.params['sid'],
                'Skey': self.params.get('skey', ''),
                'DeviceID': self.params['device_id']
            }
        }
        resp = self.sess.post(
            url, data=json.dumps(payload), timeout=1000)
        content = resp.content
        data = json.loads(content)
        self.nickName = data['User']['NickName']
        syncKey = data['SyncKey']
        syncKey = ['%s_%s' % (item['Key'], item['Val'])
                   for item in syncKey['List']]
        syncKey = '%7C'.join(syncKey)
        self.params.update(
            {
                'user_name': data['User']['UserName'],
                'skey': data['SKey'],
                'syncKey': syncKey
            }
        )
        if self.wxInitVersion == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?pass_ticket=%s&r=%s&seq=0&skey=%s' % (
                self.params.get('pass_ticket', ''),
                self.genTimeStamp(13),
                self.params['skey']
            )
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?r=%s&seq=0&skey=%s' % (
                self.genTimeStamp(13),
                self.params['skey']
            )
        resp = self.sess.get(url, timeout=1000)
        content = resp.content
        data = json.loads(content)
        self.contactList = data['MemberList']
        self.params.update(self.sess.cookies.get_dict())
        return

    def sendTextMsg(self, userName, text):
        if self.wxInitVersion == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg?pass_ticket=%s' % (
                self.params['pass_ticket'])
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg'
        timeStamp = self.genTimeStamp(17)
        payload = {
            'BaseRequest': {
                'Uin': int(self.params['uin']),
                'Sid': self.params['sid'],
                'Skey': self.params['skey'],
                'DeviceID': self.params['device_id']
            },
            'Msg': {
                'Type': 1,
                'Content': text,
                'FromUserName': self.params['user_name'],
                'ToUserName': userName,
                'LocalID': timeStamp,
                'ClientMsgId': timeStamp,
            }
        }
        resp = self.sess.post(url, data=json.dumps(
            payload, ensure_ascii=False).encode('utf-8'), timeout=1000)
        return resp

    def uploadImage(self, userName, fileName):
        if self.wxInitVersion == 1:
            url = 'https://file.wx.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmedia?f=json'
        else:
            url = 'https://file.wx2.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmedia?f=json'
        img = open(fileName, 'rb').read()
        imgLen = len(img)
        mimeType = 'image/%s' % (imghdr.what(fileName))
        payload = {
            'UploadType': 2,
            'BaseRequest': {
                'Uin': int(self.params['uin']),
                'Sid': self.params['sid'],
                'Skey': self.params['skey'],
                'DeviceID': self.params['device_id']
            },
            'ClientMediaId': int(self.genTimeStamp(13)),
            'TotalLen': imgLen,
            'StartPos': 0,
            'DataLen': imgLen,
            'MediaType': 4,
            'FromUserName': self.params['user_name'],
            'ToUserName': userName,
            'FileMd5': md5(str(time())).hexdigest()  # fake
        }
        fields = {
            'id': 'WU_FILE_0',
            'name': '%d.%s' % (time(), imghdr.what(fileName)),  # fake
            'type': mimeType,
            # fake
            'lastModifiedDate': strftime('%a %b %d %Y %H:%M:%S GMT+0800 (SCT)', localtime()),
            'size': str(imgLen),
            'mediatype': 'pic',
            'uploadmediarequest': json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            'webwx_data_ticket': self.params.get('webwx_data_ticket', ''),
            'pass_ticket': self.params.get('pass_ticket', ''),
            'filename': ('filename', open(fileName, 'rb'), mimeType),
        }
        m = MultipartEncoder(fields)
        headers = self.sess.headers
        headers.update({'Content-Type': m.content_type})
        resp = self.sess.post(
            url, headers=headers, data=m, timeout=1000)
        self.mediaId = resp.json()['MediaId']
        return self.mediaId

    def sendImage(self, userName, fileName):
        mediaId = self.mediaId
        if not self.mediaId:
            mediaId = self.uploadImage(userName, fileName)
        if self.wxInitVersion == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsgimg?fun=async&f=json&pass_ticket=%s' % (
                self.params['pass_ticket'])
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsgimg?fun=async&f=json'
        timeStamp = self.genTimeStamp(17)
        payload = {
            'BaseRequest': {
                'Uin': int(self.params['uin']),
                'Sid': self.params['sid'],
                'Skey': self.params['skey'],
                'DeviceID': self.params['device_id']
            },
            'Msg': {
                'Type': 3,
                'MediaId': mediaId,
                'FromUserName':  self.params['user_name'],
                'ToUserName': userName,
                'LocalID': timeStamp,
                'ClientMsgId': timeStamp
            }
        }
        resp = self.sess.post(url, data=json.dumps(
            payload, ensure_ascii=False).encode('utf-8'), timeout=1000)
        return resp

    def heartbeat(self):
        if self.wxInitVersion == 1:
            url = 'https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck?'
        else:
            url = 'https://webpush.wx2.qq.com/cgi-bin/mmwebwx-bin/synccheck?'
        params = 'r=%s&skey=%s&sid=%s&uin=%s&deviceid=%s&synckey=%s&_=%s' % (
            self.genTimeStamp(13),
            self.params['skey'],
            self.params['sid'],
            self.params['uin'],
            self.params['device_id'],
            self.params['syncKey'],
            self.genTimeStamp(13)
        )
        url = url + params
        resp = self.sess.get(url, timeout=1000)
        return resp.status_code

    def handle(self, resp):
        try:
            ret = resp.json()['BaseResponse']['Ret']
        except:
            print 'Error.'
        if ret == 0:
            print 'OK.'
        elif ret == 1205:
            self.mediaId = None
            endTime = time() + 300
            while time() < endTime:
                print 'Sleep... <%s>' % (self.heartbeat())
                sleep(30)
        else:
            print 'Error.'
        return


if __name__ == '__main__':
    w = WebChat()
    w.accountLogin()
    w.accountInit()
    print '=== %s ===\n' % (w.nickName)
    groups = [contact for contact in w.contactList if '@@' in contact['UserName']]
    total = len(groups)
    for index, group in enumerate(groups):
        print '[%d/%d] %s' % (index + 1, total, re.sub(r'</?span[^>]*>', '', group['NickName']))
        w.handle(w.sendTextMsg(group['UserName'], u'我能吞下玻璃而不伤身体'))
        w.handle(w.sendImage(group['UserName'], 'test.png'))
        sleep(6)
