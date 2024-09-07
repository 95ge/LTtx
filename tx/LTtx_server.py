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
import hashlib
import psutil


id_code = 0
all_que = queue.Queue(maxsize=0)

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
            time.sleep(1)
    server.shutdown(socket.SHUT_RDWR)
    close_con(server)
    
def start_thread(target,args):
    thp1 = threading.Thread(target=target,args=args)
    thp1.start()

def sys_show_on(data):
    connect_show_list.append(data)

def close_con(client):
    try:
        # 强制停止读写操作，确保 recv 不再阻塞
        client.shutdown(socket.SHUT_RDWR)
    except socket.error as e:
        pass
    finally:
        # 释放套接字资源
        client.close()

def handle_connect(client,address):
     global id_code
     while True:
        # 接收客户端发过来的数据 循环为这个客户端服务多次
        recv_data = client.recv(1024)
        sys_show_on("%s:收到客户端请求连接的消息：%s" %(get_str_time(),recv_data.decode("utf-8")))
        print("%s:收到客户端%s请求连接的消息：%s" %(get_str_time(),address,recv_data.decode("utf-8")))
        dict_data = json.loads(recv_data)
        con_type = dict_data['con_type']
        con_tocken = dict_data['tocken']
        if con_tocken != tocken:
            code = '-1'
            msg = '传入的tocken:%s不匹配,当前服务器版本%s'%(con_tocken,version)
            result = {'code':code,'msg':'服务器发来消息：%s'%(msg)}
            send_msg(client,result)
        elif con_type == 'put_mode':
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
        elif con_type == 'file_mode':
            handle_connect_file(client,address,dict_data)
            close_con(client)
            break
        elif con_type == 'plus_mode':
            id_code = id_code + 1
            result = {'code':0,'msg':'plus mode连接成功','id_code':id_code}
            start_thread(target = main_handle_push_plus,args=(client,))
            send_msg(client,result)
        elif con_type == 'check_version':
            from tx import txl
            tx1 = txl('a',2025,'test')
            version = tx1.version
            result = {'LTtx_lastest':version}
            send_msg(client,result)
        # 如果客户端发送的数据不为空那么就是需要服务
        else:
            result = '当前连接未通过'
            send_msg(client,result)
            close_con(client)
        break



def handle_connect_file(client,address,dict_data):
    file_mode = dict_data['file_mode']
    if file_mode == 'upload_file':
        file_name = dict_data['file_name']
        file_hash = dict_data['file_hash']
        print(dict_data)
        print('当前文件已经存在')
        file = open('./file_data/%s'%(file_name+'.tmp'),'wb')
        client.sendall(b'i am ok')
        file_data = client.recv(1024)
        while file_data:
            file.write(file_data)
            file_data = client.recv(1024)
        print('文件接收完成')
        file.close()
        sys_show_on('%s文件接收完成'%(file_name))
        if os.path.isfile('./file_data/%s'%(file_name)):
            os.remove('./file_data/%s'%(file_name))
        os.rename('./file_data/%s'%(file_name + '.tmp'), './file_data/%s'%(file_name))
       
    elif file_mode == 'download_file':
        file_name = dict_data['file_name']
        hash_md5 = hashlib.md5()
        if os.path.isfile('./file_data/%s'%(file_name)):
            client.sendall('file exist'.encode())
            file = open(file_name, 'rb')
            file_data = file.read(1024)
            while file_data:
                client.sendall(file_data)
                file_data = file.read(1024)
            file.close()
            time.sleep(1)
            close_con(client)
        else:
            client.sendall('file does not exist'.encode())
    else:
        pass
    


def handle_put(var,data):
    que_put.put((var,data))
    return {'code':0,'msg':'put work down'}

que_put = queue.Queue()
def main_handle_put():
    file_path = os.path.join(os.path.dirname(__file__), 'data0.txt')
    while True:
        var,data = que_put.get()
        try:
            data = json.loads(data)
        except:
            pass
        dict_var[var] = data
        if que_put.qsize() > 50:
            while True:
                if  que_put.qsize() > 2:
                    try:
                        data = json.loads(data)
                    except:
                        pass
                    dict_var[var] = data
                else:
                    break
        with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dict_var, f, ensure_ascii=False, indent=4)


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

