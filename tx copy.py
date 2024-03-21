# -*- coding: utf-8 -*-
"""
Created on Thu Sep 22 11:09:51 2022

@author: Administrator
"""


import socket
import threading
import json
import queue
import struct
import time
import os
import hashlib
import random
try:
    import zmq
except:
    print('本地没有zmq库，无法使用MQ模式，不影响其他模式使用')
import datetime

class txl:
    def __init__(self,ip,port,tocken,show=True):
        self.ip = ip
        self.port = port
        self.tocken = tocken
        self.start_tx_on = False
        self.txg = False
        self.Q = queue.Queue(maxsize=0)
        self.txg_running = False
        self.__tx = False
        self.__tx_plus = False
        self.push_count = 0
        self.timeout = 2
        self.heartbeat = 1
        self.tx_que = queue.Queue(maxsize=0)
        self.tx_que_plus = queue.Queue(maxsize=0)
        self.file_tx = None
        #ZMQ模式
        self.__ZMQ = None
        self.__ZMQ_broadcast = None
        self.__txg_heartbeat_on = True#通信系统Push模式心跳检测线程状态
        self.__txg_heartbeat_time = time.time()
        print('#'*20,'通信系统V5加载成功,Have fun!','#'*20)
    
    def send_file(self,file_name,show_on=True):
        '''
        将本地文件上传至数据中心

        Parameters
        ----------
        file_name : TYPE
            文件路径，通常为./data/file.txt.
        show_on : TYPE, optional
            是否Print进度，默认开启. The default is True.

        Returns
        -------
        code int.
        返回0表示成功，其他表示错误，参见msg
        msg string
        提示信息

        '''
        if os.path.isfile(file_name):
            if show_on:
                print('识别到文件存在')
                print(file_name)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192*100)
            client.connect((self.ip,self.port)) 
            hash_md5 = hashlib.md5()
            with open(file_name, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            file_hash = hash_md5.hexdigest()
            tem_dict = {'con_type':'file_mode',
                        'tocken':self.tocken,
                        'file_name':file_name.rsplit('/',1)[-1],
                        'file_hash':file_hash,
                        'file_mode':'upload_file',
                        }
            client.sendall(json.dumps(tem_dict).encode('utf-8'))
            server_msg = client.recv(1024).decode()
            if server_msg == 'i am ok':
                t1 = time.time()
                file = open(file_name, 'rb')
                file_data = file.read(1024)
                while file_data:
                    client.send(file_data)
                    file_data = file.read(1024)
                file.close()
                client.send(b'file send finish')
                # client.recv(1024).decode()
                client.close()
                if show_on:
                    print('file send done! usetime:%ss'%(round(time.time()-t1,6)))
            else:
                print('服务端拒绝了本次文件传输请求')
        else:
            print('文件不存在,请重新传入,当前收到的文件名:')
            print(file_name)
    
    def recv_file(self,file_name,file_path='./',show_on=False):
        '''
        从服务端下载文件

        Parameters
        ----------
        file_name : TYPE
            要下载的文件名.
        file_path : TYPE, optional
            文件保存路径，不存在的路径将会被创建. The default is './'.
        show_on : TYPE, optional
            是否Print进度，默认开启. The default is True.
        Returns
        -------
        code int.
        返回0表示成功，其他表示错误，参见msg
        msg string
        提示信息

        '''
        if file_path[-1] != '/':
            file_path = file_path + '/'
        if os.path.isdir(file_path):
            pass
        else:
            print('文件路径不存在，自动创建该路径')
            try:
                os.mkdir(file_path)
            except Exception as e:
                print(e)
                raise TypeError('文件路径自动创建失败,失败原因：%s'%(e))
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192*100)
        client.connect((self.ip,self.port)) 
        tem_dict = {'con_type':'file_mode',
                    'tocken':self.tocken,
                    'file_name':file_name,
                    'file_mode':'download_file',
                    }
        client.sendall(json.dumps(tem_dict).encode('utf-8'))
        server_msg = client.recv(1024).decode()
        if server_msg == 'file exist':
            t1 = time.time()
            file = open(file_path+file_name+'.tmp','wb')
            file_data = client.recv(1024)
            while file_data:
                file.write(file_data)
                file_data = client.recv(1024)
                if file_data == b'file send finish':
                    break
            file.close()
            hash_md5 = hashlib.md5()
            with open(file_path+file_name+'.tmp', "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            local_file_hash = hash_md5.hexdigest()
            file_hash = client.recv(1024)
            if file_hash.decode() == local_file_hash:
                code = 0
                msg = ('%s文件接收完成,文件MD5检验通过'%(file_name))
                if os.path.isfile(file_path+file_name):
                    os.remove(file_path+file_name)
                os.rename(file_path+file_name+ '.tmp', file_path+file_name)
            else:
                code = -2
                msg = '%s文件接收过程中出错,MD5校验不一致,本地文件MD5为%s,云端文件MD5为%s'%(file_name,local_file_hash,file_hash)
            
            code = 0
            msg = '%s文件接收完成,文件MD5检验通过,用时%ss'%(file_name,round(time.time()-t1,6))
            if show_on:
                print(code,msg)
            return code,msg
        else:
            code = -1
            msg = '服务端该文件不存在,请先上传'
            print(code,msg)
            return code,msg
    
    def start_tx(self):
        while True:
            try:
                print(self.get_nowtime(),'start_tx正在连接(%s,%s)LTtx服务器,请稍后'%(self.ip,self.port))
                if self.__tx == False:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                    client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192*100)
                    client.connect((self.ip,self.port))
                    self.__tx = client
                    tem_dict = {'con_type':'put_mode','tocken':self.tocken}
                    self.__tx.sendall(json.dumps(tem_dict).encode('utf-8'))
                    if self.recv_msg_start_tx(client):
                        t0 = threading.Thread(target=self.main_tx_que)
                        t0.start()
                        thp0 = threading.Thread(target = self.start_tx_hearbeat)
                        thp0.start()
                        break
                    else:
                        self.__tx.shutdown(socket.SHUT_RDWR)
                        self.__tx = False 
                else:
                    code = -1
                    msg = '请勿重复连接tx'
                    result = {'code':code,'msg':msg}
                    print(result)
                    return result
            except Exception as e:
                # if type(e) == ConnectionRefusedError:
                print(self.get_nowtime(),'服务端未启动,将在1秒后继续尝试start_tx')
                print(e)
                time.sleep(1)
    
    def start_plus(self,):
        while True:
            try:
                print(self.get_nowtime(),'start_flash正在连接(%s,%s)LTtx服务器,请稍后'%(self.ip,self.port))
                if self.__tx_plus == False:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                    client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192*100)
                    client.connect((self.ip,self.port))
                    self.__tx_plus = client
                    tem_dict = {'con_type':'plus_mode','tocken':self.tocken}
                    self.__tx_plus.sendall(json.dumps(tem_dict).encode('utf-8'))
                    if self.recv_msg_start_tx(client):
                        t0 = threading.Thread(target=self.main_tx_que_plus)
                        t0.start()
                        thp0 = threading.Thread(target = self.start_tx_hearbeat_plus)
                        thp0.start()
                        break
                    else:
                        self.__tx_plus.shutdown(socket.SHUT_RDWR)
                        self.__tx_plus = False 
                else:
                    code = -1
                    msg = '请勿重复连接'
                    result = {'code':code,'msg':msg}
                    print(result)
                    return result
                
            except Exception as e:
                if type(e) == ConnectionRefusedError:
                    print(self.get_nowtime(),'服务端未启动,将在1秒后继续尝试start_plus')
                print(self.get_nowtime(),e)
                time.sleep(1)
        # pass
    
    def start_txg(self,channel_list,pwd=''):
        while True:
            if not self.__tx:
                self.start_tx()
            try:
                if self.txg==False:
                    self.channel_list = channel_list
                    txg_count = 0
                    for who in self.channel_list.split('@'):
                        if len(who) == 0:
                            continue
                        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                        client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*1024*100)
                        self.txg_running = True
                        client.connect((self.ip,self.port,))
                        self.channel_pwd = pwd
                        tem_dict = {'con_type':'push_mode','who':who,'pwd':pwd,'tocken':self.tocken}
                        client.send(json.dumps(tem_dict).encode('utf-8'))
                        if self.recv_msg_start_txg(client) ==True:      
                            self.txg = client
                            self.__start_thread(target = self.recv_msg_broadcast, args = (client,))  
                        else:
                            self.txg.shutdown(socket.SHUT_RDWR)
                            self.txg = False
                        time.sleep(1)
                    if self.txg != False:
                        print(self.get_nowtime(),'start_txg连接成功')
                        break
                else:
                    code = -1
                    msg = '请勿重复连接txg'
                    result = {'code':code,'msg':msg}
                    print(result)
                    return result
            except Exception as e:
                if type(e) == ConnectionRefusedError:
                    print(self.get_nowtime(),'服务端未启动,将在1秒后继续尝试start_txg')
                    time.sleep(1)
                print(e)
    
    def start_MQ(self,pub_port=5555):
        '''
        开启ZMQ模式，该模式是将ZMQ与LTtx进行功能上的整合，当前版本的断线重连机制完全依赖于ZMQ自身的
        断线重连机制

        Parameters
        ----------
        pub_port : int
            传入服务端的ZMQ发布端口，通常为5555.

        Returns
        -------
        None.

        '''
        if not self.__ZMQ:
            context = zmq.Context()
            
            # 创建发布者套接字并连接到代理
            socket = context.socket(zmq.PUB)
            socket.setsockopt(zmq.RCVHWM, 1000000)
            socket.setsockopt(zmq.SNDHWM, 1000000)
            socket.connect('tcp://%s:%s'%(self.ip,pub_port))
            socket.send_string('test dsfadsafdsafsda')
            self.__ZMQ = socket
            print(self.get_nowtime(),'zmq connect ok')
        else:
            code = -1
            msg = 'start_MQ已经连接,请不要重复连接'
            print(self.get_nowtime(),msg)
    
    def start_MQ_broadcast(self,channel_list,sub_port=5556):
        '''
        开启ZMQ的订阅模式，同start_MQ

        Parameters
        ----------
        channel_list : string
            和start_txg()类似，传入要订阅的信道列表，用@进行分割.
        sub_port : int, optional
            传入服务端的ZMQ订阅端口，通常为5556

        Returns
        -------
        None.

        '''
        if not self.__ZMQ_broadcast:
            context = zmq.Context()

            # 创建订阅者套接字并连接到代理
            socket = context.socket(zmq.SUB)
            socket.setsockopt(zmq.RCVHWM, 1000000)
            socket.setsockopt(zmq.SNDHWM, 1000000)
            socket.connect("tcp://%s:%s"%(self.ip,sub_port))
            self.zmq_channel_list = channel_list.split('@')
            for channel in self.zmq_channel_list:
                if len(channel) > 0:
                    # 订阅特定主题
                    socket.setsockopt_string(zmq.SUBSCRIBE, channel)
            self.__ZMQ_broadcast = socket
            threading.Thread(target = self.main_recv_msg_from_zmq).start()
        else:
            code = -1
            msg = 'MQ_broadcast已经连接,请不要重复连接'
            print(self.get_nowtime(),msg)
    
    def main_recv_msg_from_zmq(self):
        print(self.get_nowtime(),'开始从ZMQ中接收数据')
        while True:
            data = self.__ZMQ_broadcast.recv_string().split('|',1)
            if data[0] in self.zmq_channel_list:
                self.Q.put(data[1])

    def __main_txg_heartbeat(self):
        if self.__txg_heartbeat_on:
            self.__txg_heartbeat_on = False
            while True:
                now_time = time.time()
                if now_time - self.__txg_heartbeat_time > 60:
                    print(self.get_nowtime(),'识别到txg因为网络不稳定导致断线，即将重连txg')
                    self.start_txg(self.channel_list)
                time.sleep(10)
        else:
            print(self.get_nowtime(),'当前txg的心跳检测子线程已经启动,不再重新启动子线程监控心跳')
    
    def start_tx_hearbeat(self):
        print('start_tx的heartbeat子线程启动')
        while 1:
            if self.__tx:
                self.push('heartbeat','1','heartbeat0')
                time.sleep(self.timeout)
            else:
                break

    def start_tx_hearbeat_plus(self):
        print('start_tx_plus的heartbeat子线程启动')
        while 1:
            if self.__tx_plus:
                self.push_plus('heartbeat','t','test22')
                time.sleep(2)
            else:
                break
            
    def __start_thread(self,target,args):
        thp1 = threading.Thread(target=target,args=args)
        # thp1.setDaemon(True)
        thp1.start()        
      
    
    def recv_msg_start_tx(self,client):
        
        data = client.recv(1024)
        dict_data = json.loads(data)
        code = dict_data['code']
        self.id_code = str(dict_data['id_code'])+'@'
        if code == 0:
            return True
        else:
            return False
    
    def recv_msg_start_txg(self,client):
        data = client.recv(1024)
        dict_data = json.loads(data)
        code = dict_data['code']
        if code == 0:
            return True
        else:
            return False
            
    def recv_data_from_tx(self,client):
        recv_bytes = client.recv(8,socket.MSG_WAITALL)
        bytes_len = struct.unpack("Q",recv_bytes)[0]
        recv_data = client.recv(bytes_len,socket.MSG_WAITALL).decode('utf-8',errors='replace')
        recv_data = json.loads(recv_data)
        return recv_data
    
    def get(self,key):
        if self.__tx == False:
            code = -1
            msg = '当前tx未连接,请先执行start_tx()'
            result = {'code':code,'msg':msg}
            return result
        else:
            send_data = {'func':'get','value':key}
            msg = json.dumps(send_data)
            self.send_data(self.__tx,msg)
            result = self.recv_data_from_tx(self.__tx)
            result = json.loads(result)
            if 'value' in result:
                result = result['value']
                self.heartbeat = 0
            return result
    
    def put(self,key,data):
        try:
            if self.__tx == False:
                code = -1
                msg = '当前tx未连接,请先执行start_tx()'
                result = {'code':code,'msg':msg}
                return result
            else:
                send_data = {'func':'put','value':(key,data)}
                msg = json.dumps(send_data)
                self.send_data(self.__tx,msg)
        except:
            print('Err:和服务端失去连接，即将重连')
            self.__tx = False
            self.start_tx()
    
    def list_append(self,var,data):
        '''
        对云端变量类型为列表的var进行列表append操作，相当于本地列表的基础操作，无返回值，默认成功

        Parameters
        ----------
        key : TYPE
            DESCRIPTION.
        data : TYPE
            DESCRIPTION.

        Returns
        -------
        result : TYPE
            DESCRIPTION.

        '''
        try:
            if self.__tx == False:
                code = -1
                msg = '当前tx未连接,请先执行start_tx()'
                result = {'code':code,'msg':msg}
                return result
            else:
                send_data = {'func':'list_append','value':(var,data)}
                msg = json.dumps(send_data)
                self.send_data(self.__tx,msg)
        except:
            print('Err:和服务端失去连接，即将重连')
            self.__tx = False
            self.start_tx()
    
    def list_remove(self,var,data):
        '''
        对云端变量类型为列表的var进行列表remove操作，相当于本地列表的基础操作，无返回值，默认成功

        Parameters
        ----------
        key : TYPE
            DESCRIPTION.
        data : TYPE
            DESCRIPTION.

        Returns
        -------
        result : TYPE
            DESCRIPTION.

        '''
        try:
            if self.__tx == False:
                code = -1
                msg = '当前tx未连接,请先执行start_tx()'
                result = {'code':code,'msg':msg}
                return result
            else:
                send_data = {'func':'list_remove','value':(var,data)}
                msg = json.dumps(send_data)
                self.send_data(self.__tx,msg)
        except:
            print('Err:和服务端失去连接，即将重连')
            self.__tx = False
            self.start_tx()
    
    def list_pop(self,var,data):
        '''
        对云端变量类型为列表的var进行列表pop操作，相当于本地列表的基础操作，无返回值，默认成功

        Parameters
        ----------
        key : TYPE
            DESCRIPTION.
        data : TYPE
            DESCRIPTION.

        Returns
        -------
        result : TYPE
            DESCRIPTION.

        '''
        try:
            if self.__tx == False:
                code = -1
                msg = '当前tx未连接,请先执行start_tx()'
                result = {'code':code,'msg':msg}
                return result
            else:
                send_data = {'func':'list_pop','value':(var,data)}
                msg = json.dumps(send_data)
                self.send_data(self.__tx,msg)
        except:
            print('Err:和服务端失去连接，即将重连')
            self.__tx = False
            self.start_tx()
    
    def dict_change(self,var,key,value):
        '''
        对云端变量为var的字典进行字典操作，同基础的字典操作，无返回值，默认成功

        Parameters
        ----------
        var : TYPE
            DESCRIPTION.
        key : TYPE
            DESCRIPTION.
        value : TYPE
            DESCRIPTION.

        Returns
        -------
        result : TYPE
            DESCRIPTION.

        '''
        try:
            if self.__tx == False:
                code = -1
                msg = '当前tx未连接,请先执行start_tx()'
                result = {'code':code,'msg':msg}
                return result
            else:
                send_data = {'func':'dict_change','value':(var,key,value)}
                msg = json.dumps(send_data)
                self.send_data(self.__tx,msg)
        except:
            print('Err:和服务端失去连接，即将重连')
            self.__tx = False
            self.start_tx()
    
    def push(self,key,data,who=None):
        try:
            if self.__tx == False:
                code = -1
                msg = '当前tx未连接,请先执行start_tx()'
                result = {'code':code,'msg':msg}
                return result
            else:
                send_data = {'func':'push','value':'%s|%s'%(key,data),'who':who}
                msg = json.dumps(send_data)
                self.send_data(self.__tx,msg)
                
        except Exception as e:
            print(e)
            raise ConnectionAbortedError('与服务器连接断开,push函数出错,请注意你传入的数据类型必须为字符串,请查看上方的报错内容')
            print('chucuole')
    
    def push_plus(self,key,data,who=''):
        '''
        超级push函数，会比push函数更快，效率更高，确保你传入的参数均为字符串，否则推送不成功

        Parameters
        ----------
        key : TYPE
            DESCRIPTION.
        data : TYPE
            DESCRIPTION.
        who : TYPE, optional
            DESCRIPTION. The default is None.

        Raises
        ------
        ConnectionAbortedError
            DESCRIPTION.

        Returns
        -------
        result : TYPE
            DESCRIPTION.

        '''
        try:
            if self.__tx_plus == False:
                code = -1
                msg = '当前tx_plus未连接,请先执行start_tx_plus()'
                result = {'code':code,'msg':msg}
                return result
            else:
                msg = key+'|'+data+':who:'+who
                self.send_data_plus(self.__tx_plus,msg)    
        except Exception as e:
            print(e)
            print('chucuole')
            raise ConnectionAbortedError('与服务器连接断开,push_plus函数出错,请确保你传入的参数均为字符串，请查看上方的报错内容')
         
    def MQ_push(self,var,data,who):
        '''
        采用ZMQ模式进行push，速度更快，一百万次推送耗时在1.8秒左右，但对于数据安全性没有保障，适合大通量的行情推送，在测试时发现有数据不能
        完全到达的情况，请自行做好数据校验机制

        Parameters
        ----------
        var : TYPE
            DESCRIPTION.
        data : TYPE
            DESCRIPTION.
        who : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        if self.__ZMQ:
            self.__ZMQ.send_string('%s|%s|%s'%(who,var,data))
        else:
            return (-1,'请先执行start_MQ()')
    
    def recv_msg_put(self,client):
        data = client.recv(1024)
        dict_data = json.loads(data)
        return dict_data
    
    def send_data(self,client, msg):
        self.tx_que.put(msg)
    
    def send_data_plus(self,client, msg):
        self.tx_que_plus.put(msg)
    
    def main_tx_que(self):
        while True:
            try:
                old_msg = self.tx_que.get()
                msg=old_msg.encode('utf-8')
                data_len = len(msg)
                struct_bytes = struct.pack('Q', data_len)
                self.__tx.sendall(struct_bytes)
                self.__tx.sendall(msg)
            except:
                self.__tx = False
                self.start_tx()
                if self.txg_running:
                    print('开始重连txg')
                    if self.txg:
                        self.txg.close()
                        self.txg = False
                        self.start_txg(self.channel_list)
                        self.tx_que.put(old_msg)
                print('我退出了')
                break
            
    def main_tx_que_plus(self):
        while True:
            try:
                old_msg = self.tx_que_plus.get()
                msg=old_msg.encode('utf-8')
                data_len = len(msg)
                struct_bytes = struct.pack('Q', data_len)
                self.__tx_plus.sendall(struct_bytes)
                self.__tx_plus.sendall(msg)
            except:
                self.__tx_plus = False
                self.start_plus()
                self.tx_que_plus.put(old_msg)
                break
    
    def recv_msg_broadcast(self,client):
        while True:
            try:
                if self.txg ==False:
                    mode = 2
                    msg = '识别到通信断开，结束收取broadcast信息'
                    result = {'mode':mode,'msg':msg}
                    print(result)
                    break
                else:
                    recv_data = self.recv_data_from_tx(client)
                    if '|' in recv_data:
                        self.Q.put(recv_data)
                    else:
                        self.__txg_heartbeat_time = time.time()
            except Exception as e:
                print(self.get_nowtime(),'broadcast_error:',e)
                if self.txg != False:
                    self.txg.close()
                    self.txg = False
                    self.start_txg(self.channel_list,pwd=self.channel_pwd)
                    break
                    time.sleep(1)
                else:
                    break
    
    def create_channel(self,num=30):
        '''
        创建一个随机信道，默认长度为30位字符串

        Parameters
        ----------
        num : int
            要创建的随机信道长度，默认为30位

        Returns
        -------
        None.

        '''        
        s='abcdefghijklmnopqrstuvwxz12345678901'
        str1 = ''
        for i in range(num):
            str1 = str1 + s[random.randint(0,35)]
        return str1 
    
    def close_tx(self):
        if self.__tx == False:
            code = -1
            msg = '当前tx未连接'
        else:
            self.__tx.close()
            self.__tx = False
            code = 0
            msg = 'tx关闭成功'   
        result = {'code':code,'msg':msg}
        return result
    
    def close_tx_plus(self,):
        '''
        关闭push_plus功能

        Returns
        -------
        None.

        '''
        if self.__tx_plus == False:
            code = -1
            msg = '当前tx_plus功能未开启'
            result = {'code':code,'msg':msg}
            print(result)
            return result
        else:
            self.__tx_plus.close()
            self.__tx_plus = False
            
            code = 0
            msg = 'tx_plus关闭成功'
            result = {'code':code,'msg':msg}
            print(result)
            return result
    
    def close_txg(self):
        if self.txg == False:
            code = -1
            msg = '当前txg未连接'
            result = {'code':code,'msg':msg}
            print(result)
            return result
        else:            
            self.txg.close()
            self.txg = False
            
            code = 0
            msg = 'txg关闭成功'
        result = {'code':code,'msg':msg}
        print(result)
        return result
    
    def get_nowtime(self,):
        '''
        返回当前时间，格式为2023-11-15 20:02:01

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''
        return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    
    def get_timestamp(self):
        '''
        返回当前数字时间戳

        Returns
        -------
        None.

        '''
    
    def DatestrtingToInt(self,time_str):
        '''
        把2023-10-15 20:02:01转为1697371321

        Parameters
        ----------
        time_str : string
            2023-10-15 20:02:01

        Returns
        -------
        timestamp : int
            返回整形时间戳1697371321.

        '''
        dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        timestamp = int(dt.timestamp())
        return timestamp
    def IntTimeToString(self,ct):
        '''
        把
        conv_time(1697371321) --> '2023-10-15 20:02:01'
        '''
        local_time = time.localtime(ct)
        data_head = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return data_head

    def count_datetime_day(self,str1,str2):
        '''
        计算2023-10-15 20：24：55和2023-10-14 20：24：55之间的天数

        Parameters
        ----------
        str1 : TYPE
            DESCRIPTION.
        str2 : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''
        return (datetime.datetime.strptime(str1, '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(str2, '%Y-%m-%d %H:%M:%S')).days
    
    def count_datetime_seconds(self,str1,str2):
        '''计算秒差'''
        return (datetime.datetime.strptime(str1, '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(str2, '%Y-%m-%d %H:%M:%S')).seconds
    
    def count_datetime_minutes(self,str1,str2):
        '''计算分钟差'''
        return (datetime.datetime.strptime(str1, '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(str2, '%Y-%m-%d %H:%M:%S')).seconds // 60
    
    def get_day_before(self,datestr,N):
        '''向前取N天,传入2023-10-15的格式'''
        date = datetime.datetime.strptime(datestr, '%Y-%m-%d')
        date_before = date - datetime.timedelta(days=N)
        return str(date_before.date())

    def get_local_ip():
        '''返回本地IP地址'''

        try:
        # 创建一个socket对象
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 不需要真的连接，所以使用一个不存在的地址
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
        except Exception:
            IP = "127.0.0.1"  # 如果出现异常，则返回回环地址
        finally:
            s.close()  # 关闭socket
        return IP

    def get_remote_ip():
        '''
        查询本机的公网IP
        '''
        import requests
        response = requests.get('https://api.ipify.org')
        if response.status_code == 200:
            return response.text
        else:
            return 'Error: Unable to fetch IP'



if __name__=='__main__':   
    ip = '192.168.2.2'
    # ip = 'localhost'
    # ip = '192.168.154.198'
    port = 2025
    tocken='LTtx'

    tx1=txl(ip,port,tocken)
    # tx1.send_file('./show.py')
    # tx1.recv_file('show.py','./new_data')
    tx1.start_tx()
    tx1.start_txg('litao')
    # tx1.start_MQ()
    # tx1.start_MQ_broadcast('test222')
    # tx1.MQ_push('test2222','weqrreqw','test222')
    # t1 = time.time()
    # for i in range(1000000):
    #     # socket.send_string(f"test Message {i}")
    #     # socket.send_string('%s'
    #     tx1.MQ_push('test','fdsafdas%s'%(i),'test222')
    # print(time.time()-t1)
    # tx1.ZMQ.send_string('test p5555dsafdsafdas')
    # tx1.start_plus()
    
    def show():
        while True:
            data = tx1.Q.get().split('|')
            t1 = time.time()
            print(data)
            # print(t1-float(data[1]))
    threading.Thread(target = show).start()
    # # tx1.push('test',str(time.time()),'litao')
    # # time.sleep(1)
    # # tx1.push_plus('key', str(time.time()),'litao')
    # def run_for_test():
    #     print('开始测试\n\r')
    #     print('测试push效率')
    #     t1 = time.time()
    #     for i in range(1000000):
    #         tx1.push('key', str(i),'litao2')
    #     print('push方法调用100万次耗时：')
    #     print(time.time()-t1)
    #     t1 = time.time()
    #     time.sleep(2)
    #     while 1:
    #         if tx1.tx_que.qsize() <= 0:
    #             break
    #         else:
    #             time.sleep(1)
    #     print('100万条数据用push推送到服务端耗时：')
    #     print(time.time() - t1)
    #     print('#'*10)
    #     print('测试push_plus效率')
    #     t1 = time.time()
    #     for i in range(1000000):
    #         tx1.push_plus('key', str(i),'litao2')
    #     print('push_plus方法调用100万次耗时：')
    #     print(time.time()-t1)
    #     t1 = time.time()
    #     time.sleep(2)
    #     while 1:
    #         if tx1.tx_que_plus.qsize() <= 0:
    #             break
    #         else:
    #             time.sleep(1)
    #     print('100万条数据用push_plus推送到服务端耗时：')
    #     print(time.time() - t1)
    # for i in range(4):
    #     print('第%s次测试:'%(i))
    #     run_for_test()
    #     print('\n\r')
        
    
    
    
    # tx1.start_txg('hq_center@cb_1min_klines_data_center@cb_hq_center')
    # tx1.start_txg('hq_center@cb_1min_klines_data_center')
    
    # def show():
    #     while 1:
    #         print(tx1.Q.get())
    # thp0 = threading.Thread(target=show)
    # thp0.setDaemon(True)
    # thp0.start()
    # c = {'abc':'fdsafdsa'*90000}
    # tx1.push('test',json.dumps(c),'test')
    # show()
    # import time
    # t1 = time.time()
    # # time.sleep(1)
    # for i in range(10000):
    #     tx1.push('test',str(i)*999,'test2')
    #     # print(i)
    # print(time.time()-t1)

