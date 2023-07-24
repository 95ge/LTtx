# -*- coding: utf-8 -*-
"""
Created on Sun May 21 00:42:53 2023

@author: Administrator
"""
from tx import *
tx1 = txl('192.168.1.8',2025,'test')
tx1.start_txg('test')
while 1:
    a = tx1.Q.get()
    print(a,type(a))



