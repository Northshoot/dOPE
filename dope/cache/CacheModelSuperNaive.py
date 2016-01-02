import copy
import math
import logging

from  datastruct.scapegoat_tree import SGTree, enc_insert



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


def encoding_cmp(enc1, enc2):
    ''' Comapare two encoding lists of 1s and 0s.  Preceding 0s make 
        encodings comparitively lower than preceding 1s
    '''
    if enc1 == []:
        if enc2 == []:
            return 0
        elif enc2[0] == 0:
            return 1
        else:
            return -1
    if enc2 == []:
        if enc1 == []:
            return 0
        elif enc1[0] == 0:
            return -1
        else:
            return 1

    if enc1[0] == enc2[0]:
        if len(enc1) == 1 and len(enc2) == 1:
            return 0
        elif len(enc1) == 1:
            if enc2[1] == 1:
                return -1
            else:
                return 1
        elif len(enc2) == 1:
            if enc1[1] == 1:
                return 1
            else:
                return -1
        else:
            return encoding_cmp(enc1[1:], enc2[1:])

    assert(enc1[0] != enc2[0])
    if enc1[0] == 0:
        return -1
    else:
        return 1

class CacheEntry(object):
    ''' One entry in a cache table, keeps track of ciphertext, encoding,
        lru tag, subtree size, and leaf status
    '''
    def __init__(self, ciphertext_data, encoding, lru_tag):
        self.cipher_text = ciphertext_data
        self.encoding = encoding
        self.subtree_size = 1
        self.is_leaf = True
        self.has_left_child = False
        self.has_right_child = False
        self.lru = lru_tag
        self.synced = False

    def __str__(self):
        selfstr =  ("-------------------------\nCiphertext:" + 
                    str(self.cipher_text) + "\nEncoding:" + 
                    str(self.encoding) + "\nSubtree Size:" + 
                    str(self.subtree_size) + "\n"
        )
        if self.is_leaf:
            selfstr += "LEAF\n"
        elif self.has_left_child != self.has_right_child:
            selfstr += "ONE CHILD\n"
        else:
            selfstr += "TWO CHILDREN\n"
        if self.synced:
            selfstr += "SYNCED\n"
        selfstr += "----------------------------\n"
        return selfstr

    def __lt__(self, other):
        return encoding_cmp(self.encoding, other.encoding) < 0

    def __gt__(self, other):
        return encdoing_cmp(self.encoding, other.encoding) < 0

    def __eq__(self, other):
        return encoding_cmp(self.encoding, other.encoding) == 0

    def __le__(self, other):
        return encoding_cmp(self.encoding, other.encoding) <= 0

    def __ge__(self, other):
        return encoding_cmp(self.encoding, other.encoding) >= 0

    def __ne__(self, other):
        return encoding_cmp(self.encoding, other.encoding) != 0


