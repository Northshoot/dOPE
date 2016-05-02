__author__ = 'WDaviau'
from comm.comm import Communicator
from .DataGenerator import DataGenerator
from datastruct.scapegoat_tree import traverse_insert
from utils import debugmethods
import queue
import cache.CacheModelFull as cache
from cache.CacheModelFull import OutgoingMessage, CacheEntry
import copy

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
        self.num_data_sent = 0
        self.num_gen = 0
        self.comp_req_queue = queue.Queue(1)
        self.data_queue = queue.Queue(data_queue_len)
        self.insert_round_trips = []
        self.cache = cache.CacheModel(cache_len, out_file)
        self.done = False
        # For recording more precise dope statistics
        self.total_ciphers_sent = 0
        self.total_ciphers_received = 0

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
                if popped_ptext == -9999:
                    self.done = True;
                    return
                self.data_queue.put_nowait(plaintxt)
                self.cache.insert(popped_ptext)
            else:
                if plaintxt == -9999:
                    self.done = True;
                    return
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
            if isinstance(message2send.entry, CacheEntry):
                self.total_ciphers_sent += 1

            self.communicator.send((message2send.entry, 
                                    message2send.start_flag,
                                    message2send.end_flag),
                                   message2send.messageType)
        elif len(self.cache.sync_messages) > 0:
            self.total_ciphers_sent += 1
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
        assert(self.cache._unique_ciphers())
        assert(self.cache._ordered())
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
            entry = packet.data[0]
            self.total_ciphers_received += 1
            self.cache.logger.info("Merging entry:\n " + str(entry))
            self.cache.merge([entry])
            self.cache.insert(plaintxt, encoding)


