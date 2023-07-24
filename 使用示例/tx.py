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

#客户端想要发消息和收消息同时进行,需要使用多线程达到并发效果



class txl:
    def __init__(self,ip,port,tocken):
        self.ip = ip
        self.port = port
        self.tocken = tocken
        self.start_tx_on = False
        self.txg = False
        self.Q = queue.Queue(maxsize=0)
        self.__tx = False
        self.push_count = 0
        self.timeout = 2
        self.heartbeat = 1
        print('#'*20,'通信系统V3加载成功','#'*20)
        self.tx_que = queue.Queue(maxsize=0)
        self.file_tx = None
        
    
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
                print('正在连接(%s,%s)PG服务器,请稍后'%(self.ip,self.port))
                if self.__tx == False:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                    client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192*100)
                    client.connect((self.ip,self.port))
                    self.__tx = client
                    tem_dict = {'con_type':'put_mode','tocken':self.tocken}
                    self.__tx.sendall(json.dumps(tem_dict).encode('utf-8'))
                    if self.recv_msg_start_tx():
                        t0 = threading.Thread(target=self.main_tx_que)
                        # t0.setDaemon(True)
                        t0.start()
                        thp0 = threading.Thread(target = self.start_tx_hearbeat)
                        # thp0.setDaemon(True)
                        thp0.start()
                        
                        break
                    else:
                        self.__tx.shutdown(socket.SHUT_RDWR)
                        self.__tx = False 
                else:
                    code = -1
                    msg = '请勿重复连接'
                    result = {'code':code,'msg':msg}
                    print(result)
                    return result
            except Exception as e:
                if type(e) == ConnectionRefusedError:
                    print('服务端未启动,将在1秒后继续尝试start_tx')
                    time.sleep(1)

    def start_txg(self,channel_list,pwd=''):
        while True:
            try:
                if self.txg==False:
                    self.channel_list = channel_list
                    for who in self.channel_list.split('@'):
                        if len(who) == 0:
                            continue
                        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                        client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*1024*100)
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
                    print('start_txg连接成功')
                    if self.txg != False:
                        break
                else:
                    code = -1
                    msg = '请勿重复连接txg'
                    result = {'code':code,'msg':msg}
                    print(result)
                    return result
            except Exception as e:
                if type(e) == ConnectionRefusedError:
                    print('服务端未启动,将在1秒后继续尝试')
                    time.sleep(1)
                print(e)
                    
    def start_tx_hearbeat(self):
        print('start_tx的heartbeat子线程启动')
        while 1:
            if self.__tx:
                self.push('heartbeat','test','test22')
                time.sleep(self.timeout)
            else:
                break
            
    def __start_thread(self,target,args):
        thp1 = threading.Thread(target=target,args=args)
        thp1.setDaemon(True)
        thp1.start()        
      
    def connect_judge(self,client,address):
        while True:
            try:
                data = client.recv(1024).decode('utf-8')
                dict_data = json.loads(data)
                code = dict_data['code']
                print(dict_data)
                if code =='-1':
                    break
                elif code =='0':
                    self.__tx = client
            except:
                pass
    
    def recv_msg_start_tx(self):
        
        data = self.__tx.recv(1024)
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
            raise ConnectionAbortedError('与服务器连接断开,push函数出错')
            print('chucuole')
    
    def recv_msg_put(self,client):
        data = client.recv(1024)
        dict_data = json.loads(data)
        return dict_data
    
    def send_data(self,client, msg):
        self.tx_que.put(msg)
    
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
                self.tx_que.put(old_msg)
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
            except Exception as e:
                print('broadcast_error:',e)
                if self.txg != False:
                    self.txg.close()
                    self.txg = False
                    self.start_txg(self.channel_list,pwd=self.channel_pwd)
                    break
                    time.sleep(1)
                else:
                    break
               
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

if __name__=='__main__':   
    # ip = '172.31.30.136'
    # ip = '192.168.1.65'
    ip = '192.168.1.131'
    # ip = '192.168.166.198'
    port = 2025
    tocken='LTtx'

    tx1=txl(ip,port,tocken)
    tx1.send_file('./show.py')
    tx1.recv_file('show.py','./new_data')
    tx1.start_tx()
    # # tx1.start_txg('hq_center@cb_1min_klines_data_center@cb_hq_center')
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

