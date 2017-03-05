# wechat-toolbox
WeChat toolbox.

# Features

## wxExportContact.py
* 导出微信通讯录好友（昵称、微信号、备注名、性别、省份、城市、签名）
* 隐私设置缘故，部分微信号无法获取

## wxExportGroups.py
* 导出群成员名单（昵称、微信号、群名片、是否好友、备注名、性别、省份、城市、签名）
* 只能导出已保存至通讯录的群聊
* 群成员按进群时间升序排序

## wxSendMessage.py
* 向好友或微信群发送文本、图片消息
* 只能读取已保存至通讯录的群
* 连续发送约 100 次后，会受到限制，约 1 小时后才能复活正常

# Changelog

v0.1.2
---
Mar 5, 2017

* Add wxExportContact module
* 
* Bug fix

v0.1.1
---
Feb 1, 2017

* Add some common files

v0.1.0
---
Nov 26, 2016

* Initial release
