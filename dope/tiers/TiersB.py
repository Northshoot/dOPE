import queue
import copy
from ..comm import Communicator
from .DataGenerator import DataGenerator
from ..datastruct import BTree
from ..cache import CacheModelB as cache
from ..cache import OutgoingMessage, messageType, CacheEntry
from ..utils import print_ctrl

__author__ = 'WDaviau'

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
    def __init__(self, data_queue_len, distribution, cache_len, out_file, k, data_file):
        super(dSensor,self).__init__('Sensor',Communicator())
        self.data_gen = DataGenerator(distribution, bounds = [-1000,1000],
                                      data_file = data_file)
        self.num_data_sent = 0
        self.num_gen = 0
        self.comp_req_queue = queue.Queue(1)
        self.data_queue = queue.Queue(data_queue_len)
        self.insert_round_trips = []
        self.cache = cache.CacheModel(cache_len, out_file, int(k/2))
        self.done = False
        # For recording more precise dope statistics
        self.total_ciphers_sent = 0
        self.total_ciphers_received = 0
        self.send_message_count = 0
        self.sim_lim = None

    @property
    def sim_lim_reached(self):
        if self.sim_lim is None:
            return False
        else:
            return self.send_message_count == self.sim_lim

    def generate_data(self):
        ''' Method generate_data
        ------------------------
        Take the next data point from the data model set at init.
        Either insert, pipe data through the queue or drop
        '''
        # Enqueue data for low priority sending 
        self.num_gen += 1
        plaintxt = self.data_gen.get_next()
        if plaintxt is None or self.sim_lim_reached:
            self.done = True
            return
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
            self.cache.logger.debug("Insert blocking.  Number priority " +
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
        self.send_message_count += 1
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
            self.cache.acknowledge_sync(message2send.entry.node_encoding, 
                                        message2send.entry.node_index)
            self.communicator.send((message2send.entry, False, False),
                                   message2send.messageType)

    def receive_message(self):
        ''' Method receive_message
        --------------------------
        If a message was sent to the sensor process and change state
        accordingly
        '''
        packet = self.communicator.read()
        if packet is None:
            return
        elif packet.call_type != "insert":
            raise ValueError("Higher tiers only send insert Responses")
        else:
            # continue inserted where we left off
            waiting, encoding, plaintxt = self.cache.waiting_on_insert
            assert(waiting)
            node = packet.data[0]
            self.total_ciphers_received += len(node)
            for entry in node:
                entry.lru = self.cache.lru_tag
            self.cache.lru_tag += 1
            self.cache.logger.debug("Merging entries:\n " + str(node))
            self.cache.merge(node)
            self.cache.waiting_on_insert = False, None, None
            self.cache.insert(plaintxt, encoding)


class dGateway(Tier):
    '''
    Gateway calss in dOPE heirarchy.  Intermediary between Sensor and
    Server.  Forwards sync messages, propogates evictions when cache is
    full, pushes rebalance messages through to server and flushes 
    cache, responds to insert messages querying server if necessary
    '''
    def __init__(self, out_file, cache_len = 1000, k=5):
        super(dGateway,self).__init__('Gateway', Communicator(), Communicator())
        self.rebalance_received = []
        self.rebalance2send = []
        self.rebalance_root_enc = None
        self.sensor_msg2send = None
        self.server_msg2send = None
        self.cache = cache.CacheModel(cache_len, out_file, int(k/2))
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
            self.cache.logger.debug("Sending message to server")
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
            self.cache.logger.debug("Sending rebalance request with cipher: " +
                                   str(rebalance_msg.entry.cipher_text) + 
                                   " to server")
        elif len(self.cache.sync_messages) > 0:
            self.cloud_message_count += 1
            self.cache.logger.debug("Sending delayed sync to server")
            sync_msg = self.cache.sync_messages.pop(0)
            self.cache.acknowledge_sync(sync_msg.entry.node_encoding, sync_msg.entry.node_index)
            self.communicator2.send((sync_msg.entry, sync_msg.start_flag,
                                     sync_msg.end_flag), sync_msg.messageType)

    def receive_sensor_message(self):
        ''' Method receive_message
        --------------------------
        Receive messages from sensor
        '''
        self.cache.logger.debug("Beginning receive message \n\n")
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
                self.cache.logger.debug("Receiving miss request for encoding: " + str(entry))
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
                self.cache.logger.debug('Receiving rebalance request')
                if start_flag:
                    self.cache.logger.debug("First in a possible series of " +
                                           "rebalance requests")
                    assert(self.rebalance_received == [] and 
                           self.rebalance_root_enc is None)

                    self.rebalance_root_enc = entry
                if not start_flag:
                    self.rebalance_received.append(entry)
                if end_flag:

                    self.cache.logger.debug("Last rebalance request of the " +
                                           "series")
                    self.rebalance2send = self.cache.rebalance_flush(self.rebalance_root_enc)

                    del(self.rebalance2send[0]) # Root encoding already sent
                    self.rebalance_received = [] 
                    self.rebalance_root_enc = None
                    if len(self.rebalance2send) > 0:
                        self.cache.logger.debug("Sending rebalances from "+ 
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
                assert(self.cache._entry_with_encoding(entry.node_encoding, entry.node_index) is None)
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
                self.cache.logger.debug("Receiving sync message with cipher: " + 
                                        str(packet.data[0].cipher_text))
                entry = packet.data[0]
                self.cache.logger.debug("Pre merge")
                self.cache.logger.debug(str(self.cache))
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
        self.cache.logger.debug("Beginning receive server message \n\n")
        self.cache.logger.debug(str(self.cache))
        # Receive server message
        packet = self.communicator2.read()
        if packet is None:
            return
        elif packet.call_type != "insert":
            raise ValueError("Higher tiers only send insert Responses")
        else:
            node = packet.data
            send_entry = copy.deepcopy(node)
            if (len(self.cache.cache) < self.cache.max_size):
                # If gateway has room, cache value
                self.cache.logger.debug("Merging entry:\n " + str(node))
                self.cache.merge(node)
            self.sensor_msg2send = OutgoingMessage('insert', send_entry)
        self.cache.logger.debug("Ending receive server message \n\n")
        self.cache.logger.debug(str(self.cache))


class dServer(Tier):
    '''
    Server class in dOPE hierarchy.  Equipped to receive insert, 
    eviction, rebalance and sync messages and to send back insert 
    replies.
    '''
    def __init__(self, out_file, k):
        super(dServer,self).__init__('Server',Communicator())
        self.rebalance_entries = []
        self.root_enc = None
        self.message2send = None
        self.cache = cache.CacheModel(None, out_file)
        self.tree = BTree(k)

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

    def handle_insert(self, encoding):
        '''Method handle_insert
        -----------------------
        Respond to a missing cache entry at the sensor
        '''
        node = self.tree.node_at_enc(encoding)
        if node is None:
            raise(ValueError("Server should have record of every cipher"))
        entries2send = [CacheEntry(key, encoding, i, 0) for i,key in 
                        enumerate(node.keys)]
        for entry in entries2send:
            self.cache.logger.debug(str(entry))
            entry.is_leaf = node.isLeaf
            entry.synced = True

        self.message2send = OutgoingMessage(messageType[0], entries2send)

    def handle_rebalance(self, entry, start_flag, end_flag):
        '''
        Process rebalance messages to eventually
        trigger a rebalance in the encoding tree
        '''
        if start_flag:
            self.cache.logger.debug("First in a possible series of " +
                                       "rebalance requests")
            if self.rebalance_entries != [] or self.root_enc is not None:
                self.cache.logger.debug("Rebalance Entries: " + 
                                       str(self.rebalance_entries))
            assert(self.rebalance_entries == [] and self.root_enc is None)
            # Initial rebalance entry is the root encoding
            self.root_enc = entry
            self.cache.logger.debug("Rebalance encoding" + str(self.root_enc))
        if not start_flag:
            self.cache.logger.debug("Rebalance cipher: " + 
                                   str(entry.cipher_text))
            entry.synced = True
            self.rebalance_entries.append(entry)
        if end_flag:
            self.cache.logger.debug("Last rebalance request with cipher " +
                                   str(entry.cipher_text) )
            # Insert rebalance entries and trigger a split child at root enc
            for entry in self.rebalance_entries:
                self.tree.insert_direct(entry.cipher_text, entry.node_encoding,
                                        entry.node_index)
            self.tree.trigger_rebalance(self.root_enc)
            self.root_enc = None
            self.rebalance_entries = []



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
            self.cache.logger.debug("Receiving miss request")
            encoding = entry
            self.handle_insert(encoding)
            self.cache.logger.debug(str(self.tree))
            
        elif packet.call_type == "rebalance":
            self.cache.logger.debug("Receiving rebalance request")
            self.handle_rebalance(entry, start_flag, end_flag)
            self.cache.logger.debug(str(self.tree))

            
        elif packet.call_type == "evict":
            self.cache.logger.debug("Receiving evicted entry")
            entry.synced = True
            # Do an insert into the B tree
            self.tree.insert_direct(entry.cipher_text, entry.node_encoding,
                                    entry.node_index)
        elif packet.call_type == "sync":
            self.cache.logger.debug("Receiving sync message with cipher: " + 
                                   str(packet.data[0].cipher_text))
            entry.synced = True
            # Do an insert into the B tree
            self.tree.insert_direct(entry.cipher_text, entry.node_encoding,
                                    entry.node_index)
            self.cache.logger.debug(str(self.tree))

        else:
            self.cache.logger.error("Packet of call type %s received", 
                                    packet.call_type)
            raise ValueError("Unrecognized packet type sent to server")

