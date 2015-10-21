__author__ = 'WDaviau'
from tiers.Tiers import Sensor, Gateway, Server
from comm.packet import Packet
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


def mOPE_baseline(numINSERTSMAX):
    #recording data
    out_data = []
    for numINSERTS in range(0,numINSERTSMAX,10):
      #initialization and linking of tiers
      sensor = Sensor()
      gateway = Gateway()
      server = Server()

      sensor.link(gateway)
      gateway.link(sensor,server)
      round = 0
  	 #event loop
      while sensor.num_sent < numINSERTS + 1:
        round += 1
        # Check for order queries to process
        # Generate data and send if connection is not busy
        # with order queries
        sensor.receive_packet()
        sensor.generate_send_data()

        # Pipe order queries and inserts between sensor and server
        gateway.receive_packet()

        # Receive sensor order and insert info and send back more order queries
        server.receive_packet()

        # In case of order_queries pipe packet between server and sensor
        gateway.receive_packet()
      # Print the resulting mOPE data struct at the server
      print("The resulting tree structure")
      print(server.mOPE_struct)
      print("For a total of " + str(round-1) + " RTTs. " + str(sensor.num_gen - numINSERTS -1) + " data points dropped. ")
      out_data.append(round)
    return out_data