def recv_data_from_tx_fast(client):
    recv_bytes = client.recv(8,socket.MSG_WAITALL)
    bytes_len = struct.unpack("Q",recv_bytes)[0]
    recv_data = client.recv(bytes_len,socket.MSG_WAITALL)
    recv_data = recv_data.decode('utf-8',errors='replace')
    return recv_data

def send_data_to_client_fast(client,msg):
    msg = msg.encode('utf-8')
    data_len = len(msg)
    struct_bytes = struct.pack('Q', data_len)
    client.sendall(struct_bytes)
    client.sendall(msg)
        
def send_data_to_client(client,msg):
    msg=json.dumps(msg).encode('utf-8')
    data_len = len(msg)
    struct_bytes = struct.pack('Q', data_len)
    client.sendall(struct_bytes)
    client.sendall(msg)

def main_handle_push_plus(client):
    while True:
        recv_data = recv_data_from_tx_fast(client).rsplit(':who:',1)
        who = recv_data[1]
        if who in dict_client_push_group:
            if len(dict_client_push_group[who]['group']) == 0:
                pass
            else:
                dict_client_push_group[who]['que'].put((client,recv_data[0]))
    

def main_handle_msg_tx(client,address,C_que):
    sys_show_on(get_str_time()+':'+'客户端'+str(address)+'加入tx')
    while True:
        try:
            recv_data = recv_data_from_tx(client)
            C_que.put(recv_data)
        except Exception as e:
            close_con(client)
            print(e)
            break

def main_handle_client_que(client,C_que,C_que_push):
    while True:
        try:
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
            elif func == 'list_append':
                data = recv_data['value'][1]
                var = recv_data['value'][0]
                result = handle_list_append(var,data)
            elif func == 'dict_change':
                value = recv_data['value'][2]
                data = recv_data['value'][1]
                var = recv_data['value'][0]
                result = handle_dict_change(var,data,value) 
            elif func == 'list_pop':
                data = recv_data['value'][1]
                var = recv_data['value'][0]
                result = handle_list_pop(var,data)
            elif func == 'list_remove':
                data = recv_data['value'][1]
                var = recv_data['value'][0]
                result = handle_list_remove(var,data)
            elif func == 'put_dataframe':
                data = recv_data['value'][1]
                var = recv_data['value'][0]
                result = handle_put_dataframe(var,data)
            elif func == 'get_dataframe':
                var = recv_data['value']
                result = handle_get_dataframe(var)
                C_que_push.put(result)
            elif func == 'get_dict_value':
                result = handle_get_dict_value(recv_data['value'][0],recv_data['value'][1])
                C_que_push.put(result)
            elif func == 'get_list_value':
                result = handle_get_list_value(recv_data['value'][0],recv_data['value'][1])
                C_que_push.put(result)
        except:
            pass


def handle_get_dict_value(var,key):
    if var in dict_var:
        if key in dict_var[var]:
            return {'value':dict_var[var][key]}
        else:
            return {'value':None}
    else:
        return {'value':None}

def handle_get_list_value(var,index):
    if var in dict_var:
        if abs(index) > len(dict_var[var]):
            return {'value':dict_var[var][index]}
        else:
            return {'value':None}
    else:
        return {'value':None}        

def handle_get_dataframe(var):
    '''
    处理get dataframe
    '''
    import pandas as pd
    if var in dict_df:
        try:
            df = pd.read_csv('./dataframe_data/%s.csv'%(var))
        except:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()
    
    return {'value':json.dumps(df.to_dict(orient='records'))}

dict_df = {}
def handle_put_dataframe(var,data):
    import pandas as pd
    try:
        df = pd.DataFrame(json.loads(data))
        df.to_csv('./dataframe_data/%s.csv'%(var),index=False)
        dict_df[var] = 1
        tem_dict = {'code':0,'msg':'success','value':{}}
    except Exception as e:
        tem_dict = {'code':-1,'msg':str(e)}
        print(tem_dict)
    return tem_dict


