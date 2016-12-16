import copy
import logging
import time
import _pickle as cPickle
from ..utils import print_ctrl

def decrypt(cipher):
    ''' Dummy decryption method
    '''
    return cipher


def encrypt(plaintext):
    ''' Dummy encryption method
    '''
    return plaintext

def enc2string(list):
    return hash(tuple(list))

    # s = ""
    # for elt in list:
    #     s = s + str(elt)

    # return s


class OutgoingMessageB(object):
    ''' A message to be sent to another level of the caching hierarchy.
    '''
    def __init__(self, messageType, entry, start_flag = False, 
                 end_flag = False):
        self.entry = entry
        self.messageType = messageType
        self.start_flag = start_flag 
        self.end_flag = end_flag
        self.timestamp = time.asctime(time.localtime())

    def __str__(self):
        return ("Message Type" + str(self.messageTypeB) + "\n" 
                + str(self.entryList)
               )

messageTypeB = ["insert", "rebalance", "sync", "evict", "sync_repeat"]



class CacheEntryB(object):
    ''' One entry in a cache table, keeps track of ciphertext, encoding,
        lru tag, subtree size, and leaf status
    '''
    def __init__(self, ciphertext_data, node_encoding, node_index, lru_tag):
        self.cipher_text = ciphertext_data
        self.node_encoding = node_encoding
        self.node_index = node_index
        self.is_leaf = True
        self.lru = lru_tag
        self.synced = False

    def __str__(self):
        selfstr =  ("-------------------------\nCiphertext:" + 
                    str(self.cipher_text) + "\nEncoding:" + 
                    str(self.node_encoding) + "\nNode Index:" + 
                    str(self.node_index) + "\n"
        )
        if self.is_leaf:
            selfstr += "LEAF\n"
        if self.synced:
            selfstr += "SYNCED\n"
        selfstr += "----------------------------\n"
        return selfstr


    def __deepcopy__(self, _memo):
        try:
            return cPickle.loads(cPickle.dumps(self, -1))
        except PicklingError:
            return copy.deepcopy(self)

    def __lt__(self, other):
        my_node_enc = str(self.node_encoding)
        my_total_enc = my_node_enc + ":" + str(self.node_index)
        other_node_enc = str(other.node_encoding)
        other_total_enc = other_node_enc + ":" + str(other.node_index)
        return my_total_enc < other_total_enc




