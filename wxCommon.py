#!/usr/bin/env python
# -*- coding:utf-8 -*
from wxUtils import *
import pylibmc
import requests
import re
import threading
from time import sleep, strftime, localtime
try:
    import simplejson as json
except ImportError:
    import json
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import codecs
import imghdr
from hashlib import md5
from requests_toolbelt import MultipartEncoder


mc = pylibmc.Client(['127.0.0.1:11211'])


class WebChat(object):

    def __init__(self, daemon=False):
        super(WebChat, self).__init__()
        self.daemon = daemon
        self.sess = mc.get('wx_session') or requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:53.0) Gecko/20100101 Firefox/53.0',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3'
        }
        self.sess.headers.update(headers)
        self.wx_params = mc.get('wx_params') or {}
        self.wx_uuid = mc.get('wx_uuid') or ''
        self.wx_version = mc.get('wx_version') or 1
        #self.sess.verify = False

    def fetchQRCode(self):
        url = 'https://login.wx.qq.com/jslogin?appid=wx782c26e4c19acffb&redirect_uri=https%3A%2F%2Fwx.qq.com%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxnewloginpage&fun=new&lang=zh_CN&_=' + \
            genTimeStamp(13)
        resp = self.sess.get(url, timeout=1000)
        pattern = r'window\.QRLogin\.code\s?=\s?200;\s*window\.QRLogin\.uuid\s?=\s?"([^"]+)";'
        self.wx_uuid = re.search(pattern, resp.content).group(1)
        url = 'https://login.weixin.qq.com/qrcode/%s' % (self.wx_uuid)
        resp = self.sess.get(url, timeout=1000)
        cookies = self.sess.cookies.get_dict()
        self.wx_params.update(cookies)
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        mc.set('wx_uuid', self.wx_uuid)
        return resp.content

    def accountLogin(self):
        QRCode = self.fetchQRCode()
        t1 = threading.Thread(target=displayImage, args=(QRCode,))
        t1.start()
        while 1:
            sleep(0.25)
            url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?loginicon=true&uuid=%s&tip=0&r=-%s&_=%s' % (
                self.wx_uuid,
                genRandint(9),
                genTimeStamp(13)
            )
            resp = self.sess.get(url, timeout=1000)
            content = resp.content
            if ('window.code=200;' in content):
                break
            elif ('window.code=400;' in content):
                sys.exit(1)
        pattern = r'window\.code=200;\s+window\.redirect_uri="([^"]+)";'
        url = re.search(pattern, content).group(1)
        if 'wx2.qq.com' in url:
            self.wx_version = 2
        else:
            self.wx_version = 1
        mc.set('wx_version', self.wx_version)
        try:
            newUrl = url + '&fun=new&version=v2'
            resp = self.sess.get(newUrl, timeout=1000)
            cookies = self.sess.cookies.get_dict()
            self.wx_params.update(cookies)
            content = resp.content
            root = ET.fromstring(content)
            self.wx_params.update(
                {
                    'skey': root.find('skey').text,
                    'uin': root.find('wxuin').text,
                    'sid': root.find('wxsid').text,
                    'pass_ticket': root.find('pass_ticket').text,
                    'device_id': 'e%s' % (genRandint(15))
                }
            )
        except:
            resp = self.sess.get(url, timeout=1000)
            cookies = self.sess.cookies.get_dict()
            self.wx_params.update(cookies)
            self.wx_params.update(
                {
                    'uin': cookies.get('wxuin'),
                    'sid': cookies.get('wxsid'),
                    'device_id': 'e%s' % (genRandint(15)),
                    'skey': '',
                    'pass_ticket': ''
                }
            )
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        self.accountInit()
        return

    def accountInit(self):
        if self.wx_version == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=-%s&pass_ticket=%s' % (
                genRandint(9), self.wx_params.get('pass_ticket', ''))
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxinit?r=-%s' % (
                genRandint(9))
        payload = {
            'BaseRequest':
            {
                'Uin': self.wx_params['uin'],
                'Sid': self.wx_params['sid'],
                'Skey': self.wx_params.get('skey', ''),
                'DeviceID': self.wx_params['device_id']
            }
        }
        resp = self.sess.post(url, data=json.dumps(payload), timeout=1000)
        content = resp.content
        data = json.loads(content)
        syncKey = data['SyncKey']
        cookies = self.sess.cookies.get_dict()
        self.wx_params.update(cookies)
        self.wx_params.update(
            {
                'user_name': data['User']['UserName'],
                'skey': data['SKey'],
                'syncKey': syncKey
            }
        )
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        self.nickName = data['User']['NickName']
        try:
            self.getContact()
        except:
            pass
        if self.daemon:
            t2 = threading.Thread(target=self.wxDaemon)
            t2.start()
        return

    def getContact(self):
        if self.wx_version == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?pass_ticket=%s&r=%s&seq=0&skey=%s' % (
                self.wx_params.get('pass_ticket', ''),
                genTimeStamp(13),
                self.wx_params['skey']
            )
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?r=%s&seq=0&skey=%s' % (
                genTimeStamp(13),
                self.wx_params['skey']
            )
        _memberList = []
        _seq = 0
        while 1:
            pattern = r'seq=\d+'
            url = re.sub(pattern, 'seq=' + str(_seq), url)
            try:
                resp = self.sess.get(url, timeout=10000)
                content = resp.content
                data = json.loads(content)
                if resp.status_code == 200:
                    _memberList.extend(data['MemberList'])
                    _seq = data['Seq']
                if str(_seq) == '0':
                    break
            except:
                pass
        self.wx_memberList = _memberList
        self.wx_memberDict = {contact['UserName']: contact for contact in self.wx_memberList}
        cookies = self.sess.cookies.get_dict()
        self.wx_params.update(cookies)
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        mc.set('wx_memberList', self.wx_memberList)
        mc.set('wx_memberDict', self.wx_memberDict)
        return

    def batchGetContact(self, queryList):
        # Max size of queryList: 50
        # queryList = [{'UserName': 'xxx', 'EncryChatRoomId': 'xxxx'}, {'UserName': 'xxx', 'EncryChatRoomId': ''},]
        if self.wx_version == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxbatchgetcontact?type=ex&r=%s&pass_ticket=%s' % (
                genTimeStamp(13), self.wx_params.get('pass_ticket', ''))
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxbatchgetcontact?type=ex&r=%s&pass_ticket=%s' % (
                genTimeStamp(13), self.wx_params.get('pass_ticket', ''))
        payload = {
            'BaseRequest': {
                'Uin': self.wx_params['uin'],
                'Sid': self.wx_params['sid'],
                'Skey': self.wx_params.get('skey', ''),
                'DeviceID': self.wx_params['device_id']
            },
            'Count': len(queryList),
            'List': queryList
        }
        resp = self.sess.post(url, data=json.dumps(payload), timeout=1000)
        data = json.loads(resp.content)
        return data

    def syncCheck(self):
        syncKeyString = '%7C'.join(['%s_%s' % (
            item['Key'], item['Val']) for item in self.wx_params['syncKey']['List']])
        if self.wx_version == 1:
            url = 'https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck?'
        else:
            url = 'https://webpush.wx2.qq.com/cgi-bin/mmwebwx-bin/synccheck?'
        params = 'r=%s&skey=%s&sid=%s&uin=%s&deviceid=%s&synckey=%s&_=%s' % (
            genTimeStamp(13),
            self.wx_params.get('skey', ''),
            self.wx_params['sid'],
            self.wx_params['uin'],
            self.wx_params['device_id'],
            syncKeyString,
            genTimeStamp(13)
        )
        url = url + params
        resp = self.sess.get(url, timeout=1000)
        cookies = self.sess.cookies.get_dict()
        self.wx_params.update(cookies)
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        return resp

    def wxSync(self):
        if self.wx_version == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync?sid=%s&skey=%s' % (
                self.wx_params['sid'],
                self.wx_params.get('skey', ''),
            )
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxsync?sid=%s&skey=%s' % (
                self.wx_params['sid'],
                self.wx_params.get('skey', ''),
            )
        payload = {
            'BaseRequest': {
                'Uin': self.wx_params['uin'],
                'Sid': self.wx_params['sid'],
                'Skey': self.wx_params.get('skey', ''),
                'DeviceID': self.wx_params['device_id']
            },
            'SyncKey': self.wx_params['syncKey'],
            'rr': '-%s' % (genRandint(9))
        }
        resp = self.sess.post(url, data=json.dumps(payload), timeout=1000)
        data = json.loads(resp.content)
        syncKey = data['SyncKey']
        cookies = self.sess.cookies.get_dict()
        self.wx_params.update(cookies)
        self.wx_params.update({'syncKey': syncKey})
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        return resp

    def sendTextMsg(self, userName, text):
        if self.wx_version == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg?pass_ticket=%s' % (
                self.wx_params['pass_ticket'])
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg'
        timeStamp = genTimeStamp(17)
        payload = {
            'BaseRequest': {
                'Uin': int(self.wx_params['uin']),
                'Sid': self.wx_params['sid'],
                'Skey': self.wx_params['skey'],
                'DeviceID': self.wx_params['device_id']
            },
            'Msg': {
                'Type': 1,
                'Content': text,
                'FromUserName': self.wx_params['user_name'],
                'ToUserName': userName,
                'LocalID': timeStamp,
                'ClientMsgId': timeStamp,
            }
        }
        resp = self.sess.post(url, data=json.dumps(
            payload, ensure_ascii=False).encode('utf-8'), timeout=1000)
        cookies = self.sess.cookies.get_dict()
        self.wx_params.update(cookies)
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        return resp

    def uploadImage(self, userName, fileName):
        if self.wx_version == 1:
            url = 'https://file.wx.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmedia?f=json'
        else:
            url = 'https://file.wx2.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmedia?f=json'
        img = open(fileName, 'rb').read()
        imgLen = len(img)
        mimeType = 'image/%s' % (imghdr.what(fileName))
        payload = {
            'UploadType': 2,
            'BaseRequest': {
                'Uin': int(self.wx_params['uin']),
                'Sid': self.wx_params['sid'],
                'Skey': self.wx_params['skey'],
                'DeviceID': self.wx_params['device_id']
            },
            'ClientMediaId': int(genTimeStamp(13)),
            'TotalLen': imgLen,
            'StartPos': 0,
            'DataLen': imgLen,
            'MediaType': 4,
            'FromUserName': self.wx_params['user_name'],
            'ToUserName': userName,
            # fake
            'FileMd5': md5(str(time())).hexdigest()
        }
        fields = {
            'id': 'WU_FILE_0',
            # fake
            'name': '%d.%s' % (time(), imghdr.what(fileName)),
            'type': mimeType,
            # fake
            'lastModifiedDate': strftime('%a %b %d %Y %H:%M:%S GMT+0800 (SCT)', localtime()),
            'size': str(imgLen),
            'mediatype': 'pic',
            'uploadmediarequest': json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            'webwx_data_ticket': self.wx_params.get('webwx_data_ticket', ''),
            'pass_ticket': self.wx_params.get('pass_ticket', ''),
            'filename': ('filename', open(fileName, 'rb'), mimeType),
        }
        m = MultipartEncoder(fields)
        headers = self.sess.headers
        headers.update({'Content-Type': m.content_type})
        resp = self.sess.post(
            url, headers=headers, data=m, timeout=1000)
        mediaId = resp.json()['MediaId']
        cookies = self.sess.cookies.get_dict()
        self.wx_params.update(cookies)
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        return mediaId

    def sendImage(self, userName, fileName=None):
        mediaId = self.uploadImage(userName, fileName)
        if self.wx_version == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsgimg?fun=async&f=json&pass_ticket=%s' % (
                self.wx_params['pass_ticket'])
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsgimg?fun=async&f=json'
        timeStamp = genTimeStamp(17)
        payload = {
            'BaseRequest': {
                'Uin': int(self.wx_params['uin']),
                'Sid': self.wx_params['sid'],
                'Skey': self.wx_params['skey'],
                'DeviceID': self.wx_params['device_id']
            },
            'Msg': {
                'Type': 3,
                'MediaId': mediaId,
                'FromUserName':  self.wx_params['user_name'],
                'ToUserName': userName,
                'LocalID': timeStamp,
                'ClientMsgId': timeStamp
            }
        }
        resp = self.sess.post(url, data=json.dumps(
            payload, ensure_ascii=False).encode('utf-8'), timeout=1000)
        cookies = self.sess.cookies.get_dict()
        self.wx_params.update(cookies)
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        return resp

    def accountLogout(self):
        if self.wx_version == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxlogout?redirect=1&type=1&skey=%s' % (
                self.wx_params.get('skey', ''))
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxlogout?redirect=1&type=1&skey=%s' % (
                self.wx_params.get('skey', ''))
        payload = {
            'Sid': self.wx_params['sid'],
            'Uin': self.wx_params['uin']
        }
        self.sess.post(url, data=payload, timeout=1000)
        return

    def wxDaemon(self):
        while 1:
            if not self.wx_params.get('syncKey'):
                status = 'Shutdown'
                selector = '-1'
            else:
                resp = self.syncCheck()
                pattern = r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}'
                retcode, selector = re.findall(pattern, resp.content)[0]
                if retcode == '0':
                    status = 'Running'
                elif retcode in ['1101', '1102']:
                    self.accountLogout()
                    return
                else:
                    status = 'None'
            wxLog = '[%s] - %s - %s\n' % (
                strftime('%d/%b/%Y %H:%M:%S', localtime()),
                self.nickName,
                status
            )
            with codecs.open('wx.log', 'a+', 'utf-8') as f:
                f.write(wxLog)
            f.close()
            if int(selector) > 0:
                self.wxSync()
            sleep(20)


if __name__ == '__main__':
    pass
