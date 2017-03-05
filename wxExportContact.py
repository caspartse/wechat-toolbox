#!/usr/bin/env python
# -*- coding:utf-8 -*
from wxCommon import WebChat
from wxUtils import *
from orderedset import OrderedSet
from time import strftime, localtime
import xlsxwriter


def saveContactFile(memberList):
    _data = [(u'昵称', u'微信号', u'备注名', u'性别', u'省份', u'城市', u'签名')]
    for contact in memberList:
        if not isPerson(contact):
            continue
        info = (
            removeEmoji(contact['NickName']),
            contact['Alias'],
            removeEmoji(contact['RemarkName']),
            convertGender(contact['Sex']),
            contact['Province'],
            contact['City'],
            removeEmoji(contact['Signature'])
        )
        _data.append(info)
    filename = u'%s_微信好友_%s.xlsx' % (
        removeEmoji(w.nickName),
        strftime('%Y%m%d-%H%M%S', localtime()),
    )
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()
    row = 0
    col = 0
    for nickName, alias, remarkName, gender, province, city, signature in OrderedSet(_data):
        worksheet.write(row, col, nickName)
        worksheet.write(row, col + 1, alias)
        worksheet.write(row, col + 2, remarkName)
        worksheet.write(row, col + 3, gender)
        worksheet.write(row, col + 4, province)
        worksheet.write(row, col + 5, city)
        worksheet.write(row, col + 6, signature)
        row += 1
    workbook.close()
    return row


if __name__ == '__main__':
    w = WebChat()
    w.accountLogin()
    w.accountInit()
    print '=== %s ===\n' % (w.nickName)
    count = saveContactFile(w.wx_memberList)
    print 'total: %d' % (count)
