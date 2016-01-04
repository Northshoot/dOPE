__author__ = 'WDaviau'
from comm.comm import Communicator
from .DataGenerator import DataGenerator
#from datastruct.binarytree import traverse_insert
from datastruct.scapegoat_tree import traverse_insert
from utils import debugmethods
import queue
import cache.CacheModelSuperNaive as cache

#@debugmethods
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

#@debugmethods
class Sensor(Tier):
    '''
    IoT Sensor Class
    '''
    def __init__(self, data_queue_len, distribution):
        super(Sensor,self).__init__('Sensor',Communicator())
        self.data_gen = DataGenerator(distribution)
        self.__sk = 0 # A dummy secret key that isn't used or properly initialized (yet)
        self.num_data_sent = 0
        self.num_gen = 0
        self.comp_req_queue = queue.Queue(1)
        self.data_queue = queue.Queue(data_queue_len)
        self.insert_round_trips = []

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
                comparison = self.comp_req_queue.get_nowait();
                self.insert_round_trips[-1] += 1
                self.communicator.send(comparison, 'order_query' )
            return

        # If nothing in the priority queue send enqueud data if any
        self.insert_round_trips.append(1)
        if not self.data_queue.empty():
            # If link to gateway is free
            if self.communicator.sent is None:
                cipher = self.data_queue.get_nowait()
                self.communicator.send(cipher, 'insert')
            return

    def generate_data(self):
        # Enqueue data for low priority sending 
        self.num_gen += 1
        plaintxt = self.data_gen.get_next() 
        cipher = self.encrypt(plaintxt)
        # Enqueue if there is room
        try:
            self.data_queue.put_nowait(cipher)
            self.num_data_sent += 1
        except queue.Full:
            # If there is not room in the queue drop data
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
            cmpc = packet.data[1]
            
            insertv = self.decrypt(insertc)
            cmpv = self.decrypt(cmpc)
            if insertv < cmpv:
                comparison = 0
            elif insertv > cmpv:
                comparison = 1
            else:
                raise ValueError('If the two values are equal their cipher text should be equal and the server should not have sent an order query')

            # Put this data into the priority queue reserved for order queries
            # This should be empty, and otherwise will throw an exception
            self.comp_req_queue.put_nowait(comparison)
            


#@debugmethods
class Gateway(Tier):
    '''
    IoT Gateway Class
    '''
    def __init__(self):
        super(Gateway,self).__init__('Gateway',Communicator(),Communicator())

    def receive_packet(self):
        # Check for data fom the sensor
        packet = self.communicator.read()
        if packet:
            if packet.call_type == 'insert':
                # Pass along to the server
                self.communicator2.send(packet.data,'insert')
            elif packet.call_type == 'order_query':
                # Pass along to the server
                self.communicator2.send(packet.data,'order_query')

        # Check for data from the server
        packet = self.communicator2.read()
        if packet:
            if packet.call_type == 'insert':
                raise ValueError('Server cannot send insert requests')
            elif packet.call_type == 'order_query':
                # Pass along to the sensor
                self.communicator.send(packet.data,'order_query')
        

#@debugmethods
class Server(Tier):
    '''
    Server Class
    '''
    def __init__(self):
        super(Server,self).__init__('Server',Communicator())
        self.mOPE_struct = None
        self.val_being_inserted = None
        self.encoding_being_inserted = None
        self.num_rebalances = 0

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

                self.val_being_inserted = packet.data
                self.encoding_being_inserted = []
                (val2cmp, new_struct, rebalanced) = traverse_insert(self.mOPE_struct,
                                       self.encoding_being_inserted, self.val_being_inserted)
                if val2cmp is None:
                    # Insert successful!
                    self.mOPE_struct = new_struct
                    self.val_being_inserted = None 
                    self.encoding_being_inserted = None
                    # Rebalancing can only happen on successful insert
                    if rebalanced:
                        self.num_rebalances += 1
                else:
                    order_query = [self.val_being_inserted,val2cmp]
                    self.communicator.send(order_query, 'order_query')

        elif packet.call_type == 'order_query':
            if packet.data == 0 or packet.data == 1:
                # The encoding of the value being inserted branches left if 0 right if 1
                self.encoding_being_inserted.append(packet.data)
                (val2cmp, new_struct, rebalanced) = traverse_insert(self.mOPE_struct,
                                        self.encoding_being_inserted, self.val_being_inserted)
                if val2cmp is None:
                    # Insert successful!
                    self.mOPE_struct = new_struct
                    self.val_being_inserted = None
                    self.encoding_being_inserted = None
                    # Rebalancing can only happen on successful insert
                    if rebalanced:
                        self.num_rebalances += 1
                else:
                    order_query = [self.val_being_inserted, val2cmp]
                    self.communicator.send(order_query, 'order_query')
            else:
                raise ValueError('Order query sent from sensor has non 1 or 0 value')

