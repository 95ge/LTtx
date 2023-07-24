# -*- coding: utf-8 -*-
"""
Created on Sun May 21 00:43:46 2023

@author: Administrator
"""
import time
from tx import *
num = 10000
# tx1 = txl('192.168.166.198',2025,'LTtx')
tx1 = txl('192.168.1.8',2025,'LTtx')
tx1.start_tx()

# count = 0
# while 1:
#     tx1.push('test',str(count),'test')
#     count =count + 1


t1 = time.time()
for i in range(num):
    tx1.push('test',str(i),'test')

print(time.time()-t1)

# while True:
#     tx1.push('test',str(i),'test')
