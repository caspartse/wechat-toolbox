#!/usr/bin/env python
# -*- coding:utf-8 -*
import sys
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
import imghdr
from hashlib import md5
from requests_toolbelt import MultipartEncoder
try:
    import redis
except ImportError:
    pass


mc = pylibmc.Client(['127.0.0.1:11211'])
rd = redis.Redis()


class WebChat(object):

    def __init__(self, daemon=False, flush=True):
        super(WebChat, self).__init__()
        if flush:
            mc.delete_multi(['wx_session', 'wx_params', 'wx_uuid'])
        self.daemon = daemon
        self.sess = mc.get('wx_session') or requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3'
        }
        self.sess.headers.update(headers)
        self.wx_params = mc.get('wx_params') or {}
        self.wx_uuid = mc.get('wx_uuid') or ''
        self.wx_version = mc.get('wx_version') or 1
        #self.sess.verify = False

    def fetchQRCode(self):
        mc.set('wx_stime', int(genTimeStamp(13)))
        url = 'https://login.wx.qq.com/jslogin'
        params = {
            'appid': 'wx782c26e4c19acffb',
            'redirect_uri': 'https%3A%2F%2Fwx.qq.com%2Fcgi-bin%2Fmmwebwx-bin%2Fwebwxnewloginpage',
            'fun': 'new',
            'lang': 'zh_CN',
            '_': str(mc.incr('wx_stime'))
        }
        resp = self.sess.get(url, params=params, timeout=10000)
        pattern = r'window\.QRLogin\.code\s?=\s?200;\s*window\.QRLogin\.uuid\s?=\s?"([^"]+)";'
        self.wx_uuid = re.search(pattern, resp.content).group(1)
        url = 'https://login.weixin.qq.com/qrcode/%s' % (self.wx_uuid)
        resp = self.sess.get(url, timeout=10000)
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
            url = 'https://login.wx.qq.com/cgi-bin/mmwebwx-bin/login'
            params = {
                'loginicon': 'true',
                'uuid': self.wx_uuid,
                'tip': '0',
                'r': genRString(),
                '_': str(mc.incr('wx_stime'))
            }
            resp = self.sess.get(url, params=params, timeout=10000)
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
            resp = self.sess.get(url, timeout=10000)
            cookies = self.sess.cookies.get_dict()
            self.wx_params.update(cookies)
            self.wx_params.update(
                {
                    'uin': cookies.get('wxuin'),
                    'sid': cookies.get('wxsid'),
                    'skey': '',
                    'pass_ticket': ''
                }
            )
        except:
            newUrl = url + '&fun=new&version=v2'
            resp = self.sess.get(newUrl, timeout=10000)
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
                }
            )
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        self.accountInit()
        return

    def accountInit(self):
        if self.wx_version == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit'
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxinit'
        params = {
            'r': genRString(),
            'pass_ticket': self.wx_params.get('pass_ticket', '')
        }
        payload = {
            'BaseRequest': {
                'Uin': self.wx_params['uin'],
                'Sid': self.wx_params['sid'],
                'Skey': self.wx_params.get('skey', ''),
                'DeviceID': genDeviceId()
            }
        }
        resp = self.sess.post(url, params=params,
                              data=json.dumps(payload), timeout=10000)
        content = resp.content
        data = json.loads(content)
        cookies = self.sess.cookies.get_dict()
        self.wx_params.update(cookies)
        self.wx_params.update(
            {
                'user_name': data['User']['UserName'],
                'skey': data['SKey'],
                'syncKey': data['SyncKey']
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
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact'
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact'
        params = {
            'r': genTimeStamp(13),
            'seq': '0',
            'skey': self.wx_params['skey'],
            'pass_ticket': self.wx_params.get('pass_ticket', '')
        }
        memberList = []
        while 1:
            try:
                resp = self.sess.get(url, params=params, timeout=100000)
                content = resp.content
                data = json.loads(content)
                if resp.status_code == 200:
                    memberList.extend(data['MemberList'])
                if data['Seq'] == 0:
                    break
                else:
                    params.updaut({'seq': str(data['Seq'])})
            except:
                pass
        self.wx_memberList = memberList
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
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxbatchgetcontact'
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxbatchgetcontact'
        params = {
            'type': 'ex',
            'r': genTimeStamp(13),
            'pass_ticket': self.wx_params.get('pass_ticket', '')
        }
        payload = {
            'BaseRequest': {
                'Uin': self.wx_params['uin'],
                'Sid': self.wx_params['sid'],
                'Skey': self.wx_params.get('skey', ''),
                'DeviceID': genDeviceId()
            },
            'Count': len(queryList),
            'List': queryList
        }
        resp = self.sess.post(url, params=params,
                              data=json.dumps(payload), timeout=10000)
        return resp

    def syncCheck(self):
        syncKeyString = '%7C'.join(['%s_%s' % (
            item['Key'], item['Val']) for item in self.wx_params['syncKey']['List']])
        if self.wx_version == 1:
            url = 'https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck'
        else:
            url = 'https://webpush.wx2.qq.com/cgi-bin/mmwebwx-bin/synccheck'
        params = {
            'r': genTimeStamp(13),
            'skey': self.wx_params.get('skey', ''),
            'sid': self.wx_params['sid'],
            'uin': self.wx_params['uin'],
            'deviceid': genDeviceId(),
            'synckey': syncKeyString,
            '_': str(mc.incr('wx_stime'))
        }
        resp = self.sess.get(url, params=params, timeout=10000)
        cookies = self.sess.cookies.get_dict()
        self.wx_params.update(cookies)
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        return resp

    def wxSync(self):
        if self.wx_version == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync'
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxsync'
        params = {
            'sid': self.wx_params['sid'],
            'skey': self.wx_params.get('skey', '')
        }
        payload = {
            'BaseRequest': {
                'Uin': self.wx_params['uin'],
                'Sid': self.wx_params['sid'],
                'Skey': self.wx_params.get('skey', ''),
                'DeviceID': genDeviceId()
            },
            'SyncKey': self.wx_params['syncKey'],
            'rr': genRString()
        }
        resp = self.sess.post(url, params=params,
                              data=json.dumps(payload), timeout=10000)
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
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg?pass_ticket=' + \
                self.wx_params['pass_ticket']
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg?pass_ticket=' + \
                self.wx_params['pass_ticket']
        timeStamp = genTimeStamp(17)
        payload = {
            'BaseRequest': {
                'Uin': int(self.wx_params['uin']),
                'Sid': self.wx_params['sid'],
                'Skey': self.wx_params['skey'],
                'DeviceID': genDeviceId()
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
            payload, ensure_ascii=False).encode('utf-8'), timeout=10000)
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
                'DeviceID': genDeviceId()
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
            url, headers=headers, data=m, timeout=10000)
        mediaId = json.loads(resp.content).get('MediaId')
        cookies = self.sess.cookies.get_dict()
        self.wx_params.update(cookies)
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        return mediaId

    def sendImage(self, userName, fileName=None):
        mediaId = self.uploadImage(userName, fileName)
        if self.wx_version == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsgimg'
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsgimg'
        params = {
            'fun': 'async',
            'f': 'json',
            'pass_ticket': self.wx_params['pass_ticket']
        }
        timeStamp = genTimeStamp(17)
        payload = {
            'BaseRequest': {
                'Uin': int(self.wx_params['uin']),
                'Sid': self.wx_params['sid'],
                'Skey': self.wx_params['skey'],
                'DeviceID': genDeviceId()
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
        resp = self.sess.post(url, params=params, data=json.dumps(
            payload, ensure_ascii=False).encode('utf-8'), timeout=10000)
        cookies = self.sess.cookies.get_dict()
        self.wx_params.update(cookies)
        mc.set('wx_session', self.sess)
        mc.set('wx_params', self.wx_params)
        return resp

    def accountLogout(self):
        if self.wx_version == 1:
            url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxlogout'
        else:
            url = 'https://wx2.qq.com/cgi-bin/mmwebwx-bin/webwxlogout'
        params = {
            'redirect': '1',
            'type': '1',
            'skey': self.wx_params.get('skey', '')
        }
        payload = {
            'sid': self.wx_params['sid'],
            'uin': self.wx_params['uin']
        }
        self.sess.post(url, params=params, data=payload, timeout=10000)
        return

    def wxDaemon(self):
        while 1:
            if not self.wx_params.get('syncKey'):
                self.accountLogout()
                status = 'Shutdown (-1)'
                selector = '-1'
            else:
                try:
                    resp = self.syncCheck()
                    pattern = r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}'
                    retcode, selector = re.findall(pattern, resp.content)[0]
                    if retcode == '0':
                        status = 'Running'
                    elif retcode in ['1101', '1102']:
                        self.accountLogout()
                        status = 'Shutdown (-2)'
                        selector = '-2'
                    else:
                        status = str(retcode)
                except Exception, e:
                    status = e
                    selector = '0'
            writeLog(self.nickName, status)
            if int(selector) > 0:
                try:
                    resp = self.wxSync()
                    rd.lpush('syncData', resp.content)
                except Exception, e:
                    writeLog(self.nickName, e)
            elif int(selector) < 0:
                mc.delete_multi(['wx_session', 'wx_params', 'wx_uuid'])
                rd.delete('wx_daemon')
                sys.exit(1)
            sleep(20)


if __name__ == '__main__':
    pass
