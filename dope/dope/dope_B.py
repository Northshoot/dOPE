__author__ = 'Wdaviau'
from ..tiers import dSensor, dGateway, dServer
import time
from functools import reduce
from ..utils import print_ctrl


def dOPE(maxTics, dataTics, networkTics, data_queue_len, sensor_cache_len,
         gate_cache_len, distribution = 'random', k = 5, data_file = None):
    print("dope")
    ts = str(time.asctime(time.localtime()))
    sensor = dSensor(data_queue_len, distribution, sensor_cache_len, 
                     "dSensorCache" + ts +".log", k, data_file)
    gateway = dGateway("dGatewayCache" + ts + ".log", gate_cache_len, k)
    server = dServer("dServerCache" + ts + ".log", k)
    sensor.link(gateway)
    gateway.link(sensor,server)
    tic = 0
    #event loop
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
                n_miss_inserts = len(gateway.num_traversals)
                avg_traversals = reduce(lambda a, x: [a[0]+x[0], a[1]+x[1]], gateway.num_traversals, [0,0])
                avg_traversals[0] /= n_miss_inserts
                avg_traversals[1] /= n_miss_inserts

                ret = "----------------Finished!---------------\n"
                ret += "***Total insersts = " + str(sensor.cache.insert_count) +"***\n"
                ret += "***Total repeated syncs " + str(server.repeat_count) + "***\n"
                ret += "----------------Messages----------------\n"
                ret += "|Embedded to Gateway | Gateway to Cloud|\n"
                ret += "|--------------------|-----------------|\n"
                ret += "|        " + str(gateway.sensor_message_count) + "            |" + str(gateway.cloud_message_count) +"         |\n"
                ret += "----------------------------------------\n"
                ret += "|   Misses  |   Syncs   |  Rebalances   |\n"
                ret += "|-----------|-----------|---------------|\n"
                ret += "|  " + str(gateway.miss_count) + "    |    " + str(gateway.sync_count) + "   |   " + str(gateway.rebal_count) + "  |\n\n"
                ret += "----------------Ciphertexts sent, proxy for bytes sent----------------\n"
                ret += "| Number of ciphertexts sent by the sensor: " + str(sensor.total_ciphers_sent) + "\n"
                ret += "| Number of ciphertexts sent back to the sensor: " + str(sensor.total_ciphers_received) + "\n\n"
                ret += "----------------Miss Breakdown----------------\n"
                ret += "Number of inserts requiring traversal: " + str(n_miss_inserts) +"\n"
                ret += "| Average miss gateway hits | Average miss cloud hits|\n"
                ret += "--------------------------------------------------------\n"
                ret += "|    " + str(avg_traversals[1]) + "        |   " + str(avg_traversals[0]) + "     |\n"

                sensor.cache.logger.info(ret)
                gateway.cache.logger.info(ret)
                server.cache.logger.info(ret)
                # print("Finished! Gateway received " + str(gateway.sensor_message_count) + " Gateway sent " + str(gateway.cloud_message_count))
                # print("Misses: " + str(gateway.miss_count) )
                # print("Syncs: " + str(gateway.sync_count))
                # print("Rebals: " + str(gateway.rebal_count))
                # print("Evictions: " + str(sensor.cache.evict_count))
                # print("Number of ciphers received at sensor: " + str(sensor.total_ciphers_received))
                # print('Number of ciphers sent by sensor: ' + str(sensor.total_ciphers_sent))

                # n_miss_inserts = len(gateway.num_traversals)
                # print('Number of inserts requiring traversal: ' + str(n_miss_inserts))
                # avg_traversals = reduce(lambda a, x: [a[0]+x[0], a[1]+x[1]], gateway.num_traversals, [0,0])
                # avg_traversals[0] /= n_miss_inserts
                # avg_traversals[1] /= n_miss_inserts
                # print('Traversal breakdown: ' + str(avg_traversals))
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
   


