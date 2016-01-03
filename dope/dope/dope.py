__author__ = 'Wdaviau'
from tiers.Tiers import dSensor, dGateway
from  datastruct.binarytree import BSTree, enc_insert
from time import time


# For use comparing tree to verify rebalancing
# As long as we go level by level we should be ok
# The order should be preserved in the cache list
# So not too much work
def convert_cache_to_tree(cache):
    # sort cache by encoding length
    cache = sorted(cache, key = lambda x: len(x.encoding))
    bstree = BSTree(cache[0].cipher_text)
    for elt in cache[1:]:
        enc_insert(bstree, elt.cipher_text, elt.encoding)

    return bstree

# Strip enc_root from enc.  If they don't match at the start return None
def strip(enc_root, enc):
    if enc[:len(enc_root)] != enc_root:
        return None
    else: 
        return enc[len(enc_root):]

# For non-connected cache convert into a forest
def convert_cache_to_forest(cache, out_file):
    cache = sorted(cache, key=lambda x:len(x.encoding))
    trees = []
    encs = []
    if cache == []:
        if out_file is None:
            print([])
        else:
            with open(out_file, "a") as logfile:
                print([], file=logfile)
        return
    trees.append(BSTree(cache[0].cipher_text))
    encs.append([])
    for elt in cache[1:]:
        in_tree = 0
        success = False
        # Insert on the first tree that will accept it
        while in_tree < len(trees) and not success:
            enc = strip(encs[in_tree], elt.encoding)
            if enc is None:
                in_tree += 1
                continue
            try:
                enc_insert(trees[in_tree], elt.cipher_text, enc)
                success = True
            except ValueError as e:
                # current encoding tree
                in_tree += 1
 
        # Insert doesn't work on anyone else? Add a new tree to trees
        if not success:
            trees.append(BSTree(elt.cipher_text))
            encs.append(elt.encoding)
    if out_file is None:
        for idx in range(len(trees)):
            print("\n")
            print(str(trees[idx]))
            print("Root Encoding: " + str(encs[idx]))
            print("\n")
    else:
        with open(out_file, "a") as logfile:
            for idx in range(len(trees)):
                print("\n", file=logfile)
                print(str(trees[idx]), file=logfile)
                print("Root Encoding: " + str(encs[idx]), file=logfile)
                print("\n", file=logfile)



def dOPE(maxTics, dataTics, networkTics, data_queue_len, cache_len,
         distribution = 'random'):
    ts = str(time())
    sensor = dSensor(data_queue_len, distribution, cache_len, 
                     "dSensorCache" + ts +".log")
    gateway = dGateway("dGatewayCache" + ts + ".log")
    sensor.link(gateway)
    gateway.link(sensor)
    tic = 0
    #event loop
    while tic < maxTics:
        with open(sensor.cache.outfile, "a") as sensorF:
            print("---------------\n" + "BEGINNING TIC\n" + str(tic) +
                  "---------------\n", file=sensorF)
        with open(gateway.cache.outfile, "a") as gateF:
            print("---------------\n" + "BEGINNING TIC\n" + str(tic) +
                  "---------------\n", file=gateF)
        # Generate data and place into queue
        if tic % dataTics == 0:
            sensor.generate_data()

        # Send packets between devices
        if tic % networkTics == 0:
            sensor.receive_message()
            sensor.send_message()
            convert_cache_to_forest(sensor.cache.cache, sensor.cache.outfile)
            with open(sensor.cache.outfile, "a") as sensorF:
                print(sensor.cache, file=sensorF)

            gateway.receive_message()
            gateway.send_message()
            convert_cache_to_forest(gateway.cache.cache, gateway.cache.outfile)
            with open(gateway.cache.outfile, "a") as gateF:
                print(gateway.cache, file=gateF)
        tic += 1
   

   
    print("The number of data recorded by the system")
    print(sensor.num_data_sent - sensor.data_queue.qsize())
    print("The resulting cache at the sensor")
    print(sensor.cache)
    print("The resulting tree(s) at the sensor")
    convert_cache_to_forest(sensor.cache.cache, None)
    print("The resulting cache at the gateway")
    gateway.cache.cache.sort(key = lambda x: len(x.encoding))
    print(gateway.cache)
    convert_cache_to_forest(gateway.cache.cache, None)


    # print("Round Trip Times")
    # print(10)

    # with open("Round_trips_dope.csv", "w") as f:
    #     for i in range(0,len(sensor.insert_round_trips)):
    #         f.write(str(sensor.insert_round_trips[i])+"\n")