class dSensor(Tier):
    '''
    Sensor class in dOPE hierarchy.  Equipped to generate data and
    insert into the encoding cache or enqueue / drop data if inserts 
    are blocking and to send rebalance, insert, evict and sync messages
    as well as to receive insert response messages.
    '''
    def __init__(self, data_queue_len, distribution, cache_len, out_file):
        super(dSensor,self).__init__('Sensor',Communicator())
        self.data_gen = DataGenerator(distribution)
        self.__sk = 0 # A dummy secret key that isn't used or properly initialized (yet)
        self.num_data_sent = 0
        self.num_gen = 0
        self.comp_req_queue = queue.Queue(1)
        self.data_queue = queue.Queue(data_queue_len)
        self.insert_round_trips = []
        self.cache = cache.CacheModel(cache_len, out_file)

    def generate_data(self):
        ''' Method generate_data
        ------------------------
        Take the next data point from the data model set at init.
        Either insert, pipe data through the queue or drop
        '''
        # Enqueue data for low priority sending 
        self.num_gen += 1
        plaintxt = self.data_gen.get_next()
        if (len(self.cache.priority_messages) < 1 and not 
            self.cache.waiting_on_insert[0]):
            self.insert_round_trips.append(0)
            # If queue is not empty then pop one off
            if not self.data_queue.empty():
                popped_ptext = self.data_queue.get_nowait()
                self.data_queue.put_nowait(plaintxt)
                self.cache.insert(popped_ptext)
            else:
                self.cache.insert(plaintxt)
            self.num_data_sent += 1
            return

        # If sensor can't process immediately, enqueue 
        try:
            self.insert_round_trips[-1] += 1
            self.cache.logger.info("Insert blocking.  Number priority " +
                                   "messages outstanding: %d.\n "
                                   "Wating on insert: " 
                                   + str(self.cache.waiting_on_insert[0]),
                                   len(self.cache.priority_messages))
            self.data_queue.put_nowait(plaintxt)
            self.num_data_sent += 1
        except queue.Full:
            # If there is not room in the queue drop data
            return

    def send_message(self):
        ''' Method send_message
        -------------------------
        If a message is available from the cache to send then pass 
        along to the gateway
        '''
        if len(self.cache.priority_messages) > 0:
            message2send = self.cache.priority_messages.pop(0)
            self.communicator.send((message2send.entry, message2send.start_flag,
                                    message2send.end_flag),
                                  message2send.messageType)
        elif len(self.cache.sync_messages) > 0:
            message2send = self.cache.sync_messages.pop(0)
            self.cache.acknowledge_sync(message2send.entry)
            self.communicator.send((message2send.entry, False, False),
                                   message2send.messageType)

    def receive_message(self):
        ''' Method receive_message
        --------------------------
        If a message was sent to the sensor process and change state
        accordingly
        '''
        ## For debugging check for cache duplicates
        #assert(self.cache._unique_ciphers())
        #assert(self.cache._ordered())
        ##
        packet = self.communicator.read()
        if packet is None:
            return
        elif packet.call_type != "insert":
            raise ValueError("Higher tiers only send insert Responses")
        else:
            # continue inserted where we left off
            waiting, encoding, plaintxt = self.cache.waiting_on_insert
            assert(waiting)
            entry = packet.data
            self.cache.logger.info("Merging entry:\n " + str(entry))
            self.cache.merge([entry])
            self.cache.insert(plaintxt, encoding)


class dGateway(Tier):
    '''
    Gateway class in dOPE hierarchy.  Equipped to receive insert, 
    eviction, rebalance and sync messages and to send back insert 
    replies.
    '''
    def __init__(self, out_file):
        super(dGateway,self).__init__('Gateway',Communicator())
        self.rebalance_entries = []
        self.root_enc = None
        self.message2send = None
        self.cache = cache.CacheModel(None, out_file)

    def send_message(self):
        ''' Method send_message
        -----------------------
        If a message is availabe from the cache pass along to the 
        sensor
        '''
        # Check if there is a message to send
        if self.message2send is not None:
            self.communicator.send(self.message2send.entry, 
                                   self.message2send.messageType)
            self.message2send = None


    def receive_message(self):
        ''' Method receive_message
        --------------------------
        If a message is sent from the sensor process and change state 
        at the gateway
        '''
        ## For debugging check for unique ciphers
        #assert(self.cache._unique_ciphers())
        #assert(self.cache._ordered())
        ## END DEBUG

        packet = self.communicator.read()
        if packet is None:
            return
        else: 
            entry = packet.data[0]
            start_flag = packet.data[1]
            end_flag = packet.data[2]

        if packet.call_type == "insert":
            self.cache.logger.info("Receiving insert request")
            encoding = entry
            self.message2send = self.cache.insert_request(encoding) 
        elif packet.call_type == "rebalance":
            self.cache.logger.info("Receiving rebalance request")
            if start_flag:
                self.cache.logger.info("First in a possible series of " +
                                       "rebalance requests")
                if self.rebalance_entries != [] or self.root_enc is not None:
                    self.cache.logger.info("Rebalance Entries: " + 
                                           str(self.rebalance_entries))
                assert(self.rebalance_entries == [] and self.root_enc is None)
                # Initial rebalance entry is the root encoding
                self.root_enc = entry
            if not start_flag:
                self.rebalance_entries.append(entry)
            if end_flag:
                self.cache.logger.info("Last rebalance request of the series")
                self.cache.rebalance_request(self.rebalance_entries, 
                                             self.root_enc)
                self.root_enc = None
                self.rebalance_entries = []
        elif packet.call_type == "evict":
            self.cache.logger.info("Receiving eviction message")
            entry = packet.data[0]
            self.cache.merge_new([entry])
        elif packet.call_type == "sync":
            self.cache.logger.info("Receiving sync message with cipher: %d", 
                                   packet.data[0].cipher_text)
            entry = packet.data[0]
            assert(self.cache._index_of_encoding(entry.encoding) is None)
            self.cache.merge_new([entry])
        else:
            self.cache.logger.error("Packet of call type %s received", 
                                    packet.call_type)
            raise ValueError("Unrecognized packet type sent to gateway")



