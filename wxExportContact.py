#!/usr/bin/env python
# -*- coding:utf-8 -*
from wxCommon import WebChat
from wxUtils import *
from orderedset import OrderedSet
from time import strftime, localtime
import xlsxwriter


w = WebChat()


def saveContactFile(memberList):
    _data = [(u'昵称', u'备注名', u'显示名', u'微信号', u'性别', u'省份', u'城市', u'签名', ' ')]
    for contact in memberList:
        if not isPerson(contact):
            continue
        info = (
            removeEmoji(contact['NickName']),
            removeEmoji(contact['RemarkName']),
            pickScreenName(contact['NickName'], contact['RemarkName']),
            contact['Alias'],
            convertGender(contact['Sex']),
            contact['Province'],
            contact['City'],
            removeEmoji(contact['Signature']),
            formatQuanPin(contact['PYQuanPin'], contact['RemarkPYQuanPin'])
        )
        _data.append(info)
    _data.sort(key=lambda x: x[-1])
    _data = [e[:-1] for e in _data]
    filename = u'%s_微信好友_%s.xlsx' % (
        removeEmoji(w.nickName),
        strftime('%Y%m%d-%H%M%S', localtime()),
    )
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()
    row = 0
    col = 0
    for nickName, remarkName, screenName, alias, gender, province, city, signature in OrderedSet(_data):
        worksheet.write(row, col, nickName)
        worksheet.write(row, col + 1, remarkName)
        worksheet.write(row, col + 2, screenName)
        worksheet.write(row, col + 3, alias)
        worksheet.write(row, col + 4, gender)
        worksheet.write(row, col + 5, province)
        worksheet.write(row, col + 6, city)
        worksheet.write(row, col + 7, signature)
        row += 1
    workbook.close()
    print 'total: %d' % (row - 1)
    return


if __name__ == '__main__':
    w.accountLogin()
    w.accountInit()
    print '=== %s ===\n' % (w.nickName)
    saveContactFile(w.wx_memberList)
