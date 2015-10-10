__author__ = 'WDaviau'
from comm.comm import Communicator
from comm.packet import Packet
from DataGenerator import DataGenerator
from datastruct.binarytree import BSTree, traverse_insert
from cryptography.fernet import Fernet

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
        super(Sensor,self).__init__('Sensor',Communicator())
        self.data_gen = DataGenerator()
        self.__sk = 0 # A dummy secret key that isn't used or properly initialized (yet)

    def encrypt(self,plaintxt):
        # A dummy encryption function that doesn't do anything
        return plaintxt

    def decrypt(self,cipher):
        # A dummy  decryption function that doesn't do anything
        return cipher

    def generate_send_data(self):
        # Note data is simply dropped if the gateway channel is busy
        plaintxt = self.data_gen.get_next() 
        cipher = self.encrypt(plaintxt)
        self.communicator.send(cipher,'insert')

    def receive_packet(self):
        packet = self.communicator.read()
        if packet == None:
            return
        elif packet.call_type == 'insert':
            raise ValueError('Server cannot send insert requests')
        elif packet.call_type == 'order_query':
            # look up whether the value being inserted is 
            # greater than less than or equal to the compared value
            insertc = packet.data[0]
            cmpc = packet.data[1]
            
            insertv = self.decrypt(insertc)
            cmpv = self.decrypt(cmpc)
            if insertv < cmpv:
                comparison = 0
            elif insertv > cmpv:
                comparison = 1
            else:
                raise ValueError('If the two values are equal their cipher text should be equal')
            self.communicator.send(comparison,'order_query')

class Gateway(Tier):
    '''
    IoT Gateway Class
    '''
    def __init__(self):
        super(Gateway,self).__init__('Gateway',Communicator(),Communicator())

    def receive_packet(self):
        # Check for data fom the sensor
        packet = self.communicator.read()
        if packet == None:
            return
        elif packet.call_type == 'insert':
            # Pass along to the server
            self.communicator2.send(packet.data,'insert')
        elif packet.call_type == 'order_query':
            # Pass along to the server
            self.communicator2.send(packet.data,'order_query')

        # Check for data from the server
        packet = self.communicator2.read()
        if packet == None:
            return
        elif packet.call_type == 'insert':
            raise ValueError('Server cannot send insert requests')
        elif packet.call_type == 'order_query':
            # Pass along to the sensor
            self.communicator.send(packet.data,'order_query')
        

class Server(Tier):
    '''
    Server Class
    '''
    def __init__(self):
        super(Server,self).__init__('Server',Communicator())
        self.mOPE_struct = None
        self.val_being_inserted = None
        self.encoding_being_inserted = None

    def receive_packet(self):
        packet = self.communicator.read()
        if packet == None:
            return
        elif packet.call_type == 'insert':
            # Server begins insert
            if self.val_being_inserted != None:
                # Only one insert at a time
                return
            else:
                ################# For debugging print all data being inserted
                print "Server inserting:" + str(packet.data)
                #################
                self.val_being_inserted = packet.data
                self.encoding_being_inserted = []
                (val2cmp,new_struct) = traverse_insert(self.mOPE_struct,
                                       self.encoding_being_inserted,self.val_being_inserted)
                if val2cmp == None:
                    # Insert successful!
                    self.mOPE_struct = new_struct
                    self.val_being_inserted = None   
                else:
                    order_query = [self.val_being_inserted,val2cmp]
                    self.communicator.send(order_query,'order_query')
        elif packet.call_type == 'order_query':
            print "Server is getting an order query"
            if packet.data == 0 or packet.data == 1:
                # The encoding of the value being insert branches left if 0 right if 1
                self.encoding_being_inserted.append(packet.data)
                print "encoding before: " + str(self.encoding_being_inserted)
                (val2cmp, new_struct) = traverse_insert(self.mOPE_struct,
                                        self.encoding_being_inserted,self.val_being_inserted)
                if val2cmp == None:
                    # Insert successful!
                    self.mOPE_struct = new_struct
                    self.val_being_inserted = None
                    self.encoding_being_inserted = None
                else:
                    order_query = [self.val_being_inserted,val2cmp]
                    self.communicator.send(order_query,'order_query')
            else:
                raise ValueError('Order query sent from sensor has non 1 or 0 value')

