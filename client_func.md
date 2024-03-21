# 客户端函数说明

````
#需要提前执行start_tx()函数
put("a","b")                   #把云变量“a"赋值为“b",二者均为字符串，新版本中V3中将不再对b进行字符串数据类型进行限制。  

get("a")                       #获取云变量“a"的值。当put时传入的是一个Python对象，那么获得的值也是一个Python对象。  

dict_change(var,key,value)     #把云对象var字典对象进行key和value的更新，同本地字典操作方法一致。     

list_pop(var,data)             #把云对象var列表对象进行列表的pop操作，同本地列表操作方法一致。  

list_remove(var,data)          #把云对象var列表对象进行列表的remove操作，同本地列表操作方法一致。  

push("a","abc","test")         #向“test“信道发送消息

push_plus("a","abc","test")    #是push的升级版本，可以快速完成数据推送，使用前需要先start_plus()，该方法需要大于V4版本才能使用

MQ_push('a'.'abc','test')      #是push模式的ZMQ版本，相比较于push_plus更快，适合大通量的场景，但由于当前版本中未对ZMQ的连接进行加密验证，因此存在安全漏洞，如果数据不是非常重要但又对速度和延迟有着极高的要求，可以采用这种模式

create_channel(num=30)         #返回一个30位长度的随机字符串，通常用来创建一些私有信道（程序身份识别）

get_remote_ip()                #查询公网IP

get_local_ip()                 #查询本地IP

get_nowtime()                  #返回当前时间,如'2024-03-21 16:02:00'

IntTimeToString(ct)            #把conv_time(1697371321) --> '2023-10-15 20:02:01'

DatestrtingToInt(ct)           #把2023-10-15 20:02:01转为1697371321

get_day_before(datestr,N)      #返回第N天前的日期，例如datestr为2024-03-21，N为3，则返回2024-03-18

count_datetime_minutes(str1,str2)    #计算两个时间的分钟差，传入格式:'2024-03-18 18:00:06'

count_datetime_seconds(str1,str2)    #计算两个时间的秒差，传入格式:'2024-03-18 18:00:06'

count_datetime_day(str1,str2)        #计算两个时间的天数差，传入格式:'2024-03-18 18:00:06'



````






