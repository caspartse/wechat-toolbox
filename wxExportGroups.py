#!/usr/bin/env python
# -*- coding:utf-8 -*
from wxCommon import WebChat
from wxUtils import *
from time import strftime, localtime
import xlsxwriter


w = WebChat()


def queryGMemberList(gUserName):
    queryList = [{'UserName': gUserName, 'EncryChatRoomId': ''}]
    resp = w.batchGetContact(queryList)
    data = json.loads(resp.content)
    memberList = data['ContactList'][0]['MemberList']
    queryList = [{'UserName': m['UserName'], 'EncryChatRoomId': gUserName} for m in memberList]
    gMemberList = []
    chunks = [queryList[i:i + 50] for i in range(0, len(queryList), 50)]
    for chunk in chunks:
        resp = w.batchGetContact(chunk)
        data = json.loads(resp.content)
        gMemberList.extend(data['ContactList'])
    return gMemberList


def saveGroupFile(groups, firends):
    friendsUserName = [contact['UserName'] for contact in firends]
    for group in groups:
        gMemberList = queryGMemberList(group['UserName'])
        _data = [(u'昵称', u'微信号', u'群名片', u'是否好友', u'备注名', u'性别', u'省份', u'城市', u'签名')]
        for contact in gMemberList:
            info = (
                removeEmoji(contact['NickName']),
                contact['Alias'],
                removeEmoji(contact['DisplayName']),
                isFriend(friendsUserName, contact['UserName']),
                removeEmoji(contact['RemarkName']),
                convertGender(contact['Sex']),
                contact['Province'],
                contact['City'],
                removeEmoji(contact['Signature'])
            )
            _data.append(info)
        filename = u'%s_群成员_%s.xlsx' % (
            removeEmoji(group['NickName']),
            strftime('%Y%m%d-%H%M%S', localtime()),
        )
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        row = 0
        col = 0
        for nickName, alias, displayName, friend, remarkName, gender, province, city, signature in _data:
            worksheet.write(row, col, nickName)
            worksheet.write(row, col + 1, alias)
            worksheet.write(row, col + 2, displayName)
            worksheet.write(row, col + 3, friend)
            worksheet.write(row, col + 4, remarkName)
            worksheet.write(row, col + 5, gender)
            worksheet.write(row, col + 6, province)
            worksheet.write(row, col + 7, city)
            worksheet.write(row, col + 8, signature)
            row += 1
        workbook.close()
        print '%s: %d' % (removeEmoji(group['NickName']), row - 1)
    return


if __name__ == '__main__':
    w.accountLogin()
    w.accountInit()
    print '=== %s ===\n' % (w.nickName)
    firends = [contact for contact in w.wx_memberList if isPerson(contact)]
    groups = [contact for contact in w.wx_memberList if '@@' in contact['UserName']]
    saveGroupFile(groups, firends)