def handle_list_remove(var,data):
    global dict_var_on
    try:
        dict_var[var].remove(data)
        if dict_var_on == False:
            dict_var_on = True
    except:
        pass

def handle_list_pop(var,data):
    global dict_var_on
    try:
        data = int(data)
        dict_var[var].pop(data)
        if dict_var_on == False:
            dict_var_on = True
    except:
        pass

def handle_list_append(var,data):
    global dict_var_on
    try:
        dict_var[var].append(data)
        if dict_var_on == False:
            dict_var_on = True
    except:
        pass

def handle_dict_change(var,key,value):
    global dict_var_on
    # try:
    print(dict_var)
    # tem_dict = json.loads(dict_var[var])
    # tem_dict[key] = value
    dict_var[var][key] = value
    if dict_var_on == False:
        dict_var_on = True
    # except:
    #     pass

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

def main_push_client(tem_que,client):
    while True:
        msg = tem_que.get()
        try:
            send_data_to_client(client, msg)
        except Exception as e:
            sys_show_on('有broadcast客户端退出')
            close_con(client)
            del dict_client_que[client]
            break
            

def handle_connect_push(con,address,who_list,pwd='520'):
    id_code = len(dict_client_push)+1
    dict_client_push[id_code] = {'con':con,'address':address}
    for who in who_list:
        if who in dict_client_push_group:
            if pwd == dict_client_push_group[who]['pwd']:
                dict_client_push_group[who]['group'].append(con)
                msg = '服务端发来信息：欢迎加入%s信道,当前总信道连接数为:%s'%(who,len(dict_client_push_group[who]['group']))
                tem_que = queue.Queue()
                dict_client_que[con] = tem_que
                threading.Thread(target = main_push_client,args=(tem_que,con)).start()
                code = 0
            else:
                msg = '服务端发来信息：当前信道%s已经存在，传入的密码:%s不正确，请重新传入密码'%(who,pwd)
                del dict_client_push[id_code]
                code = -1
        else:
            tem_que = queue.Queue()
            dict_client_que[con] = tem_que
            threading.Thread(target = main_push_client,args=(tem_que,con)).start()
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
        # try:
            client,recv_data = que.get()
            group_list = dict_client_push_group[who]['group']
            if len(group_list) ==0:
                sys_show_on('%s信道退出'%(who))
                del dict_client_push_group[who]
                break
            else:
                for i in group_list:
                    if i in dict_client_que:    
                        dict_client_que[i].put(recv_data)
                    else:
                        group_list.remove(i)
     


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
        # 假设 data0.txt 和 LTtx_server.py 在同一目录
        config_path = os.path.join(os.path.dirname(__file__), 'data0.txt')
        
        # 尝试打开并读取 JSON 文件
        with open(config_path, 'r', encoding='utf-8') as f:
            dict_var = json.load(f)
           # print('Load dict_var success!')
    except FileNotFoundError:
        #print(f"Load Error: File not found at {config_path}")
        dict_var = {}
    except json.JSONDecodeError:
       # print("Load Error: File is not valid JSON")
        dict_var = {}
    except Exception as e:
      #  print('Load Error:', e)
        dict_var = {}
    
    return dict_var

def main_show():
    while True:
        table_data = []
        for who,value in dict_client_push_group.items():
            print(who,value['que'].qsize())
            tem_list = [who[:10],len(value['group']),value['que'].qsize(),'']
            table_data.append(tem_list)
        print('\033c', end='')

        print('#'*20,'服务器信息V5','#'*20)
        print('ip:%s'%(ip),' '*10,'port:%s'%(port),' '*10,'tocken:%s'%(tocken))
        
        print('#'*20,'当前LTtx状态','#'*20)
        print('当前TX连接数：%s                 当前TXG信道数'%(len(dict_client)),len(dict_client_push_group))
        
        print(tabulate.tabulate(table_data, headers=['信道名称', '当前连接数', '信道队列数据量','备注'], tablefmt='fancy_grid',stralign='wrap'))

        print('%sLTtx系统最新日志信息：'%(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())))
        print('#'*30)
        for i in connect_show_list:
            print(i)
            if len (connect_show_list) > 10:
                connect_show_list.remove(i)
        print('#'*30)
        
        
        time.sleep(1)

