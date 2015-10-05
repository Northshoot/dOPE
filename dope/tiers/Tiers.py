__author__ = 'WDaviau'
from comm import Communicator
from DataGenerator import DataGenerator
from DataStructureModel import DataStructureModel

class Tier(object):
	'''
	IoT Tier Class
	'''
    def __init__(self,space,comm,comm2=None):
        self.space = space
        self.communicator = comm
        # only the gateway needs two communication channnels
        self.communicator2 = comm2

    def link(self,other_tier,other_tier2=None):
        self.communicator.connect(other_tier.communicator)
        other_tier.communicator.connect(self.communicator)
        if self.space == 'Gateway':
            self.communicator2.connect(other_tier2.communicator)
            other_tier2.communicator.connect(self.communicator2)


class Sensor(Tier):
	'''
	IoT Sensor Class
	'''
    def __init__(self):
        super('Sensor',Communicator())
        self.data_gen = DataGenerator()
        # initialize cryptographic keys

    def newData(self):
        return self.data_gen.new()

    def encrypt(self,plaintxt):
        pass

    def decrypt(self,cipher):
        pass

class Gateway(Tier):
	'''
	IoT Gateway Class
	'''
    def __init__(self):
    	super('Gateway',Communicator(),Communicator)
      

class Server(Tier):
	'''
	Server Class
	'''
    def __init__(self):
    	super('Server',Communicator())
    	self.mOPE_struct = DataStructureModel