class CacheModel(object):
    """ A representation of a dOPE cache.  Includes the list of 
        cache entries, a global lru tag, queues for outgoing 
        messages and factors necessary for rebalancing.

        Supports an insert operation that triggers data syncing,
        rebalancing of the implied tree structure, and cache 
        misses that query the next level of the hierarchy
    """

    def __init__(self, table_size=None, logfile=None):
        self.max_size = table_size
        self.current_size = 0
        self.cache = []
        self.lru_tag = 0
        self.priority_messages = [] # queue for rebalance eviction
                                    # and cache miss events
        self.sync_messages = [] # queue for syncing data between 
                                # the sensor and gateway
        self.sg_alpha = 0.5
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
        out_string = sizes + priority_messages
        for x in self.cache:
            out_string += str(x)
        return out_string

    def _index_of_encoding(self, encoding):
        ''' Internal Method index_of_encoding
        -------------------------------------
        Return the index of the provided encoding in the cache table
        '''
        for i,v in enumerate(self.cache):
            if v.encoding == encoding:
                return i
        return None

    def _enc_copy(self, list_to_copy):
        ''' Internal Method _enc_copy
        -----------------------------
            Make an encoding copy.  Uses python built-in [:] operator
        '''
        return list_to_copy[:]

    def _left_child(self, index):
        '''Internal Method left_child
        -----------------------------
        Return the index of the left child of the entry at index.  If 
        no such child exists return None
        '''
        encoding = self._enc_copy(self.cache[index].encoding)
        encoding.append(0)
        return self._index_of_encoding(encoding)

    def _right_child(self, index):
        '''Internal Method right_child
        -----------------------------
        Return the index of the right child of the entry at index. If 
        no such child exists return None
        '''
        encoding = self._enc_copy(self.cache[index].encoding)
        encoding.append(1)
        return self._index_of_encoding(encoding)

    def _update_parent_sizes(self, encoding):
        ''' Method update_parent_sizes
        ------------------------------
        Go through all entries affected by adding entry with the
        provided encoding and update subtree size fields
        '''
        self.logger.info("Updating parent sizes")
        level = 0
        while (level < len(encoding)):
            next_index = self._index_of_encoding(encoding[:level])
            if next_index is not None:
                self.cache[next_index].subtree_size += 1
            level += 1

    def _evict(self, num_evictions):
        ''' Internal Method evict
        -------------------------
        Remove the num_eviction least recently used entries in the 
        cache and send a message to the next space in the hierarchy
        '''
        sorted_entries = sorted(self.cache, key=lambda x: x.lru)
        lru_entries = sorted_entries[:num_evictions]
        self.cache = [x for x in self.cache if not x in lru_entries]
        self.cache.sort()
        for entry in lru_entries:
            if not entry.synced:
                self.logger.info("Adding eviction to outgoing messages")
                self.priority_messages.append(OutgoingMessage(messageType[3], 
                                              copy.deepcopy(entry)))

    def _handle_miss(self, subtree_root, next_encoding, plaintext):
        '''Internal Method handle_miss
        ------------------------------
        Bring in the next entry along the encoding path to complete the
        current insert.
        '''
        self.logger.info("Handling cache miss")
        if len(self.cache) == self.max_size:
            self._evict(1)
        self.waiting_on_insert = (True, subtree_root, plaintext)
        self.logger.info("Adding insert request to outgoing messages")
        self.priority_messages.append(OutgoingMessage(messageType[0],
                                      self._enc_copy(next_encoding)))

    def _cachetable_add(self, new_ciphertext, new_entry_encoding):
        ''' Internal Method cachetable_add
        ----------------------------------
        Add the ciphertext to the cache in an entry with the provided 
        encoding
        '''
        assert(self._index_of_encoding(new_entry_encoding) is None)
        self.logger.info("Adding %d to the cache", new_ciphertext)
        self.cache.append(CacheEntry(new_ciphertext, new_entry_encoding,
                                     self.lru_tag))
        self.cache.sort()
        self.lru_tag += 1
        self.current_size += 1

    def _clear_syncs(self, index):
        ''' Internal Method clear_syncs
        -------------------------------
        Remove sync messages that will be made obsolete by a rebalance at 
        the provided index.
        '''
        root_encoding = self.cache[index].encoding
        bad_entries = []
        for msg in self.sync_messages:
            entry = msg.entry
            if entry.encoding[:len(root_encoding)] == root_encoding:
                bad_entries.append(entry)
                self.logger.info("Clearing sync with cipher %d from " +
                                 "outgoing syncs", entry.cipher_text)
        self.sync_messages = [msg for msg in self.sync_messages if
                              not msg.entry in bad_entries]

    def _rebalance_request(self, index):
        ''' Internal Method purge_subtree
        ---------------------------------
        Called during a sensor rebalance to evict the subtree rooted
        at the provided index to prepare for a nonlocal rebalance.
        '''
        root_entry = copy.deepcopy(self.cache[index])
        start_encoding = root_entry.encoding
        subtree_to_evict = [x for x in self.cache if 
                            x.encoding[:len(start_encoding)] == start_encoding]
        subtree_to_evict = sorted(subtree_to_evict, key=lambda x: len(x.encoding))
        self.cache = [x for x in self.cache if not x in subtree_to_evict]
        entries_to_send = [x for x in subtree_to_evict if not x.synced]
        self.logger.info("Adding rebalance root to outgoing messages.")
        if len(entries_to_send) == 0:
            self.priority_messages.append(OutgoingMessage(messageType[1], 
                                          root_entry.encoding, 
                                          start_flag=True,
                                          end_flag=True))
            return
        self.priority_messages.append(OutgoingMessage(messageType[1], 
                                      root_entry.encoding, start_flag=True))
        for entry in entries_to_send[:len(entries_to_send)-1]:
            self.logger.info("Adding rebalance request to outgoing messages  " +
                             "Ciphertext = %d", entry.cipher_text)
            self.priority_messages.append(OutgoingMessage(messageType[1],
                                          copy.deepcopy(entry)))
        self.priority_messages.append(OutgoingMessage(messageType[1], 
                                      copy.deepcopy(entries_to_send[-1]),
                                      end_flag=True))
        self.logger.info("Adding rebalance request to outgoing messages " + 
                         "Ciphertext = %d", entries_to_send[-1].cipher_text)

    def _balanced_h(self):
        '''Internal Method balanced_h 
        -----------------------------
        Return the largest height the scapegoat tree represented by the
        cache considers balanced
        '''
        return math.floor(math.log(self.current_size, (1/self.sg_alpha)))

    def _is_scapegoat_node(self,index):
        '''Internal Method is_scapegoate_node 
        -------------------------------------
        Return true if the node at this index is unbalanced enough to 
        be the scapegoate in a rebalance
        '''
        left_child_idx = self._left_child(index)
        right_child_idx = self._right_child(index)
        if left_child_idx is not None:
            if (self.cache[left_child_idx].subtree_size > 
                self.cache[index].subtree_size * self.sg_alpha):
                return True
        if right_child_idx is not None:
            if (self.cache[right_child_idx].subtree_size > 
                self.cache[index].subtree_size * self.sg_alpha):
                return True
        return False

    def _filter_cache_occupancy(self, entry):
        ''' Internal Method filter_cache_occupancy 
        ------------------------------------------
        Returns false if an entry with the same encoding exists in the
        cache
        '''
        for y in self.cache:
            if y.encoding == entry.encoding:
                return False
        return True

    def _unique_ciphers(self):
        ''' Internal Method _unique_ciphers
        -----------------------------------
        Returns true if all ciphertexts in the cache are unique
        '''
        for entry in self.cache:
            same_ciphers = filter()

        return True
    def acknowledge_sync(self, entry):
        ''' Method acknowledge_sync
        ---------------------------
        Flip the sync flag of the matching entry 
        '''
        index = self._index_of_encoding(entry.encoding)
        if self.cache[index].cipher_text != entry.cipher_text:
            self.logger.error("Non-matching ciphertext while acking sync")
        self.logger.info("Acknowledging that cipher %d is synced", 
                         self.cache[index].cipher_text)
        self.cache[index].synced = True

    def merge(self, incoming_entries):
        ''' Method merge
        ----------------
        Merge new entries into the existing cache.  
        '''
        self.logger.info("Beginning merge of %d elements",len(incoming_entries))
        new_entries = list(filter(self._filter_cache_occupancy, 
                                  incoming_entries))
        self.cache.extend(incoming_entries)
        self.cache.sort()

    def rebalance(self, encoding):
        ''' Method rebalance
        --------------------
        Check if the tree implied by the cache is unbalanced.  If so
        traverse up the path of the newly inserted value causing the
        imbalance, and find a scapegoat node.  Flush the cache of the
        the subtree below this node sending non synced values to the
        next space in the hierarchy.
        '''
        if len(encoding) > self._balanced_h():
            self.logger.info("Tree is unbalanced")
            index = self._index_of_encoding(encoding)
            # Find scapegoat node
            level = len(encoding)
            while (level >= 0):
                index = self._index_of_encoding(encoding[:level])
                if self._is_scapegoat_node(index):
                    self.logger.info("Found scapegoat node with cipher: %d",
                                  self.cache[index].cipher_text)
                    self.logger.info("Clearing outdated syncs")
                    self._clear_syncs(index)
                    self.logger.info("Purging cache and sending rebalance " +
                                     "request messages")
                    self._rebalance_request(index)
                    return
                level -= 1
            self.logger.warning("Insert should not register unbalanced if " +
                                " no scapegoat can be found")

    def insert(self, new_plaintext, start_index=None):
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
                self.cache.append(CacheEntry(new_plaintext, [], self.lru_tag))
                self.lru_tag += 1
                self.current_size += 1
                new_entry = copy.deepcopy(self.cache[0])
                self.sync_messages.append(OutgoingMessage(messageType[2], 
                                                          new_entry))
                return
            else: # Recover from rebalance at root 
                self.logger.info("Recovering from rebalance at root")
                self._handle_miss(0, [], new_plaintext)
                return

        new_entry_encoding = []
        if start_index is not None:
            self.logger.info("Continuing insert after message received")
            current_index = start_index
            current_entry = self.cache[start_index]
            new_entry_encoding = self._enc_copy(current_entry.encoding)
        else:
            current_index = self._index_of_encoding([])
            current_entry = self.cache[current_index]

        # Traverse the tree encoded in the cache table 
        while not current_entry.is_leaf:
            current_entry.lru = self.lru_tag
            self.lru_tag += 1
            current_plaintext = decrypt(current_entry.cipher_text)
            if current_plaintext == new_plaintext:
                self.logger.info("Found duplicate %d in the cache", 
                                 current_plaintext)
                self.waiting_on_insert = (False, None, None)
                return # Found duplicate in cache
            elif (current_plaintext > new_plaintext and 
                 not current_entry.has_left_child):
                # Insert new value as left child
                current_entry.has_left_child = True
                break
            elif (current_plaintext < new_plaintext and
                 not current_entry.has_right_child):
                # Insert new value as right child
                current_entry.has_right_child = True
                break
            else:
                new_entry_encoding.append(0 if current_plaintext > 
                                          new_plaintext else 1)
                index = self._index_of_encoding(new_entry_encoding)
                if index is not None:
                    current_index = index
                    current_entry = self.cache[current_index]
                else:
                    self._handle_miss(current_index, new_entry_encoding,
                                      new_plaintext)
                    return

        # Traversed up to the parent entry of the new entry
        self.logger.info("Traversed up to insert position of plaintext %d",
                     new_plaintext)
        self.waiting_on_insert = (False, None, None)
        
        current_entry.lru = self.lru_tag
        self.lru_tag += 1
        current_plaintext = decrypt(current_entry.cipher_text)
        if current_plaintext == new_plaintext:
            self.logger.info("Found duplicate %d in the cache", 
                             current_plaintext)
            return # Found duplicate in cache
        elif new_plaintext < current_plaintext:
            self.cache[current_index].has_left_child = True
            new_entry_encoding.append(0)
        elif new_plaintext > current_plaintext:
            self.cache[current_index].has_right_child = True
            new_entry_encoding.append(1)
        self.cache[current_index].is_leaf = False
        self._update_parent_sizes(new_entry_encoding)
        if (self.max_size is not None and len(self.cache) == 
            self.max_size):
            self._evict(1)
        new_ciphertext = encrypt(new_plaintext)
        self._cachetable_add(new_ciphertext, new_entry_encoding)
        new_index = self._index_of_encoding(new_entry_encoding)
        new_entry = copy.deepcopy(self.cache[new_index])
        if not new_entry.synced:
            self.sync_messages.append(OutgoingMessage(messageType[2], new_entry))
        self.rebalance(new_entry_encoding)
        assert(self._unique_ciphers)

        
    #######################################################################
    ######################### Higher Tier Methods #########################
    #######################################################################
    def _build_balanced(self, encoding, subtree_list):
        ''' Internal Method build_balanced 
        ----------------------------------
        Return a balanced subtree cache provided with an ordered 
        encoding list
        '''
        if subtree_list == []:
            return (0, [])
        mid_index = math.floor(len(subtree_list)/2)
        left = subtree_list[:mid_index]
        right = subtree_list[mid_index+1:]
        entry = CacheEntry(subtree_list[mid_index].cipher_text, encoding,
                           subtree_list[mid_index].lru)
        r_size, r_entry = self._build_balanced(encoding + [1], right)
        l_size, l_entry = self._build_balanced(encoding + [0], left)

        # Update entry metadata
        entry.subtree_size += l_size + r_size
        if r_entry != [] or l_entry != []:
            entry.is_leaf = False
        if r_entry != []:
            entry.has_right_child = True
        if l_entry != []:
            entry.has_left_child = True

        return (entry.subtree_size, sorted([entry] + r_entry + l_entry))

    def _rebalance_node(self, index):
        ''' Internal Method rebalance_node 
        ----------------------------------
        Rebalance the subtree rooted at the index.  Precondition: the 
        subtree is in the cache
        '''
        self.logger.info("Rebalancing node with cipher: %d", 
                         self.cache[index].cipher_text)
        start_encoding = self.cache[index].encoding
        start_level = len(start_encoding)
        subtree_list = [x for x in self.cache if x.encoding[0:start_level] ==
                        start_encoding]
        self.cache = [x for x in self.cache if x not in subtree_list]
        subtree_list = sorted(subtree_list)
        rebalanced_subtree = self._build_balanced(start_encoding, 
                                                  subtree_list)[1]
        self.merge(rebalanced_subtree)

    def _subtree_in_cache(self, root_index):
        ''' Internal Method subtree_in_cache
        -------------------------------------
        Return true if the entire subtree of the entry at index is in the cache
        '''
        start_encoding = self.cache[root_index].encoding
        subtree_in_cache = [x for x in self.cache if 
                            x.encoding[:len(start_encoding)] == 
                            start_encoding]
        in_cache = len(subtree_in_cache) == self.cache[root_index].subtree_size

        if in_cache:
            self.logger.info("Subtree rooted at cipher %d is in the cache", 
                             self.cache[root_index].cipher_text)
        else:
            self.logger.info("Only %d elements of subtree rooted at cipher " +
                             "%d in the cache.  Expected %d", 
                             len(subtree_in_cache), 
                             self.cache[root_index].cipher_text,
                             self.cache[root_index].subtree_size)
        # For debugging incorrect subtree calculations
        cipher_sub = []
        for elt in subtree_in_cache:
            cipher_sub.append(elt.cipher_text)
        self.logger.info("' Subtree in cache' : " + str(cipher_sub))
        ################################################
        return in_cache

    def merge_new(self, incoming_entries):
        ''' Method merge_new
        --------------------
        Filter incoming entries, only merging in new entries updating
        subtree sizes to match tree in lower hierarchy.  Precondition:
        entry has not been added to the cache yet.  This must hold to 
        guarantee no overcounting of subtree sizes on multiple inserts.  
        This method combines syncs from tier below while merge is
        used on insert requests from above or rebalance merges from
        the same tier.
        '''
        self.logger.info("Beginning merge of %d elements",len(incoming_entries))
        new_entries = list(filter(self._filter_cache_occupancy, 
                                  incoming_entries))
        self.cache.extend(new_entries)
        self.cache.sort()
        self.current_size += 1
        for entry in incoming_entries:
            self._update_parent_sizes(entry.encoding)
        # update parental status 
        for i in range(len(self.cache)):
            if self._right_child(i) is not None: 
                self.cache[i].is_leaf = False
                self.cache[i].has_right_child = True
            if self._left_child(i) is not None:
                self.cache[i].is_leaf = False
                self.cache[i].has_left_child = True

    def rebalance_request(self, subtree, root_enc):
        ''' Method rebalance_request
        ----------------------------
        Assure that the entire subtree is in this cache and perform the
        rebalance
        '''
        self.merge_new(subtree)
        root_index = self._index_of_encoding(root_enc)
        assert(self._subtree_in_cache(root_index))
        self._rebalance_node(root_index)

    def insert_request(self, encoding):
        ''' Method insert_request
        -------------------------
        Return the message to be sent back to the requester in order to
        continue the insert at the sensor. 
        '''
        index = self._index_of_encoding(encoding)
        if index is None:
            self.logger.error("Could not find cipher to send back")
            raise(ValueError("The server should have a record of every" +
                              "existing encoding not at the sensor"))
        entry = copy.deepcopy(self.cache[index])
        entry.synced = True
        self.logger.info("Sending insert reply with cipher %d",
                         self.cache[index].cipher_text)
        return OutgoingMessage(messageType[0], entry)



