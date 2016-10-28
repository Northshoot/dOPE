__author__ = 'WDaviau'
from ..comm import Communicator
from .DataGenerator import DataGenerator
from ..datastruct import BTree
import queue


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
        if self.communicator2 is not None:
            self.communicator2.connect(other_tier2.communicator)
            other_tier2.communicator.connect(self.communicator2)


class Sensor(Tier):
    '''
    IoT Sensor Class
    '''
    def __init__(self, data_queue_len, distribution, data_file=None, num_data=1000):
        super(Sensor,self).__init__('Sensor',Communicator())
        print("mmope")
        self.data_gen = DataGenerator(distribution, data_file, bounds = [-500, 500], data_num = num_data)
        self.__sk = 0 # A dummy secret key that isn't used or properly initialized (yet)
        self.num_data_sent = 0
        self.ciphers_from_cloud = 0
        self.avg_msg_size = []
        self.num_gen = 0
        self.comp_req_queue = queue.Queue(1)
        self.data_queue = queue.Queue(data_queue_len)
        self.insert_round_trips = []
        self.done = False
        self.sim_lim = None

    @property
    def sim_lim_reached(self):
        if self.sim_lim is None:
            return False
        else:
            return self.num_data_sent == self.sim_lim

    def encrypt(self,plaintxt):
        # A dummy encryption function that doesn't do anything
        return plaintxt

    def decrypt(self,cipher):
        # A dummy  decryption function that doesn't do anything
        return cipher

    def send_data(self):
        # Check priority queue and send that data if any
        if not self.comp_req_queue.empty():
            # If link to gateway is free
            if self.communicator.sent is None:
                comparison = self.comp_req_queue.get_nowait()
                self.insert_round_trips[-1] += 1
                self.communicator.send(comparison, 'order_query' )
            return

        # If nothing in the priority queue send enqueud data if any
        self.insert_round_trips.append(1)
        if not self.data_queue.empty():
            # If link to gateway is free
            if self.communicator.sent is None:
                cipher = self.data_queue.get_nowait()
                self.num_data_sent += 1
                self.communicator.send(cipher, 'insert')
            return

    def generate_data(self):
        # Enqueue data for low priority sending 
        self.num_gen += 1
        plaintxt = self.data_gen.get_next()
        if plaintxt is None and self.data_queue.empty():
            self.done = True
            return
        cipher = self.encrypt(plaintxt)
        # Enqueue if there is room
        try:
            if plaintxt is not None:
                self.data_queue.put_nowait(cipher)
        except queue.Full:
            # If there is not room in the queue drop data
            print("drops")
            return

    def receive_packet(self):
        packet = self.communicator.read()
        if packet is None:
            return
        elif packet.call_type == 'insert':
            raise ValueError('Server cannot send insert requests')
        elif packet.call_type == 'order_query':
            # look up whether the value being inserted is 
            # greater than less than or equal to the compared value
            insertc = packet.data[0]
            compare, overwrite, enc = packet.data[1]
            self.ciphers_from_cloud += len(compare)
            self.avg_msg_size.append(len(compare))
            # Dummy decryption of ciphers
            insertv = self.decrypt(insertc)  # Dummy decryption of ciphers
            comparev = compare
            if insertv in comparev:
                raise ValueError('If the two values are equal their cipher ' + 
                                 'text should be equal and the server should ' +
                                 'not have sent an order query')

            # Find next index
            if comparev == []:
                next = 0
            else:
                i = 0
                while i < len(compare) and compare[i] < insertv:
                    i += 1
                next = i
            # Append to or overwrite encoding
            if overwrite >= 0:
                # clear last overwrite elements from enc
                del enc[-1*overwrite:]
            # add next
            enc.append(next)

            # Put new enc into the priority queue reserved for order queries
            # This should be empty, and otherwise will throw an exception
            self.comp_req_queue.put_nowait(enc)
            

class Gateway(Tier):
    '''
    IoT Gateway Class
    '''
    def __init__(self):
        super(Gateway,self).__init__('Gateway',Communicator(),Communicator())
        self.sensor_message_count = 0
        self.cloud_message_count = 0

    def receive_packet(self):
        # Check for data fom the sensor
        packet = self.communicator.read()
        if packet:
            self.sensor_message_count += 1
            if packet.call_type == 'insert':
                # Pass along to the server
                self.communicator2.send(packet.data,'insert')
            elif packet.call_type == 'order_query':
                # Pass along to the server
                self.communicator2.send(packet.data,'order_query')

        # Check for data from the server
        packet = self.communicator2.read()
        if packet:
            self.cloud_message_count += 1
            if packet.call_type == 'insert':
                raise ValueError('Server cannot send insert requests')
            elif packet.call_type == 'order_query':
                # Pass along to the sensor
                self.communicator.send(packet.data,'order_query')

class Server(Tier):
    '''
    Server Class
    '''
    def __init__(self, k):
        super(Server,self).__init__('Server',Communicator())
        self.mOPE_struct = BTree(k)
        self.val_being_inserted = None
        self.encoding_being_inserted = None
        self.traversals = 0
        self.avg_traversal = []

    def receive_packet(self):
        packet = self.communicator.read()
        if packet is None:
            return

        elif packet.call_type == 'insert':
            # Server begins insert
            if self.val_being_inserted:
                # Only one insert at a time
                return
            else:
                ################# For debugging print all data being inserted
                #print("Server inserting:" + str(packet.data))
                #################
                self.traversals += 1
                self.val_being_inserted = packet.data
                self.encoding_being_inserted = []
                (compare, overwrite) = self.mOPE_struct.insert_enc(self.val_being_inserted,
                                                                   self.encoding_being_inserted)
                if compare is None:
                    # Insert successful!
                    self.val_being_inserted = None 
                    self.encoding_being_inserted = None
                    self.avg_traversal.append(self.traversals)
                    self.traversals = 0
                else:
                    order_query = [self.val_being_inserted, (compare, overwrite, self.encoding_being_inserted)]
                    self.communicator.send(order_query, 'order_query')

        elif packet.call_type == 'order_query':
            self.traversals += 1
            self.encoding_being_inserted = packet.data
            (compare, overwrite) = self.mOPE_struct.insert_enc(self.val_being_inserted,
                                                               self.encoding_being_inserted)
            if compare is None:
                # Insert successful!
                self.val_being_inserted = None
                self.encoding_being_inserted = None
                self.avg_traversal.append(self.traversals)
                self.traversals = 0
            else:
                order_query = [self.val_being_inserted, (compare, overwrite, self.encoding_being_inserted)]
                self.communicator.send(order_query, 'order_query')




