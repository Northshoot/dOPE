__author__ = 'WDaviau'
from comm.comm import Communicator
from .DataGenerator import DataGenerator
#from datastruct.binarytree import traverse_insert
from datastruct.scapegoat_tree import traverse_insert
from utils import debugmethods
import queue
import cache.FasterCMSN as cache

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

class dSensor(Tier):
    '''
    Sensor class in dOPE hierarchy.  Equipped to generate data and
    insert into the encoding cache or enqueue / drop data if inserts 
    are blocking and to send rebalance, insert, evict and sync messages
    as well as to receive insert response messages.
    '''
    def __init__(self, data_queue_len, distribution, cache_len, out_file):
        super(dSensor,self).__init__('Sensor',Communicator())
        self.data_gen = DataGenerator(distribution, bounds = [-1000,1000])
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
            self.cache.acknowledge_sync(message2send.entry.encoding)
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
            assert(self.cache._entry_with_encoding(entry.encoding) is None)
            self.cache.merge_new([entry])
        else:
            self.cache.logger.error("Packet of call type %s received", 
                                    packet.call_type)
            raise ValueError("Unrecognized packet type sent to gateway")

