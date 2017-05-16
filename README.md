# wechat-toolbox
WeChat toolbox（微信工具箱）

# Features

## wxExportContact.py
* 导出微信通讯录好友（昵称、备注名、显示名、~~微信号~~、性别、省份、城市、签名）
* 为方便阅读及显示，已移除昵称、备注名中的 Emoji 等特殊内容
* 显示名：备注名非空为备注名，反之为昵称
* ~~隐私设置缘故，部分微信号无法获取~~ （微信版本升级，已无法获取微信号）
* 通讯录按显示名全拼升序排列，特殊类型置于末尾

online demo: [http://kagent.applinzi.com/wx](http://kagent.applinzi.com/wx)

## wxExportGroups.py
* 导出群成员名单（昵称、~~微信号~~、群名片、是否好友、备注名、性别、省份、城市、签名）
* 只能读取已保存至通讯录的群聊
* 群成员按进群时间升序排序

## wxSendMessage.py
* 向好友或微信群发送文本、图片消息
* 只能读取已保存至通讯录的群聊
* 连续发送约 100 次后，会受到限制，约 1 小时后才能复活正常


# External Resources
* [Memcached](https://memcached.org/)
* [XlsxWriter](https://xlsxwriter.readthedocs.io/)


# Changelog
v0.1.4
---
May 17, 2017
* Bug fix
* Sort contact list and add  "ScreenName" field

v0.1.3
---
May 14, 2017
* Update README file
* Add online demo (wxExportContact)

v0.1.2
---
Mar 5, 2017

* Add wxExportContact module
* Add wxExportGroups module
* Bug fix

v0.1.1
---
Feb 1, 2017

* Add some common files

v0.1.0
---
Nov 26, 2016

* Initial release
