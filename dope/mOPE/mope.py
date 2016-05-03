__author__ = 'WDaviau'
from ..tiers import Sensor, Gateway, Server

'''
Functions defining mOPE simulation
'''

def mOPE_baseline(maxTics, dataTics, networkTics, data_queue_len, k,
                  distribution = 'random', data_file=None):
    #initialization and linking of tiers
    sensor = Sensor(data_queue_len, distribution, data_file)
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
                print("Finished! Gateway received " + str(gateway.sensor_message_count) + " Gateway sent " + str(gateway.cloud_message_count))
                print(server.mOPE_struct.num_rebal)
                print("Number of ciphers received at sensor: " + str(sensor.ciphers_from_cloud))
                print('Number of ciphers sent by sensor: ' + str(sensor.num_data_sent))
                print('Avg message size: ' + str(sensor.avg_msg_size))
                print('Avg traversals: ' + str(server.avg_traversal))
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
    print("The resulting tree structure")
    #print(list(server.mOPE_struct))
    print( "For " + str( sensor.num_data_sent - sensor.data_queue.qsize()) + " total inserts")
    print("And " + str(sensor.num_gen - sensor.num_data_sent) + " dropped packets")
 