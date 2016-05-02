__author__ = 'Wdaviau'
from ..tiers import dSensor, dGateway, dServer
from time import time
from functools import reduce
from ..utils import print_ctrl


def dOPE(maxTics, dataTics, networkTics, data_queue_len, sensor_cache_len,
         gate_cache_len, distribution = 'random', k = 5, data_file = None):
    print("dope")
    ts = str(time())
    sensor = dSensor(data_queue_len, distribution, sensor_cache_len, 
                     "dSensorCache" + ts +".log", k, data_file)
    gateway = dGateway("dGatewayCache" + ts + ".log", gate_cache_len, k)
    server = dServer("dServerCache" + ts + ".log", k)
    sensor.link(gateway)
    gateway.link(sensor,server)
    tic = 0
    #event loop
    while tic < maxTics:
        # with open(sensor.cache.outfile, "a") as sensorF:
        #     print("---------------\n" + "BEGINNING TIC\n" + str(tic) +
        #           "---------------\n", file=sensorF)
        # with open(gateway.cache.outfile, "a") as gateF:
        #     print("---------------\n" + "BEGINNING TIC\n" + str(tic) +
        #           "---------------\n", file=gateF)
        # with open(server.cache.outfile, "a") as servF:
        #     print("---------------\n" + "BEGINNING TIC\n" + str(tic) +
        #           "---------------\n", file=servF)

        #Generate data and place into queue
        if tic % dataTics == 0:
            sensor.generate_data()
            if sensor.done:
                print("Finished! Gateway received " + str(gateway.sensor_message_count) + " Gateway sent " + str(gateway.cloud_message_count))
                print("Misses: " + str(gateway.miss_count) )
                print("Syncs: " + str(gateway.sync_count))
                print("Rebals: " + str(gateway.rebal_count))
                print("Evictions: " + str(sensor.cache.evict_count))
                print("Number of ciphers received at sensor: " + str(sensor.total_ciphers_received))
                print('Number of ciphers sent by sensor: ' + str(sensor.total_ciphers_sent))

                n_miss_inserts = len(gateway.num_traversals)
                print('Number of inserts requiring traversal: ' + str(n_miss_inserts))
                avg_traversals = reduce(lambda a, x: [a[0]+x[0], a[1]+x[1]], gateway.num_traversals, [0,0])
                avg_traversals[0] /= n_miss_inserts
                avg_traversals[1] /= n_miss_inserts
                print('Traversal breakdown: ' + str(avg_traversals))
                print('Send message count: ' + str(sensor.send_message_count))
                print('Plaintexts who miss: ' + str(sensor.cache.plaintexts_who_miss))


                break
        # Send packets between devices
        if tic % networkTics == 0:
            sensor.receive_message()
            sensor.send_message()
            # with open(sensor.cache.outfile, "a") as sensorF:
            #     print(sensor.cache, file=sensorF)
            #     print(sensor.cache.cache, file=sensorF)
            #     print(sensor.cache.cache_lookup, file=sensorF)
            gateway.receive_sensor_message()
            for entry in gateway.cache.cache:
                assert(entry not in sensor.cache.cache)
            gateway.send2server()
            # with open(gateway.cache.outfile, "a") as gateF:
            #     print(gateway.cache, file=gateF)
            #     print(gateway.cache.cache, file=gateF)
            server.receive_message()
            server.send_message()
            # with open(server.cache.outfile, "a") as serverF:
            #     print(server.cache, file=serverF)
            gateway.receive_server_message()
            gateway.send2sensor()

        tic += 1
        print_ctrl(tic)
   

   
    print("The number of data recorded by the system")
    print(sensor.num_data_sent - sensor.data_queue.qsize())
    # print("The resulting cache at the sensor")
    # print(sensor.cache)
    # print("The resulting tree(s) at the sensor")
    #convert_cache_to_forest(sensor.cache.cache, None)
    #print("The resulting cache at the gateway")
    #gateway.cache.cache.sort(key = lambda x: len(x.node_encoding))
    #print(gateway.cache)
    #print(list(server.tree))
    #convert_cache_to_forest(gateway.cache.cache, None)


    # print("Round Trip Times")
    # print(10)

    # with open("Round_trips_dope.csv", "w") as f:
    #     for i in range(0,len(sensor.insert_round_trips)):
    #         f.write(str(sensor.insert_round_trips[i])+"\n")