def make_dir():
    flod_list = ['file_data','dataframe_data']
    for i in flod_list:
        try:
            os.mkdir(i)
        except:
            pass

def main_save_dict_var():
    global dict_var_on, dict_var
    # 获取当前脚本所在目录，并构建文件路径
    file_path = os.path.join(os.path.dirname(__file__), 'data0.txt')

    while True:
        if dict_var_on:
            dict_var_on = False  # 重置标志
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dict_var, f, ensure_ascii=False, indent=4)
            print(f"dict_var saved to {file_path}")
        time.sleep(60)  # 每 60 秒检查一次

            
def main_zmq_mode(zmq_xsub_port,zmq_xpub_port):
    import zmq
    context = zmq.Context()
    # 创建并绑定发布者套接字
    frontend = context.socket(zmq.XSUB)
    frontend.setsockopt(zmq.SNDHWM, 10000000)
    frontend.setsockopt(zmq.RCVHWM, 10000000)
    frontend.bind("tcp://*:%s"%(zmq_xsub_port))

    # 创建并绑定订阅者套接字
    backend = context.socket(zmq.XPUB)
    backend.setsockopt(zmq.SNDHWM, 10000000)
    backend.setsockopt(zmq.RCVHWM, 10000000)
    backend.bind("tcp://*:%s"%(zmq_xpub_port))
    print("tcp://*:%s"%(zmq_xpub_port))
    print('zmq启动成功')
    # 启动代理
    zmq.proxy(frontend, backend)

def load_config():
    tem_dict = {}
    config_path = os.path.join(os.path.dirname(__file__), 'Config.txt')
    with open(config_path, 'r', encoding='utf-8') as f:
        data = f.read().split('\n')
        for i in data:
            if len(i) > 0 and ' ' in i and ':' in i:
                key = i.split(' ')[0].split(':')[0]
                value = i.split(' ')[0].split(':')[1]
                tem_dict[key] = value
    return tem_dict

def main():
    global tocken,ip,port,version
    version = 'V7.1.5'
    import multiprocessing
    config = load_config()
    port = int(config['port'])
    tocken = config['token']
    ip = get_local_ip()
    #ZMQ的订阅端口
    zmq_xsub_port = config['zmq_port1']
    #ZMQ的发布端口
    zmq_xpub_port = config['zmq_port2']
    zmq_mode = config['zmq_mode']
    set_cpu = config['set_cpu']
    if zmq_mode == "True":
        p0 = multiprocessing.Process(target=main_zmq_mode,args=(zmq_xsub_port,zmq_xpub_port))
        p0.daemon = True
        p0.start()
        
    if set_cpu:        
        # 创建一个Process对象，代表当前进程
        p = psutil.Process(os.getpid())
        
        # 获取当前进程的CPU亲和性
        print(p.cpu_affinity())
        
        # 将当前进程的CPU亲和性设置为只运行最后一颗CPU上
        p.cpu_affinity([p.cpu_affinity()[-1]])
        
        # 验证设置是否生效
        print(p.cpu_affinity())
    
    

    recv_buffer_size = 1024*1024*100
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, recv_buffer_size,)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.settimeout(5)
    server.bind((ip,port))
    server.listen(5)
    print('\n\r')
    print('#'*20,'服务器信息%s'%(version),'#'*20)
    print('ip:%s'%(ip),' '*10,'port:%s'%(port),' '*10,'tocken:%s'%(tocken))
#    threading.Thread(target=main_show).start()
    threading.Thread(target = main_heartbeat).start()
    threading.Thread(target = main_save_dict_var).start()
    threading.Thread(target = main_handle_put).start()
    wait_accept(server)

#配置
connect_show_list = []
dict_var_on = False
make_dir()
dict_client_que = {}
dict_client_push = {}
dict_client_push_group = {}
dict_client = {}
dict_client_status = {}
dict_var = load_dict_var()#保存云变量

if __name__ == '__main__':
    main()















