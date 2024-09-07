from tx import txl
tx1 = txl('192.168.1.65',2025,'test')
tx1.start_txg('hq_center')
while 1:
    print(tx1.Q.get())


    