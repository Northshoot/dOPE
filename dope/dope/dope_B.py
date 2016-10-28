__author__ = 'Wdaviau'
from ..tiers import dSensor_B, dGateway_B, dServer_B
import time
from functools import reduce
from ..utils import print_ctrl
from ..utils.printer import stats_string
import matplotlib.pyplot as plt


def dOPE_B(maxTics, dataTics, networkTics, data_queue_len, sensor_cache_len,
           gate_cache_len, distribution = 'random', k = 10, data_file = None,
           num_data=1000):
    print("dope")
    ts = str(time.asctime(time.localtime()))
    sensor = dSensor_B(data_queue_len, distribution, sensor_cache_len, 
                     "dSensorCache" + ts +".log", k, data_file, num_data)
    gateway = dGateway_B("dGatewayCache" + ts + ".log", gate_cache_len, k)
    server = dServer_B("dServerCache" + ts + ".log", k)
    sensor.link(gateway)
    gateway.link(sensor,server)
    tic = 0
    #event loop
    sensor.cache.logger.info("Sensor Cache Size = " + str(sensor_cache_len))

    while tic < maxTics:
        sensor.cache.logger.debug("---------------\n" + "BEGINNING TIC\n" +
                                  str(tic) + "---------------\n")
        gateway.cache.logger.debug("---------------\n" + "BEGINNING TIC\n" +
                                  str(tic) + "---------------\n")
        server.cache.logger.debug("---------------\n" + "BEGINNING TIC\n" +
                                  str(tic) + "---------------\n")


        #Generate data and place into queue
        if tic % dataTics == 0:
            sensor.generate_data()
            if sensor.done:
                #print(server.tree)
                n_miss_inserts = len(gateway.num_traversals)
                avg_traversals = reduce(lambda a, x: [a[0]+x[0], a[1]+x[1]], gateway.num_traversals, [0,0])
                avg_traversals[0] /= n_miss_inserts
                avg_traversals[1] /= n_miss_inserts
                avg_msg_size = sum(sensor.avg_msg_size)/len(sensor.avg_msg_size)
                ret = stats_string(str(sensor.cache.insert_count), 
                                   str(server.repeat_count),
                                   str(server.tree.num_rebal),
                                   str(sensor.cache.evict_count),
                                   str(sensor.cache.rebal_count),
                                   str(gateway.sensor_message_count), 
                                   str(gateway.cloud_message_count),
                                   str(gateway.miss_count),
                                   str(gateway.sync_count),
                                   str(gateway.rebal_count),
                                   str(sensor.total_ciphers_sent),
                                   str(sensor.total_ciphers_received),
                                   str(round(avg_msg_size,2)),
                                   str(n_miss_inserts),
                                   str(round(avg_traversals[1] + avg_traversals[0],2)),
                                   str(round(avg_traversals[0],2)))
                print(ret)

                sensor.cache.logger.info(ret)
                gateway.cache.logger.info(ret)
                server.cache.logger.info(ret)
                plt.plot(sensor.insert_round_trips, 'b*-')
                plt.plot(sensor.rebalance_events, 'r*-')
                plt.xlabel("Insert number")
                plt.ylabel("Number of round trips")
                plt.title("Dope round trips over inserts")
                plt.show()
                #print('Send message count: ' + str(sensor.send_message_count))
                #print('Plaintexts who miss: ' + str(sensor.cache.plaintexts_who_miss))


                break
        # Send packets between devices
        if tic % networkTics == 0:
            sensor.receive_message()
            sensor.send_message()

            gateway.receive_sensor_message()
            for entry in gateway.cache.cache:
                assert(entry not in sensor.cache.cache)
            gateway.send2server()

            server.receive_message()
            server.send_message()

            gateway.receive_server_message()
            gateway.send2sensor()

        tic += 1
        print_ctrl(tic)
   


