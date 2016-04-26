import copy
import math
import logging

def decrypt(cipher):
    ''' Dummy decryption method
    '''
    return cipher


def encrypt(plaintext):
    ''' Dummy encryption method
    '''
    return plaintext


class OutgoingMessage(object):
    ''' A message to be sent to another level of the caching hierarchy.
    '''
    def __init__(self, messageType, entry, start_flag = False, 
                 end_flag = False):
        self.entry = entry
        self.messageType = messageType
        self.start_flag = start_flag 
        self.end_flag = end_flag

    def __str__(self):
        return ("Message Type" + str(self.messageType) + "\n" 
                + str(self.entryList)
               )

messageType = ["insert", "rebalance", "sync", "evict"]



class CacheEntry(object):
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
        self.logger.setLevel(logging.INFO)
        self.outfile = logfile

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
            self._evict_node()
        self.logger.info("Addingt %d to the cache", entry.cipher_text)
        self.cache.append(entry)
        self.current_size += 1


    def _evict_node(self):
        ''' Method _evict_node
        ----------------------
        Evict all entries from the least recently used node of the cache
        '''
        zero_nodes = [entry for entry in self.cache if entry.node_index == 0]
        sorted_zero_nodes = sorted(zero_nodes, key=lambda x: x.lru)
        node = [entry for entry in self.cache if entry.node_encoding == 
                sorted_zero_nodes[0].node_encoding]
        self.cache = [x for x in self.cache if not x in node]
        for entry in node:
            self.logger.info("Evicting " + str(entry.cipher_text))

            if not entry.synced:
                self.logger.info("Adding eviction to outgoing messages")
                self.priority_messages.append(OutgoingMessage(messageType[3],
                                              copy.deepcopy(entry)))


    def _entry_with_encoding(self, encoding, idx):
        '''
        Return the entry with the provided node encoding and node index
        '''
        node = [entry for entry in self.cache if entry.node_encoding == encoding]
        entry = [entry for entry in node if entry.node_index == idx]
        if entry == []:
            entry = None
        else:
            entry = entry[0]
        return entry


    def rebalance(self, new_entry_encoding):
        ''' Method rebalance
        --------------------
        Check if a rebalance is necessary after adding nodes to the cache.
        If so flush the entire cache and signal to higher tiers to 
        allow a rebalance to occur
        '''
        node = [entry for entry in self.cache if entry.node_encoding ==
                new_entry_encoding]
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
        entries_to_send = [x for x in self.cache if not x.synced]
        outgoing = []
        # Clear cache
        self.cache = []
        self.sync_messages = []
        self.logger.info("Adding rebalance root to outgoing messages.")
        if len(entries_to_send) == 0:
            outgoing.append(OutgoingMessage(messageType[1], 
                                            new_entry_encoding,
                                            start_flag=True,
                                            end_flag=True))
            return outgoing
        outgoing.append(OutgoingMessage(messageType[1], 
                                        new_entry_encoding,
                                        start_flag=True,
                                        end_flag=False))
        for entry in entries_to_send[:len(entries_to_send)-1]:
            self.logger.info("Adding rebalance request to outgoing messages  " +
                             "Ciphertext = " + str(entry.cipher_text))
            outgoing.append(OutgoingMessage(messageType[1],
                                            copy.deepcopy(entry)))
        # Add last message
        self.logger.info("Adding rebalance request to outgoing messages. " + 
                         "Ciphertext = " + str(entries_to_send[-1].cipher_text))
        outgoing.append(OutgoingMessage(messageType[1],
                                        copy.deepcopy(entries_to_send[-1]),
                                        end_flag=True))
        return outgoing


    def _handle_miss(self, next_encoding, plaintext):
        '''Method _handle_miss
        ----------------------
        Request the next entry along the encoding path to complete
        the current insert
        '''
        self.logger.info("Handling cache miss")
        if len(self.cache) == self.max_size:
            self._evict_node()
        self.waiting_on_insert = (True, next_encoding, plaintext)
        self.logger.info("Adding cache miss request to outgoing messages")
        self.priority_messages.append(OutgoingMessage(messageType[0], 
                                      next_encoding[:]))


    def traverse_node(self, current_node_start, new_plaintext):
        ''' Method traverse_node
        -------------------------
        Return the child index to continue the traverse to insert 
        new_plaintext.  Return None if a repeat is found at this node 
        '''
        node_idx = 0
        entry = current_node_start
        while entry is not None and entry.cipher_text < new_plaintext:
            print("we're loopin")
            print(str(entry))
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
        entries = [entry for entry in self.cache if entry.node_encoding == encoding]
        entries = sorted(entries, key = lambda x: x.node_index)
        found = False
        index = 0
        for i, entry in enumerate(entries):
            entry.lru = self.lru_tag
            if not found and entry.cipher_text == new_plaintext:
                self.logger.info("Found duplicate")
                return None
            if not found and entry.cipher_text > new_plaintext:
                index = i
                found = True
            if found:
                entry.node_index += 1
        # Create new entry
        if not found:
            index = len(entries)
        new_entry = CacheEntry(new_plaintext, encoding, index, self.lru_tag)
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
        self.logger.info("Inserting: %d", new_plaintext)

        if self.cache == []:
            if self.current_size == 0:
                self.logger.info("Inserting original root")
                self.cache.append(CacheEntry(new_plaintext, [], 0, self.lru_tag))
                self.lru_tag += 1
                self.current_size += 1
                new_entry = copy.deepcopy(self.cache[0])
                self.sync_messages.append(OutgoingMessage(messageType[2], new_entry))
                return


            else: # Recover from rebalance at root
                self.logger.info("Recovering from rebalance at root")
                self._handle_miss([], new_plaintext)
                return

        new_entry_encoding = []
        if start_enc is not None:
            current_node_start = self._entry_with_encoding(start_enc, 0)
            new_entry_encoding = start_enc[:]
        else:
            current_node_start = self._entry_with_encoding([], 0)
            # TODO handle case where root is evicted or prevent all root evictions

        # Traverse the tree encoded in the cache table
        while not current_node_start.is_leaf:
            # Traverse the current node and find the index of the next insert
            next_child = self.traverse_node(current_node_start, new_plaintext)
            if next_child is None:
                # Repeat!
                self.logger.info("Found duplicate")
                return
            new_entry_encoding.append(next_child)
            current_node_start = self._entry_with_encoding(new_entry_encoding, 0)
            if current_node_start is None:
                self._handle_miss(new_entry_encoding, new_plaintext)
                return
            self.lru_tag += 1

        # Traversed up to a leaf node
        self.logger.info("Traversed up to insert postion of plaintext %d", new_plaintext)
        # Add new entry to the node
        new_entry = self._update_node(new_entry_encoding, new_plaintext)
        self.lru_tag += 1
        if new_entry is None:
            print("NONE")
        new_entry_cp = copy.deepcopy(new_entry)

        # Sync with higher tiers
        self.sync_messages.append(OutgoingMessage(messageType[2], new_entry_cp))

        # If necessary flush cache for rebalance
        self.rebalance(new_entry_encoding)

    def merge(self, incoming_entries):
        self.logger.info("Beginning merge of %d elements",len(incoming_entries))
        new_entries = [entry for entry in incoming_entries if entry 
                       not in self.cache]
        self.cache.extend(new_entries)

    def merge_new(self, incoming_entries):
        ''' Method merge_new
        --------------------
        Filter incoming entries, evict old entries as necessary 
        '''
        self.current_size += len(incoming_entries)
        self.merge(incoming_entries)

        # Handle any evictions
        if not self.max_size is None:
            while len(self.cache) > self.max_size:
                self._evict_node()

    def acknowledge_sync(self, encoding, node_idx):
        ''' Method acknowledge_sync
        ---------------------------
        Flip the sync flag of the matching entry 
        '''
        entry = self._entry_with_encoding(encoding, node_idx)
        self.logger.info("Acknowledging that cipher %d is synced", 
                         entry.cipher_text)
        entry.synced = True

    def insert_request(self, encoding):
        ''' Method insert_request
        -------------------------
        Return the message to be sent back to the requester in order to
        continue the insert at the sensor. 
        '''
        node = [ entry for entry in self.cache if entry.node_encoding == encoding]
        if node == []:
            self.logger.error("encoding: " + str(encoding) + " not found")
            return None
        send = node[:]
        for entry in send:
            entry.synced = True

        self.logger.info("Sending insert reply")
        return OutgoingMessage(messageType[0], send)












