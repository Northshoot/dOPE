__author__ = 'WDaviau'

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
  		# Sensor -- Generate (encrypted) data
  		# 			Send data
  		#			Receive data



  		# Gateway -- Receive data
  		#			 Send data



  		# Server -- Receive data
  		#			Send data