class CacheModel(object):
    """ A representation of a dOPE cache.  Includes the list of 
        cache entries, a global lru tag, queues for outgoing 
        messages and factors necessary for rebalancing.

        Supports an insert operation that triggers data syncing,
        rebalancing of the implied tree structure, and cache 
        misses that query the next level of the hierarchy
    """

    def __init__(self, table_size=None, logfile=None, t=5):
        self.t = t
        self.max_size = table_size
        self.current_size = 0
        self.cache = []
        self.cache_lookup = {}
        self.lru_tag = 0
        self.priority_messages = [] # queue for rebalance eviction
                                    # and cache miss events
        self.sync_messages = [] # queue for syncing data between 
                                # the sensor and gateway
        # waiting_on_insert = status, index, plaintext
        self.waiting_on_insert = (False, None, None) 
        self.logger = logging.getLogger(logfile)
        fh = logging.FileHandler(logfile)
        self.logger.addHandler(fh)
        self.logger.setLevel(logging.DEBUG)
        self.outfile = logfile

        self.evict_count = 0
        self.plaintexts_who_miss = []
        self.insert_count = 0
        self.rebal_count = 0

    def __str__(self):
        sizes = ("Max Size: " + str(self.max_size) + "\nCurrent Size: " +
                 str(self.current_size) + "\n"
        )
        priority_messages = ("Outgoing Messages: " + 
                                 str(self.priority_messages) + "\n"
        )
        sync_messages = ("Sync Messages: " +
                         str(self.sync_messages) +"\n")
        out_string = sizes + priority_messages + sync_messages
        for x in self.cache:
            out_string += str(x)
        return out_string

    def _cachetable_add(self, entry):
        ''' Method _cachetable_add
        --------------------------
        Add a new entry to the table, evicting a node if necessary
        '''
        if self.max_size is not None and len(self.cache) == self.max_size:
            self.logger.debug("eviction triggered")
            self._evict_node()
        self.logger.debug("Adding %d to the cache", entry.cipher_text)
        self.cache_lookup[enc2string(entry.node_encoding)][entry.node_index] = entry
        self.cache.append(entry)
        self.current_size += 1

    def _evict_node(self):
        ''' Method _evict_node
        ----------------------
        Evict all entries from the least recently used node of the cache
        '''
        self.evict_count += 1
        zero_nodes = [entry for entry in self.cache if entry.node_index == 0]
        self.logger.debug("Zero nodes " + str(zero_nodes))
        sorted_zero_nodes = sorted(zero_nodes, key=lambda x: x.lru)
        if sorted_zero_nodes[0].node_encoding == []:
            sorted_zero_nodes.pop(0)
        #node = [entry for entry in self.cache if entry.node_encoding == 
        #        sorted_zero_nodes[0].node_encoding]
        node = self.cache_lookup[enc2string(sorted_zero_nodes[0].node_encoding)].values()
        #assert(sorted(node) == sorted(NODE))
        del self.cache_lookup[enc2string(sorted_zero_nodes[0].node_encoding)]
        self.cache = [x for x in self.cache if not x in node] # This can be sped up
        for entry in node:
            self.logger.debug("Evicting " + str(entry.cipher_text))
            if not entry.synced:
                self.logger.debug("Adding eviction to outgoing messages")
                self.priority_messages.append(OutgoingMessageB(messageTypeB[3],
                                              copy.deepcopy(entry)))


    def _entry_with_encoding(self, encoding, idx):
        '''
        Return the entry with the provided node encoding and node index
        '''
        #node = [entry for entry in self.cache if entry.node_encoding == encoding]
        #entry = [entry for entry in node if entry.node_index == idx]
        try:
            node = self.cache_lookup[enc2string(encoding)].values()
            entry = [] if idx not in self.cache_lookup[enc2string(encoding)] else [self.cache_lookup[enc2string(encoding)][idx]]
        except:
            node = []
            entry = []
        
        #assert(sorted(node) == sorted(NODE))
        #assert(entry == ENTRY)

        if entry == []:
            entry = None
        else:
            if len(entry) != 1:
                self.logger.debug(str(self))
                assert(len(entry) == 1)
            entry = entry[0]
        return entry


    def rebalance(self, new_entry_encoding):
        ''' Method rebalance
        --------------------
        Check if a rebalance is necessary after adding nodes to the cache.
        If so flush the entire cache and signal to higher tiers to 
        allow a rebalance to occur
        '''
        #node = [entry for entry in self.cache if entry.node_encoding ==
        #        new_entry_encoding]
        node = self.cache_lookup[enc2string(new_entry_encoding)].values()
        #assert(sorted(NODE) == sorted(node))
        if len(node) >= 2* self.t - 1:
            self.priority_messages += self.rebalance_flush(new_entry_encoding)
            return True
        else:
            return False

    def rebalance_flush(self, new_entry_encoding):
        ''' Method flush
        ----------------
        Flush the entire cache due to a rebalance.  Return any unsynced entries
        to synchronize with higher tiers
        '''
        self.rebal_count += 1
        entries_to_send = [x for x in self.cache if not x.synced]
        outgoing = []
        # Clear cache
        self.cache = []
        self.cache_lookup = {}
        self.sync_messages = []
        #self.logger.debug("Adding rebalance root to outgoing messages.")
        if len(entries_to_send) == 0:
            outgoing.append(OutgoingMessageB(messageTypeB[1], 
                                            new_entry_encoding,
                                            start_flag=True,
                                            end_flag=True))
            return outgoing
        outgoing.append(OutgoingMessageB(messageTypeB[1], 
                                        new_entry_encoding,
                                        start_flag=True,
                                        end_flag=False))
        for entry in entries_to_send[:len(entries_to_send)-1]:
            #self.logger.debug("Adding rebalance request to outgoing messages  " +
            #                 "Ciphertext = " + str(entry.cipher_text))
            outgoing.append(OutgoingMessageB(messageTypeB[1],
                                            copy.deepcopy(entry)))
        # Add last message
        #self.logger.debug("Adding rebalance request to outgoing messages. " + 
        #                 "Ciphertext = " + str(entries_to_send[-1].cipher_text))
        outgoing.append(OutgoingMessageB(messageTypeB[1],
                                        copy.deepcopy(entries_to_send[-1]),
                                        end_flag=True))
        return outgoing


    def _handle_miss(self, next_encoding, plaintext):
        '''Method _handle_miss
        ----------------------
        Request the next entry along the encoding path to complete
        the current insert
        '''
        self.plaintexts_who_miss.append(plaintext)
        #self.logger.debug("Handling cache miss")
        if len(self.cache) == self.max_size:
            self._evict_node()
        self.waiting_on_insert = (True, next_encoding, plaintext)
        #self.logger.debug("Adding cache miss request to outgoing messages")
        self.priority_messages.append(OutgoingMessageB(messageTypeB[0], 
                                      next_encoding[:]))


    def traverse_node(self, current_node_start, new_plaintext):
        ''' Method traverse_node
        -------------------------
        Return the child index to continue the traverse to insert 
        new_plaintext.  Return None if a repeat is found at this node 
        '''
        node_idx = 0
        entry = current_node_start
        #self.logger.debug(entry.cipher_text)
        #self.logger.debug("plaintext: " + str(new_plaintext))
        while entry is not None and entry.cipher_text < new_plaintext:
            #self.logger.debug(entry.cipher_text)
            entry.lru = self.lru_tag
            node_idx += 1
            entry = self._entry_with_encoding(current_node_start.node_encoding,
                                              node_idx)

        # Repeat
        if entry is not None and entry.cipher_text == new_plaintext:
            return None

        return node_idx

    def _update_node(self, encoding, new_plaintext):
        ''' Method update_node
        ----------------------
        Insert new_plaintext into the leaf node pointed to by
        encoding.  In general the node index of other entries
        will be shifted by the new arrival.
        '''
        #entries = [entry for entry in self.cache if entry.node_encoding == encoding]
        #entries = sorted(entries, key = lambda x: x.node_index)
        entries = sorted(self.cache_lookup[enc2string(encoding)].values())
        #assert(entries == ENTRIES)
        #self.logger.debug(entries)
        found = False
        index = 0
        for i, entry in enumerate(entries):
            entry.lru = self.lru_tag
            #self.logger.debug(str(entry.cipher_text))
            if not found and entry.cipher_text == new_plaintext:
                #self.logger.debug("Found duplicate")
                return None
            if not found and entry.cipher_text > new_plaintext:
                index = i
                found = True
            if found:
                entry.node_index += 1
                self.cache_lookup[enc2string(encoding)][entry.node_index] = entry

        # Create new entry
        if not found:
            index = len(entries)
            #self.logger.debug(index)
        new_entry = CacheEntryB(new_plaintext, encoding, index, self.lru_tag)
        self._cachetable_add(new_entry)
        return new_entry


    def insert(self, new_plaintext, start_enc=None):
        ''' Method insert
        -----------------
        Used for both fresh inserts and picking up on inserts after
        cache misses.  Either terminates with an updated cache table
        with the new entry inserted, a new outgoing message requesting
        the region of the encoding tree necessary to continue the
        the insert, or no change in the case a duplicate is found
        '''
        #self.logger.debug("Inserting: %f", new_plaintext)
        assert(len(self.cache) <= self.max_size)

        if self.cache == []:
            self.insert_count += 1
            if self.current_size == 0:
                #self.logger.debug("Inserting original root")
                entry = CacheEntryB(new_plaintext, [], 0, self.lru_tag)
                self.cache.append(entry)
                self.cache_lookup[enc2string([])] = {}
                self.cache_lookup[enc2string([])][0] = entry
                self.lru_tag += 1
                self.current_size += 1
                new_entry = copy.deepcopy(self.cache[0])
                self.sync_messages.append(OutgoingMessageB(messageTypeB[2], new_entry))
                return

            else: # Recover from rebalance at root
                #self.logger.debug("Recovering from rebalance at root")
                self._handle_miss([], new_plaintext)
                return

        new_entry_encoding = []
        if start_enc is not None:
            current_node_start = self._entry_with_encoding(start_enc, 0)
            new_entry_encoding = start_enc[:]
        else:
            self.insert_count += 1
            current_node_start = self._entry_with_encoding([], 0)

        # Traverse the tree encoded in the cache table
        if current_node_start is None:
            print("\nThis is the cache state upon error")
            print(self)
            raise("Start node not in the cache")

        while not current_node_start.is_leaf:
            # Traverse the current node and find the index of the next insert
            next_child = self.traverse_node(current_node_start, new_plaintext)
            if next_child is None:
                # Repeat!
                self.sync_messages.append(OutgoingMessageB(messageTypeB[4], new_entry_encoding))
                #self.logger.debug("Found duplicate")
                return
            new_entry_encoding.append(next_child)
            #self.logger.debug("New entry encoding: " + str(new_entry_encoding))
            current_node_start = self._entry_with_encoding(new_entry_encoding, 0)
            if current_node_start is None:
                self._handle_miss(new_entry_encoding, new_plaintext)
                return
            self.lru_tag += 1

        # Traversed up to a leaf node
        #self.logger.debug("Traversed up to insert postion of plaintext %d", new_plaintext)
        # Add new entry to the node
        new_entry = self._update_node(new_entry_encoding, new_plaintext)
        self.lru_tag += 1
        if new_entry is None:
            # Repeat!
            self.sync_messages.append(OutgoingMessageB(messageTypeB[4], new_entry_encoding))
            return
        new_entry_cp = copy.deepcopy(new_entry)

        # Sync with higher tiers
        self.sync_messages.append(OutgoingMessageB(messageTypeB[2], new_entry_cp))

        # If necessary flush cache for rebalance
        self.rebalance(new_entry_encoding)

    def merge(self, incoming_entries):
        #self.logger.debug("Beginning merge of %d elements",len(incoming_entries))
        #new_entries = [entry for entry in incoming_entries if entry 
        #               not in self.cache]
        new_entries = [entry for entry in incoming_entries if enc2string(entry.node_encoding)
                       not in self.cache_lookup]
        #assert(sorted(new_entries) == sorted(NEW_ENTRIES))
        for entry in new_entries:
            entry.lru = self.lru_tag
            if enc2string(entry.node_encoding) not in self.cache_lookup:
                self.cache_lookup[enc2string(entry.node_encoding)] = {}
            self.cache_lookup[enc2string(entry.node_encoding)][entry.node_index] = entry
        self.lru_tag += 1
        self.cache.extend(new_entries)
        if not self.max_size is None:
            while len(self.cache) >= self.max_size:
                self._evict_node()

    def merge_new(self, incoming_entries):
        ''' Method merge_new
        --------------------
        Filter incoming entries, evict old entries as necessary 
        '''
        #self.logger.debug("merging new\n\n\n\n")
        self.current_size += len(incoming_entries)
        for new in incoming_entries:
            # Find the node to which this entry belongs
            node = [entry for entry in self.cache if entry.node_encoding == 
                    new.node_encoding ]
            try:
                NODE = self.cache_lookup[enc2string(new.node_encoding)].values()
            except KeyError:
                NODE = []
                self.cache_lookup[enc2string(new.node_encoding)] = {}
            assert(sorted(node)==sorted(NODE))
            #self.logger.debug(node)
            #for entry in node:
            #    self.logger.debug(str(entry))
            # Update the other entries at this node
            for entry in node:
                #self.logger.debug(str(entry))
                if entry.node_index >= new.node_index:
                    entry.node_index += 1
                    self.cache_lookup[enc2string(new.node_encoding)][entry.node_index] = entry
                #self.logger.debug(str(entry))
            self.cache_lookup[enc2string(new.node_encoding)][new.node_index] = new
            self.cache.append(new)

        # Handle any evictions
        if not self.max_size is None:
            while len(self.cache) >= self.max_size:
                self._evict_node()

    def acknowledge_sync(self, encoding, node_idx):
        ''' Method acknowledge_sync
        ---------------------------
        Flip the sync flag of the matching entry 
        '''
        entry = self._entry_with_encoding(encoding, node_idx)
        #self.logger.debug("Acknowledging that cipher %d is synced", 
        #                 entry.cipher_text)
        entry.synced = True

    def insert_request(self, encoding):
        ''' Method insert_request
        -------------------------
        Return the message to be sent back to the requester in order to
        continue the insert at the sensor. 
        '''
        #node = [ entry for entry in self.cache if entry.node_encoding == encoding]
        try:
            node = list(self.cache_lookup[enc2string(encoding)].values())[:]
        except KeyError:
            node = []
        #assert(sorted(node) == sorted(NODE))
        if node == []:
            self.logger.error("encoding: " + str(encoding) + " not found")
            return None
        # send = []
        # for entry in node:
        #     new_entry = CacheEntryB(entry.cipher_text, entry.node_encoding[:],
        #             entry.node_index, entry.lru)
        #     new_entry.synced = True
        #     new_entry.is_leaf = entry.is_leaf
        #     send.append(new_entry)

        send = copy.deepcopy(node)
        for entry in send:
            assert(entry not in node)
            entry.synced = True

        #self.logger.debug("Sending insert reply")
        return OutgoingMessageB(messageTypeB[0], send)


#    def __init__(self, ciphertext_data, node_encoding, node_index, lru_tag):










