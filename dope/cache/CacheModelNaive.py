    #import pdb; pdb.set_trace()
from copy import copy
import math

def decrypt(cipher):
  # Dummy decryption
  return cipher

def encrypt(plaintext):
  # Dummy encryption
  return plaintext

class OutgoingMessage(object):
  '''
  A message to be sent to another level of the caching hierarchy.
  '''
  def __init__(self, messageType, entryList, size = 0):
    self.entryList = entryList
    self.messageType = messageType
    self.size = size

  def __str__(self):
    return "Message Type" + str(self.messageType) + "\n" + str(self.entryList)

class messageType:
  insertRequest, insertResponse, rebalanceCoherencyRequest, rebalanceNonLocalRequest, evictionRequest = range(5)


class CacheModel(object):

  def __init__(self, table_size):
    self.max_size = table_size
    self.current_size = 0
    self.cache = []
    self.lru_tag = 0
    self.outgoing_messages = []
    self.sg_alpha = 0.5
    self.waiting_on_insert = (False, None)

  def __str__(self):
    sizes = "Max Size: " + str(self.max_size) + "\n" + "Current Size: " + str(self.current_size) + "\n"
    outgoing_messages = "Outgoing Messages:" + str(self.outgoing_messages) + "\n"
    ret = sizes + outgoing_messages
    for x in self.cache:
      ret += str(x)
    return ret

  ## Internal Method enc_copy
  ## ------------------------
  ## Make a deeper copy of a list
  def _enc_copy(self, list_to_copy):
    new_list = []
    for elt in list_to_copy:
      new_list.append(elt)
    return new_list

  ## Internal Method search_for_encoding
  ## -----------------------------------
  ## Provided a cache index and the encoding of the child we are looking for
  ## search the region of the cache where this child could be and return 
  ## False if not found, True if found and in this case also the child entry's index
  def _search_for_encoding(self, current_cache_index, next_encoding):
      #import pdb; pdb.set_trace()
      current_encoding = self.cache[current_cache_index].encoding
      start_level = len(current_encoding)

      # Search up to next tree level for next encoding
      while (len(current_encoding) < start_level + 2 and current_cache_index < self.current_size-1):
        current_cache_index += 1
        current_encoding = self.cache[current_cache_index].encoding
        if current_encoding == next_encoding:
          return (True, current_cache_index)

      # No encoding found
      return(False, -1)




  ## Internal Method evict 
  ## ---------------------
  ## Remove the num_eviction least recently used entries in the cache
  ## Send a message 
  def _evict(self, num_evictions):
    sorted_entries = sorted(self.cache, lambda x: x.lru)
    # Finding elements to evict could be much more intelligent than lru (locality missing)
    lru_entries = sorted_entries[:num_evictions]
    self.cache = [x for x in self.cache if not x in lru_entries]
    return lru_entries


  ## Internal Method find_add_idx
  ## ----------------------------
  ## Return the index into which the child of the entry with current index 
  ## should be inserted
  def _find_add_idx(self, current_index, level):
    for idx, entry in enumerate(self.cache[current_index:]):
      if len(entry.encoding) > level:
        return idx - 1
    return len(self.cache)

  ## Internal Method cachetable_add
  ## ------------------------------
  ## Encrypt the plaintext and add it to the cache as the child of the node
  ## at the current index.  Add entry with the provided new encoding
  def _cachetable_add(self, current_index, new_ciphertext, new_entry_encoding):
    add_idx = self._find_add_idx(current_index, len(new_entry_encoding))
    self.cache.insert(add_idx, CacheEntry(new_ciphertext, new_entry_encoding, self.lru_tag))
    self.lru_tag += 1
    self.current_size += 1
 

  ## Internal Method update_parent_sizes
  ## -----------------------------------
  ## Go back through all entries effected by the addition of the entry
  ## with the provided encoding and update their subtree size fields
  def _update_parent_sizes(self, encoding):
    level = 1
    self.cache[0].subtree_size += 1
    current_index = 0
    while (level <= len(encoding)):
      _, next_index = self._search_for_encoding(current_index, encoding[:level])
      self.cache[next_index].subtree_size += 1
      current_index = next_index
      level += 1

  ## Internal Method update_parent_sizes_list
  ## ----------------------------------------
  ## Provided an external list of cache entries and a newly added entry
  ## peform the same process of updating all nodes along the encoding path
  ## to register one more child in their subtree
  def _update_parent_sizes_list(self, encoding, list):
    level = 1
    list[0].subtree_size += 1
    for entry in list:
      if entry.encoding == encoding[:level]:
        level += 1
        entry.subtree_size += 1


  ## Internal Method balanced_h
  ## --------------------------
  ## Return the largest height the scapegoat tree represented by the cache
  ## considers balanced 
  def _balanced_h(self):
    return math.floor(math.log(self.current_size,(1/self.sg_alpha)))

  ## Internal Method left_child
  ## --------------------------
  ## Return the index of the left child of the entry at the provided index
  ## if no such child return None  
  def _left_child(self, index):
    encoding = self._enc_copy(self.cache[index].encoding)
    encoding.append(0)
    found, left_child_index = self._search_for_encoding(index, encoding)
    if found == False:
      return None
    else: 
      return left_child_index

  ## Internal Method right_child
  ## ---------------------------
  ## Return the index of the right child of the entry at the provided index
  ## if no such child return None
  def _right_child(self, index):
    encoding = self._enc_copy(self.cache[index].encoding)
    encoding.append(1)
    found, right_child_index = self._search_for_encoding(index, encoding)
    if found == False:
      return None
    else: 
      return right_child_index

  ## Internal Method is_scapegoat_node
  ## ---------------------------------
  ## Return true if the node at this index is unbalanced enough to be the scapegoat
  ## in a rebalance 
  def _is_scapegoat_node(self, index):
    left_child_idx = self._left_child(index)
    right_child_idx = self._right_child(index)

    if left_child_idx is not None:
      if self.cache[left_child_idx].subtree_size > self.cache[index].subtree_size * self.sg_alpha:
        return True
    if right_child_idx is not None:
      if self.cache[right_child_idx].subtree_size > self.cache[index].subtree_size * self.sg_alpha:
        return True
    return False

  ## Internal Method encoding_cmp
  ## ----------------------------
  ## Compares two encoding lists of 1s and 0s.  Trailing 0s go before
  ## Trailing 1s
  def _encoding_cmp(enc1, enc2):
    if enc1[0] == enc2[0]:
      if len(enc1) ==1 and len(enc2) == 1:
        return 0
      elif len(enc1) == 1:
        if enc2[1] == 1:
          return 1
        else:
          return -1
      elif len(enc2) == 1:
        if enc1[1] == 1:
          return -1
        else:
          return 1
      else:
        return _encoding_cmp(enc1[1:],enc2[1:])

    if enc1[0] != enc2[0]:
      if enc1[0] == 0:
        return 1
      else 
        return -1




  ## Internal Method _median_find
  ## ----------------------------
  ## Return the median and the index of the median of the provided list
  ## The list is sorted!  Which makes this simple.  If the list has an even
  ## length then return the lower of the two middle values
  def _median_find(self, inlist):
    if len(inlist) % 2 == 0:
      median_idx = math.floor(len(inlist)/2) -1
    else:
      median_idx = math.floor(len(inlist)/2)
    return inlist[median_idx], median_idx

  ## Internal Method index_of_encoding
  ## ---------------------------------
  ## Return the index of the provided encoding
  ## If it can't be found an exception will be raised so this 
  ## should only be called when looking for an encoding previously
  ## found in a list.  Does not search from a smart starting place 
  ## like search_for_encoding
  def _index_of_encoding(self, encoding):
    return next(i for i,v in enumerate(self.cache) if v.encoding == encoding)

  ## Internal Method subtree_in_cache
  ## --------------------------------
  ## Return true if the entire subtree of entry at index is in the cache
  def _subtree_in_cache(self, index):
    start_encoding = self.cache[index].encoding
    subtree_in_cache = [x for x in self.cache if x.encoding[:len(start_encoding)] == start_encoding]
    return len(subtree_in_cache) >= self.cache[index].subtree_size
    
  ## Internal Method rebalance_coherence
  ## -----------------------------------
  ## Signal the next level of the hierarchy about a rebalance in order to keep
  ## levels coherent
  def _rebalance_coherence(self, root_entry):
    ##list_to_send = [x for x in self.cache if x.encoding[:len(start_encoding)] == start_encoding]
    self.outgoing_messages.append(OutgoingMessage(messageType.rebalanceCoherencyRequest, [root_entry]))

  ## Internal Method rebalance_request
  ## ---------------------------------
  ## Send a request for the next level in the hierarchy to handle rebalancing of this node for you
  def _rebalance_request(self, index):
    root_entry = self.cache[index]
    self.outgoing_messages.append(OutgoingMessage(messageType.rebalanceNonLocalRequest, [root_entry]))

  ## Internal Method filter_cache_occupancy
  ## --------------------------------------
  ## Returns false if an entry with the same
  ## encoding exists in the cache
  def _filter_cache_occupancy(entry):
    for y in self.cache:
      if y.encoding == entry.encoding:
        return False
    return True

  ## Method merge
  ## ------------
  ## For higher tiers, merge new entries to existing cache.
  ## Also used internally to merge in newly rebalanced subtrees.
  ## Maintains the partitioning of levels in the cache but no further
  ## ordering claims.  Assumes all incoming entries are either new or 
  ## repeats.  All incoherence is handled elsewhere
  def merge(self, incoming_entries):
    insert_index = 0
    entry_index = 0
    incoming_entries = sorted(incoming_entries, key=lambda x: ''.join(str(y) for y in x.encoding))
    filter(self._filter_cache_occupancy, incoming_entries)
    while entry_index < len(incoming_entries):
      if self.cache == []:
        self.cache.append(incoming_entries[entry_index])
        entry_index += 1
      elif len(self.cache[insert_index].encoding) < len(incoming_entries[entry_index].encoding):
        if insert_index == len(self.cache) - 1:
          self.cache.append(incoming_entries[entry_index])
          entry_index += 1
        insert_index += 1
      else:
        self.cache.insert(insert_index, incoming_entries[entry_index])
        entry_index += 1


  ## Internal Method rebalance_node
  ## ------------------------------
  ## If all elements of subtree rooted at node of provided index are in cache
  ## then rebalance in cache and send coherency message up the hierarchy
  ## If not all elements of the subtree are in the cache then evict the whole
  ## subtree to be rebalanced and mark it for rebalancing up the hierarchy
  def _rebalance_node(self, index):
    if self._subtree_in_cache(index):
      # Can rebalance in the cache
      start_encoding = self.cache[index].encoding
      start_level = len(start_encoding)
      subtree_list = [x for x in self.cache if x.encoding[0:start_level] == start_encoding]
      self.cache = [x for x in self.cache if x not in subtree_list]
      subtree_list = sorted(subtree_list, cmp=self._encoding_cmp)

      # Reorder entries, placing successive medians into the rebalanced list
      rebalanced_subtree = []
      while subtree_list != []:      
        median, median_idx = self._median_find(subtree_list)
        del subtree_list[median_idx]
        rebalanced_subtree.append(median)

      # Reassign encodings
      for entry in rebalanced_subtree:
        entry.has_one_child = False
        entry.is_leaf = True
        entry.subtree_size = 1
      rebalanced_subtree[0].encoding = start_encoding
      leaf_set_size = 1
      leaf_set_start = 0
      next_leaf_idx = leaf_set_start
      next_symbol = 0

      for idx, entry in enumerate(rebalanced_subtree[1:]):
        entry.encoding = self._enc_copy(rebalanced_subtree[next_leaf_idx].encoding)
        entry.encoding.append(next_symbol)
        self._update_parent_sizes_list(entry.encoding, rebalanced_subtree[:idx+1])
        next_symbol = 1 if next_symbol == 0 else 0
        if next_symbol == 1:
          rebalanced_subtree[next_leaf_idx].is_leaf = False
          rebalanced_subtree[next_leaf_idx].has_one_child = True
        elif next_symbol == 0: # move on to another new parent
          rebalanced_subtree[next_leaf_idx].has_one_child = False
          next_leaf_idx += 1  
        if leaf_set_start + leaf_set_size == next_leaf_idx:
          # Finished one level
          leaf_set_start = next_leaf_idx
          leaf_set_size *= 2
      # Add new encodings into the cache.  No problem with collisions 
      # because all possible new encodings have to be in the subtree that
      # was filtered out of the cache.  Solved by simple merge call
      self.merge(rebalanced_subtree)
      # Signal the higher levels of the hierarchy to maintain coherence
      self._rebalance_coherence(start_encoding) 
    else:
      # Evict this subtree and request that the next level of the hierarchy 
      # handle rebalancing
      self._rebalance_request(rebalanced_subtree[0])

  ## Method rebalance
  ## ----------------
  ## Check if the cache is unbalanced after adding encoding.  If so traverse
  ## up the input path, find a scapegoat node and rebalance.  If all entries are
  ## in the cache then simply rebalance in place in the cache.  If some entries are
  ## missing then evict that number and request these entries from the next device
  ## in the hierarchy
  def rebalance(self, encoding):
    # Check if tree is unbalanced
    if len(encoding) > self._balanced_h():
      index = self._index_of_encoding(encoding)
      # Find scapegoat node
      level = len(encoding)
      while (level >= 0):
        index =  self._index_of_encoding(encoding[:level])
        if self._is_scapegoat_node(index):
          self._rebalance_node(index)
          return
        level -= 1
      print("Insert should not register unbalanced if no scapegoat can be found") 


  ## Internal Method handle_miss
  ## ---------------------------
  ## Called during inserts when the next entry to compare is in the encoding
  ## tree but not in this level of the cache.  Bring in as much of the subtree
  ## rooted at the entry associated with the provided index
  def _handle_miss(self, subtree_root):
    root_entry = self.cache[subtree_root]
    start_encoding = root_entry.encoding
    requested_size = min(self.current_size -1, root_entry.subtree_size)
    self.cache[subtree_root].lru = self.lru_tag
    self._evict(requested_size)
    self.waiting_on_insert = (True, self._index_of_encoding(start_encoding))
    self.outgoing_messages.append(OutgoingMessage(insertRequest, [root_entry], request_size))

  
  ## Method insert 
  ## -------------
  ## Used for both fresh inserts and picking up on inserts after cache misses
  ## Either terminates with an updated cache table with the new entry inserted,
  ## a new outgoing message requesting the region of the encoding tree necessary
  ## to continue the insert, or no change in the case of a duplicate found
  def insert(self, new_plaintext, start_index = None):
    if self.cache == []:
      self.cache.append(CacheEntry(new_plaintext, [], 0))
      self.lru_tag += 1
      self.current_size += 1
      return

    new_entry_encoding = []
    if start_index is not None:
      current_index = start_index
      current_entry = self.cache[start_index]
    else:
      # Start at root 
      current_index = 0
      current_entry = self.cache[0]

    # Traverse tree encoded in cache
    while (not current_entry.is_leaf):
      current_entry.lru = self.lru_tag
      self.lru_tag += 1
      current_plaintext = decrypt(current_entry.cipher_text)
      if current_plaintext == new_plaintext:
        return  # Found the value no further steps needed
      elif current_plaintext > new_plaintext and self._left_child(current_index) is None:
        break
      elif current_plaintext < new_plaintext and self._right_child(current_index) is None:
        break
      else:
        new_entry_encoding.append(0 if current_plaintext > new_plaintext else 1)
        (found, index) = self._search_for_encoding(current_index, new_entry_encoding)
        if found:
          current_index = index
          current_entry = self.cache[current_index]
        else:
          self._handle_miss()

    # Traversed up to leaf node or parent with correct child free
    if current_entry.is_leaf:
      current_entry.lru = self.lru_tag
      self.lru_tag += 1
      current_plaintext = decrypt(current_entry.cipher_text)
      if current_plaintext == new_plaintext:
        return # Found the value no further steps needed
      self.cache[current_index].is_leaf = False
      self.cache[current_index].has_one_child = True
    else:
      self.cache[current_index].has_one_child = False
    self._update_parent_sizes(new_entry_encoding)
    new_entry_encoding.append(0 if current_plaintext > new_plaintext else 1)
    if self.max_size is not None and self.current_size == self.max_size:
      self._evict(1)
    new_ciphertext = encrypt(new_plaintext)
    self._cachetable_add(current_index, new_ciphertext, new_entry_encoding)
    self.rebalance(new_entry_encoding)


## Handle rebalance
class CacheEntry(object):
  '''
  One entry in a cache table
  '''
  def __init__(self, ciphertext_data, encoding, lru_tag):
    self.cipher_text = ciphertext_data
    self.encoding = encoding
    self.subtree_size = 1
    self.is_leaf = True
    self.has_one_child = False
    self.lru = lru_tag

  def __str__(self):
    selfstr = "-------------------------\nCiphertext:" + str(self.cipher_text) + "\nEncoding:" + str(self.encoding) + "\nSubtree Size:" + str(self.subtree_size) + "\n"
    if self.is_leaf:
      selfstr+= "LEAF\n"
    elif self.has_one_child:
      selfstr+= "ONE CHILD\n"
    else:
      selfstr+= "TWO CHILDREN\n"

    selfstr+= "-------------\n"
    return selfstr

