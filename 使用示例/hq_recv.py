# -*- coding: utf-8 -*-
"""
Created on Wed Jun 21 09:48:13 2023

@author: Administrator
"""
import time
from tx import *
tx1 = txl('192.168.3.24',2025,'test')
# tx1.start_tx()
tx1.start_txg('hq_center')
while 1:
    # print(tx1.Q.qsize())
    print(tx1.Q.get())
    # time.sleep(0.05)

