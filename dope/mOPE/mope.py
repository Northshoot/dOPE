__author__ = 'WDaviau'
from tiers.Tiers import Sensor, Gateway, Server
from comm.packet import Packet
import csv

'''
Functions defining mOPE simulation
'''

# For use debugging communication channels
def print_sensor_comm(sensor):
  print("Sensor -> gateway: " + str(sensor.communicator.sent) )
  print("Gateway -> sensor: " + str(sensor.communicator.received) )
  print("\n")

def print_server_comm(server):
  print("Server -> gateway: " + str(server.communicator.sent) )
  print("Gateway -> server: " + str(server.communicator.received) )
  print("\n")

def print_gateway_comm(gateway):
  print("Gateway -> sensor: " + str(gateway.communicator.sent) )
  print("Sensor -> gateway: " + str(gateway.communicator.received) )
  print("Gateway -> server: " + str(gateway.communicator2.sent) )
  print("Server -> gateway: " + str(gateway.communicator2.received) )
  print("\n")


def mOPE_baseline(maxTics, dataTics, networkTics, data_queue_len, distribution = 'random'):
 
  #initialization and linking of tiers
  sensor = Sensor(data_queue_len, distribution)
  gateway = Gateway()
  server = Server()

  sensor.link(gateway)
  gateway.link(sensor,server)
  tic = 0
  #event loop
  while tic < maxTics:
    tic += 1
    # Generate data and place in lower priority queue.
    if tic % dataTics == 0:
      sensor.generate_data()
  
      #print("Queue size: " + str(sensor.data_queue.qsize()))

    # Send packets between devices
    if tic % networkTics == 0:
      # Check for order queries to process
      sensor.receive_packet()
      sensor.send_data();

      # Pipe order queries and inserts between sensor and server
      gateway.receive_packet()

      # Receive sensor order and insert info and send back more order queries
      server.receive_packet()

      # In case of order_queries pipe packet between server and sensor
      gateway.receive_packet()


  # Print the resulting mOPE data struct at the server
  print("The resulting tree structure")
  print(server.mOPE_struct)
  print( "For " + str( sensor.num_data_sent - sensor.data_queue.qsize()) + " total inserts")
  print("Causing " + str(server.num_rebalances) + " rebalances\n")
  print("And " + str(sensor.num_gen - sensor.num_data_sent) + " dropped packets")
  
  
   
  # # Print out Table showing 
  # print("-------- Drops for Q lengths N/D ratio = 1/" + str(dataTics) + " --------")
  # for i in range(1,1000):
  #     print(str(i) + "--- " + str(DataMatrix[i][dataTics]))
 
  with open("Round_trips.csv", "w") as f:
    for i in range(0,len(sensor.insert_round_trips)):
      f.write(str(sensor.insert_round_trips[i])+"\n")

 