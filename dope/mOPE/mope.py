__author__ = 'WDaviau'
from tiers.Tiers import Sensor, Gateway, Server
'''
Functions defining mOPE simulation
'''
def mOPE_baseline(nSIMSTEPS):
    #initialization and linking of tiers
    sensor = Sensor()
    gateway = Gateway()
    server = Server()

    sensor.link(gateway)
    gateway.link(sensor,server)

    
  	#event loop
    for i in range(0,nSIMSTEPS):
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

    # Print the resulting mOPE data struct at the servre
    print("The resulting tree structure")
    print(server.mOPE_struct)
    return


