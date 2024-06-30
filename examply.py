# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 21:02:26 2023

@author: LTtx
"""
import time
#导入客户端
from tx import *

#创建对应的实例
tx1 = txl('192.168.1.65',2049,'LTtx')#对应的信息根据自己部署服务端时填写的内容做相应的变更

#开启start_tx()功能后可以使用put、get、push等方法进行数据推送
tx1.start_tx()

# #可以关闭start_tx()的功能、一般用不到，关闭后需要再开启才能使用
# tx1.close_tx()

# #再次开启start_tx()
# tx1.start_tx()

#使用put()方法把本地变量推送到服务端（云变量）

#创建一个列表
tem_list = [1,'2',4,{'a':'cc','b':80}]

#推送列表到云端
tx1.put('test_list',tem_list)

#如果想要删除这个数据，再推送一个"test"，赋值为“”空字符串即可。

#从云端拉取这个刚刚推送的云变量并赋值给cc对象
cc = tx1.get('test_list')
#打印这个get的变量
print(cc,type(cc))

##接下来开始使用start_txg()的功能
#开启start_txg(channel)功能，channel为信道名称，表示你要接收哪个信道的消息
tx1.start_txg('test')

#我们现在往“test"信道内发送一条消息
#push（var,data,who），var表示消息头，data为具体的内容，是一个字符串，who表示要哪个信道进行数据推送
tx1.push('消息头','this is a test,这是一条测试消息','test')

#我们通过tx1.Q这个队列对象来获取我们刚刚发送的消息 
print('start_txg功能收到的数据为：')
print(tx1.Q.get())  #他的数据结构为var|data,可以通过|线切割，根据var头是否是自己想要的数据来进行下一步处理

##接下来我们演示如何进行大批量数据推送，也就是我们常用的股票行情推送
print('将在10秒后测试大通量数据推送')
time.sleep(10)
#首先导入一个子线程库，用来显示收到的数据
import threading

#定一个函数，用来打印收到的数据
def show():
    while True:
        print(tx1.Q.get())

threading.Thread(target = show).start()

#此时我们模拟推送一万条数据
num = 10000
for i in range(num):
    tx1.push('test',str(i),'test')#注意推送的消息中全是字符串
time.sleep(3)
#对于文件传输的演示也非常简单，直接调用方法即可，本处不再演示，本数据中心的核心功能是消息推送与数据云存储

print('想体验更多start_txg()的功能，请分别运行show.py和push_test.py。注意调整好对应的服务端参数')

print('#'*5,'所有演示完毕，祝您使用愉快！如果对你有帮助，请帮忙在github上点一下star哦，万分感谢！','#'*5,)
print('后续会上传更多的进阶使用示例，敬请期待')






