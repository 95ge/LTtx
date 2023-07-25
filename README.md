# LTtx
LTtx是一个分布式数据中心，基于Python语言开发，为分布式服务架构提供基础的通信服务。本项目代码完全开源，由于处于开源初期，相应的代码未完全整理，作者主要是用在股票量化的开发，在实际中，对于中国股市全市场Tick行情推送可以胜任。基于LTtx数据中心，可以实现许多程序的拆分，各个模块间相互独立，相互配合，也可以做成常用的服务端————客户端模型。在新版本中，新增文件传输功能，为实际开发提供更加全面的功能支持，此外本项目会根据实际生产环境需要，开发新的功能。
# 部署方式
1、本项目是基于服务端———客户端的架构方式，在使用时需要先运行服务端程序。启动方式也特别简单，git在对应的服务器（可以是Windows,Linux,只要能运行Python文件即可)后通过Python启动，如果是在Linux服务器中请留意放开对应的端口。

2、由于Python的GIL属性，服务端采用了大量的子线程进行功能实现，为保证性能发挥，建议部署在Linux服务器上，并且通过绑定核心运行的方法使用服务端性能达到最优。绑定核心启动命令示例：
```
taskset -c 2 python pg_server.py
```
本命令可将程序绑定在CPU2上。绑定核心后经本人测试发现在高并发时可以提高大约80%以上的性能。如果您的CPU是12代英特尔，请务必让他运行在性能（大核）核心上。

##

## 服务端部署命令
```
python pg_server.py
```
1、服务端特殊字段说明：port表示运行的端口，默认是2025可以通过修改pg_server.py对应的port变量完成。

2、服务端特殊字段说明：tocken表示认证口令，客户端在连接时需要传入该字段做身份认证。

3、对应的代码如下：

![图片](https://github.com/95ge/LTtx/assets/92923254/90a2b4fa-c7a0-4d8d-83b3-08191342a688)

##
## 函数方法说明
````
#需要提前执行start_tx()函数
tx1.put("a","b")                   #把云变量“a"赋值为“b",二者均为字符串，新版本中V3中将不再对b进行字符串数据类型进行限制。  

tx1.get("a")                       #获取云变量“a"的值。当put时传入的是一个Python对象，那么获得的值也是一个Python对象。  

tx1.dict_change(var,key,value)     #把云对象var字典对象进行key和value的更新，同本地字典操作方法一致。     

tx1.list_pop(var,data)             #把云对象var列表对象进行列表的pop操作，同本地列表操作方法一致。  

tx1.list_remove(var,data)          #把云对象var列表对象进行列表的remove操作，同本地列表操作方法一致。  

tx1.push("a","abc","test")         #向“test“信道发送消息

````

## 客户端使用示例
详细请参考使用示例/基础使用示例.py
```
from tx import *
tx1 = txl('192.168.1.65',2025,'LTtx')        #连接服务器 'LTtx'为认证的token,因服务端变化而变化。
tx1.start_tx()                               #开启put/get/push功能
tx1.start_txg("test")                        #开启接收信道"test"消息的功能，若不用可以不开启该功能，所有的数据通过tx1.Q.get()进行获取
```

## 使用场景举例
### 量化领域
#### 本人目前在开发泊松股票量化交易系统，有兴趣的朋友欢迎加下方VX私聊。
1、行情数据推送

2、交易指令发送

### 通信领域
1、自建聊天室

### 其他



## 


## 特别说明
1、 客户端在使用时注意子线程的死循环，最好是加上0.1秒的延迟或者阻塞队列，不要让CPU空转导到客户端无法接收消息

2、历史版本会以pg_server_v1.py这样保留，最新版本为pg_server.py


## 升级日志

#### 2023.7.24---------V3
1、新增文件传输功能，支持文件上传和下载，云端文件保存目录在/file_data/路径中，文件传输为单次短连接，传输完成后会有MD5校验，但没有重传机制。

2、更新内部代码逻辑，在put时可以传入基础的Python对象（只要是Json库支持的即可，例如字典，列表等，但不支持dataframe，如果要保存dataframe请先将dataframe转为字典进行保存，然后再通过
字典转dataframe完成存储）。注意，当传入一个字典对象时，通过get得到的将是一个字典对象，不再是字符串。这也意味着不用每次云变量赋值时进行json.dumps()操作。

3、新增基础的云变量字典对象操作，详请见方法说明dict_change(var,key,value)。

4、新增基础的列表操作方法list_pop()和list_remove(),原理和正常的操作一样。


#### 2023.7.13---------V2

1、升级服务端消息推送方式，防止因为单个客户端不能接受消息而造成其他客户端不能收到消息，这主要是在大通量数据推送时会发生。

#### 2023.6.1---------V1.1  
1、新增多信道订阅，在start_txg()时传入"hq_center@cb_hq_center"表示同时订阅hq_center信道和cb_hq_center信道。

2、优化代码逻辑，防止粘包。

## 待开发功能


1、开发配套同步程序，该程序会使各个PG数据中心的新增云变量保持一致，为分布式部署提供保障，防止因为单个服务端故障后影响其他程序正常运行。

## 写在最后
祝大家使用愉快，欢迎加本人VX，共同探讨量化交易的开发乐趣。

#### LTtx交流群：
![图片](https://github.com/95ge/LTtx/assets/92923254/89066202-2a5e-4c87-a349-4c1a3c6a9cd2)

#### 本人VX：
![图片](https://github.com/95ge/LTtx/assets/92923254/fb34a8b2-8d34-45b0-827c-aed80f2dd788)

#### 如果觉得有用，请作者喝杯霸王茶姬吧
![图片](https://github.com/95ge/LTtx/assets/92923254/7bdbb3ce-1c58-4546-906c-029e5097a3a6)

## 本项目star:
[![Stars](https://img.shields.io/github/stars/95ge/LTtx.svg)](https://github.com/95ge/LTtx)

## star走势
[![Star history](https://star-history.t9t.io/#95ge/LTtx)](https://star-history.t9t.io/#95ge/LTtx)







