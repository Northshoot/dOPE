__author__ = 'WDaviau'
from ..tiers import Sensor, Gateway, Server
import logging
import time
from ..utils.printer import stats_string

'''
Functions defining mOPE simulation
'''

def mOPE_baseline(maxTics, dataTics, networkTics, data_queue_len, k,
                  distribution = 'random', data_file=None, num_data=1000):

    ts = str(time.asctime(time.localtime()))
    logfile = "mope_log_"+ts+".log"
    logger = logging.getLogger(logfile)
    fh = logging.FileHandler(logfile)
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)

    #initialization and linking of tiers
    sensor = Sensor(data_queue_len, distribution, data_file, num_data = num_data)
    gateway = Gateway()
    server = Server(k)

    sensor.link(gateway)
    gateway.link(sensor,server)
    tic = 0
    #event loop
    while True:
        tic += 1
        # Generate data and place in lower priority queue.
        if tic % dataTics == 0:
            sensor.generate_data()
            if sensor.done:
                avg_msg_size = sum(sensor.avg_msg_size)/len(sensor.avg_msg_size)
                avg_travs = sum(server.avg_traversal)/len(server.avg_traversal)
                ret = stats_string(str(sensor.num_data_sent), 
                                   "N/A", 
                                   str(server.mOPE_struct.num_rebal),
                                   "N/A",
                                   "N/A",
                                   str(gateway.cloud_message_count),
                                   str(gateway.cloud_message_count),
                                   "N/A",
                                   "N/A",
                                   "N/A",
                                   str(sensor.num_data_sent),                                   
                                   str(sensor.ciphers_from_cloud),
                                   str(round(avg_msg_size, 2)),
                                   "N/A",
                                   str(round(avg_travs, 2)),
                                   str(round(avg_travs, 2)))

                print(ret)
                logger.info(ret)
                break

        # Send packets between devices
        if tic % networkTics == 0:
            # Check for order queries to process
            sensor.receive_packet()
            sensor.send_data()

        # Pipe order queries and inserts between sensor and server
        gateway.receive_packet()

        # Receive sensor order and insert info and send back more order queries
        server.receive_packet()

        # In case of order_queries pipe packet between server and sensor
        gateway.receive_packet()


  # Print the resulting mOPE data struct at the server
    #print("The resulting tree structure")
    #print(list(server.mOPE_struct))

 