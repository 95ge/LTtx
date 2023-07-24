# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 21:16:19 2022

@author: Administrator
"""
import threading
import socket 
import os
import time
import json
import struct
import signal
import queue
import tabulate


def get_local_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip
def my_handler(signum, frame):
    print('程序退出')
    os._exit(0)

signal.signal(signal.SIGINT, my_handler)


def send_msg(client,result):
    result = json.dumps(result).encode('utf-8')    
    client.sendall(result)


def wait_accept(server):
    while True:
        try:
            client, address = server.accept()
            start_thread(target = handle_connect,args=(client,address))
        except Exception as e: 
            pass
    server.close()
    
def start_thread(target,args):
    thp1 = threading.Thread(target=target,args=args)
    thp1.start()

def sys_show_on(data):
    connect_show_list.append(data)

def handle_connect(client,address):
     while True:
        # 接收客户端发过来的数据 循环为这个客户端服务多次
        recv_data = client.recv(1024)
        sys_show_on("%s:收到客户端请求连接的消息：%s" %(get_str_time(),recv_data.decode("utf-8")))
        dict_data = json.loads(recv_data)
        con_type = dict_data['con_type']
        con_tocken = dict_data['tocken']
        if con_tocken != tocken:
            code = '-1'
            msg = '传入的tocken:%s不匹配'%(con_tocken)
            result = {'code':code,'msg':'服务器发来消息：%s'%(msg)}
            send_msg(client,result)
        elif con_type == 'put_mode':
            # print('请求连接tx')
            result = handle_connect_put(client,address)
            C_que = queue.Queue(maxsize=0)
            C_que_push = queue.Queue(maxsize=0)
            start_thread(target = main_handle_client_que,args=(client, C_que, C_que_push))
            start_thread(target = main_push_data_que,args=(client, C_que_push))
            send_msg(client,result)
            start_thread(target = main_handle_msg_tx,args=(client,address,C_que)) 
        elif con_type == 'push_mode':
            who = dict_data['who']
            if '@' not in who:
                who = [who]
            else:
                who = who.split('@')
            pwd = dict_data['pwd']
            result = handle_connect_push(client,address,who,pwd)
            send_msg(client,result)
        # 如果客户端发送的数据不为空那么就是需要服务
        else:
            result = '当前连接未通过'
            send_msg(client,result)
            # print(result)
            client.close()
        break

def handle_put(var,data):
    dict_var[var] = data
    # print('云变量%s赋值成功,前5位内容为%s'%(var,data[:5]))
    with open('./data0.txt','w',encoding='utf-8') as f:
        json.dump(dict_var, f)
        f.close()
    
    return {'code':0,'msg':'put work down'}
        
def handle_get(var):
    if var in dict_var:
        return {'value':dict_var[var]}
    else:
        return {'value':None}
def get_str_time():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())


def recv_data_from_tx(client):
    recv_bytes = client.recv(8,socket.MSG_WAITALL)
    bytes_len = struct.unpack("Q",recv_bytes)[0]
    recv_data = client.recv(bytes_len,socket.MSG_WAITALL)
    recv_data = json.loads(recv_data.decode('utf-8',errors='replace'))
    return recv_data
        
def send_data_to_client(client,msg):
    msg=json.dumps(msg).encode('utf-8')
    data_len = len(msg)
    struct_bytes = struct.pack('Q', data_len)
    client.sendall(struct_bytes)
    client.sendall(msg)



def main_handle_msg_tx(client,address,C_que):
    sys_show_on(get_str_time()+':'+'客户端'+str(address)+'加入tx')
    while True:
        try:
            recv_data = recv_data_from_tx(client)
            C_que.put(recv_data)
        except Exception as e:
            client.close()
            print(e)
            break

def main_handle_client_que(client,C_que,C_que_push):
    while True:
        # try:
        recv_data = C_que.get()
        func = recv_data['func']
        if func == 'push':
            who = recv_data['who']
            if who in dict_client_push_group:
                if len(dict_client_push_group[who]['group']) == 0:
                    pass
                else:
                    recv_data = recv_data['value']
                    dict_client_push_group[who]['que'].put((client,recv_data))
            else:
                pass
        elif func == 'get':
            var = recv_data['value']
            result = handle_get(var)
            C_que_push.put(result)
        elif func == 'put':
            data = recv_data['value'][1]
            var = recv_data['value'][0]
            result = handle_put(var,data)
        # elif func == 'put_add':
        #     data = recv_data['value'][1]
        #     var = recv_data['value'][0]
        #     result = handle_put_add(var,data)

# def handle_put_add(var,data):
#     if var in dict_var:
#         dict_var[var] = dict_var[var]

def main_push_data_que(client,C_que_push):
    while True:
        result = C_que_push.get()
        # print(result,'----')
        send_data_to_client(client,msg=json.dumps(result))
                
        
def handle_connect_put(con,address):
    global id_code
    id_code = id_code + 1
    dict_client[id_code] = {'con':con,'address':address}
    msg = '服务端发来信息：新连接加入成功'
    code = 0 
    result = {'code':code,'msg':msg,'id_code':id_code}
    return result

def main_heartbeat():
    '''
    客户端心跳维护子线程

    Returns
    -------
    None.

    '''
    recv_data = {1:1}
    while True:
        for who,value in dict_client_push_group.items():
            value['que'].put((1,recv_data))
        time.sleep(5)

def handle_connect_push(con,address,who_list,pwd='520'):
    id_code = len(dict_client_push)+1
    dict_client_push[id_code] = {'con':con,'address':address}
    for who in who_list:
        if who in dict_client_push_group:
            if pwd == dict_client_push_group[who]['pwd']:
                # print('密码判断通过')
                dict_client_push_group[who]['group'].append(con)
                msg = '服务端发来信息：欢迎加入%s信道,当前总信道连接数为:%s'%(who,len(dict_client_push_group[who]['group']))
                # print(msg)
                code = 0
            else:
                msg = '服务端发来信息：当前信道%s已经存在，传入的密码:%s不正确，请重新传入密码'%(who,pwd)
                del dict_client_push[id_code]
                # print(msg)
                code = -1
        else:
            tem_que = queue.Queue(maxsize=0)
            dict_client_push_group[who] = {'group':[con],'pwd':pwd,'que':tem_que}
            thp0 = threading.Thread(target = main_push_queue,args=(tem_que,who))
            thp0.start()
            msg = '服务端发来信息：新信道%s创建成功'%(who)
            code = 0
        result = {'code':code,'msg':msg}
    return result

def main_push_queue(que,who):
    sys_show_on('新信道%s子线程启动'%(who))
    while True:
        try:
            client,recv_data = que.get()
            group_list = dict_client_push_group[who]['group']
            if len(group_list) ==0:
                sys_show_on('%s信道退出'%(who))
                del dict_client_push_group[who]
                break
            else:
                for i in group_list:
                    try:
                        if client != i:
                            send_data_to_client(i,msg=recv_data)
                    except Exception as e:
                        dict_client_push_group[who]['group'].remove(i)
                        # print('断开连接',e)
        except Exception as e:
            sys_show_on('信道推送消息出错了',e)
            


def build_header_push(data_len):
    header = {'data_len': data_len}
    return json.dumps(header).encode('utf-8')
    

def main_test():
    while True:
        print('\n\r')
        a=input('输入要执行的python代码:\n\n')
        print('执行结果如下:\n\n')
        if a=='clear':
            os.system('clear')
        else:
            try:
                exec(a)
                print('\n')
            except Exception as e:
                print(e)

def load_dict_var():
    try:
        with open('./data0.txt','r',encoding='utf-8') as f:
            dict_var = json.load(f)
            print('load dict_var success !')
            f.close()
    except Exception as e:
        print('load Error',e)
        dict_var = {}
    return dict_var

def main_show():
    # time.sleep(2)
    while True:
        # for who,value in dict_client_push_group.items():
        #     print(who,value['que'].qsize())
        # time.sleep(5)
        table_data = []
        for who,value in dict_client_push_group.items():
            print(who,value['que'].qsize())
            tem_list = [who[:10],len(value['group']),value['que'].qsize(),'']
            table_data.append(tem_list)
            
        print('\033c', end='')

        print('#'*20,'服务器信息V5','#'*20)
        print('ip:%s'%(ip),' '*10,'port:%s'%(port),' '*10,'tocken:%s'%(tocken))
        
        print('#'*20,'当前PG状态','#'*20)
        print('当前TX连接数：%s                 当前TXG信道数'%(len(dict_client)),len(dict_client_push_group))
        
        print(tabulate.tabulate(table_data, headers=['信道名称', '当前连接数', '信道队列数据量','备注'], tablefmt='fancy_grid',stralign='wrap'))

        print('PG系统最新日志信息：')
        for i in connect_show_list:
            print(i)
            if len (connect_show_list) > 10:
                connect_show_list.remove(i)
        
        
        time.sleep(1)

if __name__ == '__main__':
    port = 2025
    tocken = 'LTtx'
    ip = get_local_ip()
    
    id_code = 0
    all_que = queue.Queue(maxsize=0)
    #配置
    connect_show_list = []
    
    dict_client_push = {}
    dict_client_push_group = {}
    dict_client = {}
    dict_client_status = {}
    dict_var = load_dict_var()#保存云变量
    recv_buffer_size = 1024*1024*100
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, recv_buffer_size)
    # server.settimeout(5)
    server.bind((ip,port))
    server.listen(5)
    print('\n\r')
    print('#'*20,'服务器信息V5','#'*20)
    print('ip:%s'%(ip),' '*10,'port:%s'%(port),' '*10,'tocken:%s'%(tocken))
    # threading.Thread(target=main_test).start()
    threading.Thread(target=main_show).start()
    threading.Thread(target = main_heartbeat).start()
    wait_accept(server)
