class dGateway(Tier):
    '''
    Gateway calss in dOPE heirarchy.  Intermediary between Sensor and
    Server.  Forwards sync messages, propogates evictions when cache is
    full, pushes rebalance messages through to server and flushes 
    cache, responds to insert messages querying server if necessary
    '''
    def __init__(self, out_file, cache_len = 1000):
        super(dGateway,self).__init__('Gateway', Communicator(), Communicator())
        self.rebalance_received = []
        self.rebalance2send = []
        self.rebalance_root_enc = None
        self.sensor_msg2send = None
        self.server_msg2send = None
        self.cache = cache.CacheModel(cache_len, out_file)
        self.sensor_message_count = 0
        self.sync_count = 0
        self.rebal_count = 0
        self.miss_count = 0
        self.evict_count = 0
        self.cloud_message_count = 0
        self.num_traversals = []
        self.ongoing_traversal = False


    def send2sensor(self):
        ''' Method send_message
        -----------------------
        Send messages to both sensor and server
        '''
        if self.sensor_msg2send is not None:
            self.communicator.send((self.sensor_msg2send.entry,
                                    self.sensor_msg2send.start_flag,
                                    self.sensor_msg2send.end_flag),
                                   self.sensor_msg2send.messageType)
            self.sensor_msg2send = None

    def send2server(self):
        if self.server_msg2send is not None:
            self.cloud_message_count += 1
            self.cache.logger.info("Sending message to server")
            self.communicator2.send((self.server_msg2send.entry,
                                     self.server_msg2send.start_flag,
                                     self.server_msg2send.end_flag),
                                    self.server_msg2send.messageType)
            self.server_msg2send = None
        elif len(self.rebalance2send) > 0:
            
            rebalance_msg = self.rebalance2send.pop(0)
            self.communicator2.send((rebalance_msg.entry,
                                     rebalance_msg.start_flag,
                                     rebalance_msg.end_flag),
                                    rebalance_msg.messageType)
            self.cache.logger.info("Sending rebalance request with cipher: " +
                                   str(rebalance_msg.entry.cipher_text) + 
                                   " to server")
        elif len(self.cache.sync_messages) > 0:
            self.cloud_message_count += 1
            self.cache.logger.info("Sending delayed sync to server")
            sync_msg = self.cache.sync_messages.pop(0)
            self.cache.acknowledge_sync(sync_msg.entry.encoding)
            self.communicator2.send((sync_msg.entry, sync_msg.start_flag,
                                     sync_msg.end_flag), sync_msg.messageType)

    def receive_sensor_message(self):
        ''' Method receive_message
        --------------------------
        Receive messages from sensor
        '''
        ## For debugging check for unique ciphers
        assert(self.cache._unique_ciphers())
        assert(self.cache._ordered())
        ## END DEBUG
        # Unable to reply consistently
        if len(self.rebalance2send) > 0:
            return

        # Receive sensor message
        packet = self.communicator.read()
        if packet is not None:
            self.sensor_message_count += 1

            entry = packet.data[0]
            start_flag = packet.data[1]
            end_flag = packet.data[2]
            send_entry = copy.deepcopy(entry)


            if packet.call_type == 'insert':
                if not self.ongoing_traversal:
                    # Record new traversal
                    self.ongoing_traversal = True
                    self.num_traversals.append([0,0])

                self.miss_count += 1
                self.cache.logger.info("Receiving insert request")
                encoding = entry
                msg = self.cache.insert_request(encoding)
                if msg is None:
                    self.num_traversals[-1][0] += 1
                    self.server_msg2send = OutgoingMessage('insert', 
                                                           send_entry)
                else:
                    self.num_traversals[-1][1] += 1
                    self.sensor_msg2send = msg

            elif packet.call_type == 'rebalance':
                self.ongoing_traversal = False
                self.rebal_count += 1
                self.cache.logger.info('Receiving rebalance request')
                if start_flag:
                    self.cache.logger.info("First in a possible series of " +
                                           "rebalance requests")
                    assert(self.rebalance_received == [] and 
                           self.rebalance_root_enc is None)

                    self.rebalance_root_enc = entry
                if not start_flag:
                    self.rebalance_received.append(entry)
                if end_flag:

                    self.cache.logger.info("Last rebalance request of the " +
                                           "series")
                    self.cache.flush(self.rebalance_received)
                    self.rebalance2send = self.cache.rebalance_start(
                                            self.rebalance_root_enc)
                    del(self.rebalance2send[0]) # Root encoding already sent
                    self.rebalance_received = [] 
                    self.rebalance_root_enc = None
                    if len(self.rebalance2send) > 0:
                        self.cache.logger.info("Sending rebalances from "+ 
                                               "this hierarchy")
                        end_flag = False
                self.server_msg2send = OutgoingMessage(packet.call_type, send_entry,
                                                      start_flag=start_flag,
                                                      end_flag=end_flag)
                
            elif packet.call_type == 'eviction':
                self.ongoing_traversal = False
                self.evict_count += 1
                self.cache.logger('Receiving evicted entry')
                entry = packet.data[0]
                assert(self.cache._entry_with_encoding(entry.encoding) is None)
                self.cache.merge_new([entry])
                if len(self.cache.priority_messages) > 0:
                    self.server_msg2send = self.cache.priority_messages.pop(0)
                    assert(self.cache.priority_messages == [])
                else:
                    # Propogate eviction
                    self.server_msg2send = OutgoingMessage(packet.call_type,
                                                           send_entry)
            elif packet.call_type == 'sync':
                self.ongoing_traversal = False
                self.sync_count += 1
                self.cache.logger.info("Receiving sync message with cipher: " + 
                                        str(packet.data[0].cipher_text))
                entry = packet.data[0]
                assert(self.cache._entry_with_encoding(entry.encoding) is None)
                self.cache.merge_new([entry])
                if len(self.cache.priority_messages) > 0:
                    self.server_msg2send = self.cache.priority_messages.pop(0)
                    assert(self.cache.priority_messages == [])
                self.cache.sync_messages.append(OutgoingMessage('sync',
                                                send_entry))
            else:
                self.cache.logger.error("Packet of call type " + 
                                        packet.call_type + " received")
                                      
                raise ValueError("Unrecognized packet type sent to gateway")

    def receive_server_message(self):
        '''
        Receive message from server
        '''
        ## For debugging check for unique ciphers
        assert(self.cache._unique_ciphers())
        assert(self.cache._ordered())
        ## END DEBUG

        # Receive server message
        packet = self.communicator2.read()
        if packet is None:
            return
        elif packet.call_type != "insert":
            raise ValueError("Higher tiers only send insert Responses")
        else:
            entry = packet.data
            send_entry = copy.deepcopy(entry)
            if (len(self.cache.cache) < self.cache.max_size):
                # If gateway has room, cache value
                self.cache.logger.info("Merging entry:\n " + str(entry))
                self.cache.merge([entry])
            self.sensor_msg2send = OutgoingMessage('insert', send_entry)


class dServer(Tier):
    '''
    Server class in dOPE hierarchy.  Equipped to receive insert, 
    eviction, rebalance and sync messages and to send back insert 
    replies.
    '''
    def __init__(self, out_file):
        super(dServer,self).__init__('Server',Communicator())
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
        assert(self.cache._unique_ciphers())
        assert(self.cache._ordered())
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
            if self.message2send is None:
                raise(ValueError("Server should have record of every cipher"))
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
                self.cache.logger.info("Rebalance cipher: " + 
                                       str(entry.cipher_text))
                entry.synced = True
                self.rebalance_entries.append(entry)
            if end_flag:
                self.cache.logger.info("Last rebalance request with cipher " +
                                       str(entry.cipher_text) )
                self.cache.rebalance_request(self.rebalance_entries, 
                                             self.root_enc)
                self.root_enc = None
                self.rebalance_entries = []
        elif packet.call_type == "evict":
            self.cache.logger.info("Receiving evicted entry")
            entry.synced = True
            self.cache.merge_new([entry])
        elif packet.call_type == "sync":
            self.cache.logger.info("Receiving sync message with cipher: " + 
                                   str(packet.data[0].cipher_text))
            entry.synced = True
            assert(self.cache._entry_with_encoding(entry.encoding) is None)
            self.cache.merge_new([entry])
        else:
            self.cache.logger.error("Packet of call type %s received", 
                                    packet.call_type)
            raise ValueError("Unrecognized packet type sent to server")

