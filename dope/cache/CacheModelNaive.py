

def decrypt(cipher):
  # Dummy decryption
  return cipher

def encrypt(plaintext):
  # Dummy encryption
  return plaintext


class CacheModel(object):

  def __init__(self, table_size):
    self.max_size = table_size
    self.current_size = 0
    self.cache = []
    self.lru_tag = 0
    self.outgoing_messages = []
    self.sg_alpha = 0.5
    self.waiting_on_insert = (False, None)

  ## Method insert 
  ## -------------
  ## Used for both fresh inserts and picking up on inserts after cache misses
  ## Either terminates with an updated cache table with the new entry inserted,
  ## a new outgoing message requesting the region of the encoding tree necessary
  ## to continue the insert, or no change in the case of a duplicate found
  def insert(self, new_plaintext, start_index):
    if self.cache == []:
      self.cache = CacheEntry(new_plaintext, [], 0)
      self.lru_tag += 1

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
      current_plaintext = decrypt(current_entry.cipher)
      if current_plaintext == new_plaintext:
        return  # Found the value no further steps needed
      else:
        new_entry_encoding.append(0 if current_plaintext > new_plaintext else 1)
        (found, index) = _search_for_encoding(current_index, new_entry_encoding)
        if found:
          current_index = index
          current_entry = self.cache[current_index]
        else:
          handle_miss()

      # Traversed up to leaf node
      current_entry.lru = self.lru_tag
      self.lru_tag += 1
      current_plaintext = decrypt(current_entry.cipher)
      if current_plaintext == new_plaintext:
        return # Found the value no further steps needed
      _update_parent_sizes(new_entry_encoding)
      cache[current_index].is_leaf = False
      new_entry_encoding.append(0 if current_plaintext > new_plaintext else 1)
      if self.max_size is not None and self.current_size == self.max_size:
        _evict(1)
      new_ciphertext = encrypt(new_plaintext)
      _cachetable_add(current_index, new_ciphertext, new_entry_encoding)


  ## Internal Method search_for_encoding
  ## -----------------------------------
  ## Provided a cache index and the encoding of the child we are looking for
  ## search the region of the cache where this child could be and return 
  ## False if not found, True if found and in this case also the child entry's index
  def _search_for_encoding(self, current_cache_index, next_encoding):
      current_encoding = self.cache[current_cache_index].encoding
      start_level = len(current_encoding)

      # Search up to next tree level for next encoding
      while (len(current_encoding) < start_level + 2):
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
  def _evict(self, int num_evictions):
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
      if len(entry.encoding) > level
        return idx - 1
    return len(self.cache)

  ## Internal Method cachetable_add
  ## ------------------------------
  ## Encrypt the plaintext and add it to the cache as the child of the node
  ## at the current index.  Add entry with the provided new encoding
  def _cachetable_add(current_index, new_ciphertext, new_entry_encoding):
    add_idx = _find_add_idx(current_index, len(new_entry_encoding))
    self.cache.insert(add_idx, CacheEntry(new_ciphertext, new_entry_encoding, self.lru_tag))
    self.lru_tag += 1
    self.current_size += 1

  ## Internal Method update_parent_sizes
  ## -----------------------------------
  ## Go back through all entries effected by the addition of the entry
  ## with the provided encoding and update their subtree size fields
  def _update_parent_sizes(encoding):
    level = 1
    self.cache[0].subtree_size += 1
    current_index = 0
    while (level <= len(encoding)):
      _, next_index = _search_for_encoding(current_index, encoding[:level])
      self.cache[next_idx].subtree_size += 1
      current_index = next_index
      level += 1

  ## Internal Method balanced_h
  ## --------------------------
  ## Return the largest height the scapegoat tree represented by the cache
  ## considers balanced 
  def _balanced_h(self):
    return floor(log(self.current_size,(1/self.alpha)))

  ## Internal Method left_child
  ## --------------------------
  ## Return the index of the left child of the entry at the provided index
  ## if no such child return None  
  def _left_child(index):
    encoding = self.cache[index].encoding
    found, left_child_index = _search_for_encoding(index, encoding.append(0))
    if found == False:
      return None
    else: 
      return left_child_index

  ## Internal Method right_child
  ## ---------------------------
  ## Return the index of the right child of the entry at the provided index
  ## if no such child return None
  def _right_child(index):
    encoding = self.cache[index].encoding
    found, right_child_index = _search_for_encoding(index, encoding.append(1))
    if found == False:
      return None
    else: 
      return right_child_index
  
  ## Internal Method is_scapegoat_node
  ## ---------------------------------
  ## Return true if the node at this index is unbalanced enough to be the scapegoat
  ## in a rebalance 
  def _is_scapegoat_node(index):
    left_child_idx = _left_child(index)
    right_child_idx = _right_child(index)

    if left_child_idx is not None:
      if self.cache[left_child_idx].subtree_size > self.cache[index].subtree_size * self.sg_alpha:
        return True
    if right_child_idx is not None:
      if self.cache[right_child_idx].subtree_size > self.cache[index].subtree_size * self.sg_alpha:
        return True
    return False

  ## Method rebalance
  ## ----------------
  ## Check if the cache is unbalanced after adding encoding.  If so traverse
  ## up the input path, find a scapegoat node and rebalance.  If all entries are
  ## in the cache then simply rebalance in place in the cache.  If some entries are
  ## missing then evict that number and request these entries from the next device
  ## in the hierarchy
  def rebalance(self, encoding, index):
    # Check if tree is unbalanced
    if len(encoding) > _balanced_h():
      # Find scapegoat node
      level = len(encoding)
      while (level > 2)
        _, index =  _search_for_encoding(index, encoding[:level-1])
        if _is_scapegoat_node(index):
          _rebalance_node(index)
          return
        level -= 1
      print("Insert should not register unbalanced if no scapegoat can be found") 

  ## Internal Method _median_find
  ## ----------------------------
  ## Return the median and the index of the median of the provided list
  ## The list is sorted!  Which makes this simple.  If the list has an even
  ## length then return the lower of the two middle values
  def _median_find(inlist):
    if len(inlist) % 2 == 0:
      median_idx = len(inlist)/2 -1
    else:
      median_idx = len(inlist)/2
    return median_idx, inlist[median_idx]

  ## Internal Method index_of_encoding
  ## ---------------------------------
  ## Return the index of the provided encoding
  ## If it can't be found an exception will be raised so this 
  ## should only be called when looking for an encoding previously
  ## found in a list.  Does not search from a smart starting place 
  ## like search_for_encoding
  def _index_of_encoding(encoding):
    return next(i for i,v in enumerate(self.cache) if v.encoding == encoding)

  ## Internal Method subtree_in_cache
  ## --------------------------------
  ## Return true if the entire subtree of entry at index is in the cache
  def _subtree_in_cache(index):
    start_encoding = self.cache[index]
    subtree_in_cache = [x for x in self.cache if x.encoding[:len(start_encoding)] == start_encoding]
    return len(subtree_in_cache) >= self.cache[index].subtree_size
    
  ## Internal Method rebalance_node
  ## ------------------------------
  ## If all elements of subtree rooted at node of provided index are in cache
  ## then rebalance in cache and send coherency message up the hierarchy
  ## If not all elements of the subtree are in the cache then evict the whole
  ## subtree to be rebalanced and mark it for rebalancing up the hierarchy
  def _rebalance_node(index):
    if _subtree_in_cache(index):
      # Can rebalance in the cache
      start_encoding = self.cache[index].encoding
      start_level = len(start_encoding)
      subtree_list = [x for x in self.cache if x.encoding[0:start_level] = start_encoding]
      self.cache = [x for x in self.cache if x is not in subtree_list]
      subtree_list = sorted(subtree_list, lambda x: ''.join(str(y) for y in x.encoding))

      # Reorder entries, placing successive medians into the rebalanced list
      rebalanced_subtree = []
      while subtree_list is not []:      
        median, median_idx = _median_find(subtree_list)
        del subtree_list[median_idx]
        rebalanced_subtree.append(median)

      # Reassign encodings
      rebalanced_subtree[0].encoding = start_encoding
      leaf_set_size = 1
      leaf_set_start = 0
      next_leaf_idx = leaf_set_start
      next_symbol = 0
      for entry in rebalanced_subtree[1:]:
        entry.encoding = rebalanced_subtree[next_leaf_idx].encoding
        entry.encoding.append(next_symbol)
        next_symbol = 1 if next_symbol == 0 else 0
        next_leaf_idx += 1
        if leaf_set_start + leaf_set_size == next_leaf_idx:
          # Finished one level
          leaf_set_start = next_leaf_idx
          leaf_set_size *= 2
      # Add new encodings into the cache.  No problem with collisions 
      # because all possible new encodings have to be in the subtree that
      # was filtered out of the cache.  Solved by simple merge call
      merge(rebalanced_subtree)
      # Signal the higher levels of the hierarchy to maintain coherence
      rebalance_index = _index_of_encoding
      _rebalance_coherence(rebalance_index) 
    else:
      # Evict this subtree and request that the next level of the hierarchy 
      # handle rebalancing
      _rebalance_request(index)

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
    _evict(requested_size)
    self.waiting_on_insert = (True, _index_of_encoding(start_encoding))
    self.outgoing_messages.append(OutgoingMessage(insertRequest, [root_entry], request_size))

  ## Internal Method rebalance_coherence
  ## -----------------------------------
  ## Signal the next level of the hierarchy about a rebalance in order to keep
  ## levels coherent
  def _rebalance_coherence(index):
    root_entry = self.cache[index]
    ##list_to_send = [x for x in self.cache if x.encoding[:len(start_encoding)] == start_encoding]
    self.outgoing_messages.append(OutgoingMessage(rebalanceCoherencyRequest, [root_entry]))

  ## Internal Method rebalance_request
  ## ---------------------------------
  ## Send a request for the next level in the hierarchy to handle rebalancing of this node for you
  def _rebalance_request(index):
    root_entry = self.cache[index]
    self.outgoing_messages.append(OutgoingMessage(rebalanceNonLocalRequest, [root_entry]))


  ## Method merge
  ## ------------
  ## For higher tiers, merge new entries to existing cache.
  ## Also used internally to merge in newly rebalanced subtrees.
  ## Maintains the partitioning of levels in the cache but no further
  ## ordering claims.  Assumes all incoming entries are either new or 
  ## repeats.  All incoherence is handled elsewhere
  def merge(self, incoming_entries):
    insert_index = 0
    incoming_entries = sorted(incoming_entries)
    incoming_entries = [x for x in incoming_entries if x.encoding != y.encoding for y in self.cache] # Filter out repeats
    for entry in incoming_entries:
      if len(self.cache[insert_index].encoding) < len(entry.encoding):
        if insert_index == len(self.cache) - 1:
          self.cache.append(entry)
        insert_index += 1
      else:
        self.cache.insert(insert_index, entry)


  ## Handle rebalance
class CacheEntry(object):
  '''
  One entry in a cache table
  '''
  def __init__(self, ciphertext_data, encoding, lru_tag):
    self.cipher_text = ciphertext_data
    self.encoding = encoding
    self.subtree_size = 0
    self.is_leaf = True
    self.lru = lru_tag

  def __str__(self):
    selfstr = "-------------------------\nPlaintext:" + str(self.plaintext_data) + "\nEncoding:" + str(self.encoding) + "\nSubtree Size:" + str(self.subtree_size) + "\n";
    if self.is_leaf:
      selfstr+= "LEAF\n"

    selfstr+= "-------------\n"
    return selfstr

class OutgoingMessage(Object)
  '''
  A message to be sent to another level of the caching hierarchy.
  '''
  def __init__(self, messageType, entryList, size = 0):
    self.entryList = entryList
    self.messageType = messageType
    self.size = size

class messageType:
  insertRequest, insertResponse, rebalanceCoherencyRequest, rebalanceNonLocalRequest, evictionRequest = range(5)
