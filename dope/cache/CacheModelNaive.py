    #import pdb; pdb.set_trace()
from copy import copy
import math
from  datastruct.scapegoat_tree import SGTree, enc_insert

# Strip enc_root from enc.  If they don't match at the start return None
def strip(enc_root, enc):
  if enc[:len(enc_root)] != enc_root:
    return None
  else: 
    return enc[len(enc_root):]

# For non-connected cache convert into a forest
def convert_cache_to_forest(cache):
  cache = sorted(cache, key=lambda x:len(x.encoding))
  trees = []
  encs = []
  if cache == []:
    print([])
    return
  trees.append(SGTree(cache[0].cipher_text))
  encs.append([])
  for elt in cache[1:]:
    in_tree = 0
    success = False
    # Insert on the first tree that will accept it
    while in_tree < len(trees) and not success:
      enc = strip(encs[in_tree], elt.encoding)
      if enc is None:
        in_tree += 1
        continue
      try:
        enc_insert(trees[in_tree], elt.cipher_text, enc)
        success = True
      except ValueError as e:
        # current encoding tree
        in_tree += 1
 
    # Insert doesn't work on anyone else? Add a new tree to trees
    if not success:
      trees.append(SGTree(elt.cipher_text))
      encs.append(elt.encoding)

  for idx in range(len(trees)):
    print("\n")
    print(trees[idx])
    print("Encoding: " + str(encs[idx]))
    print("\n")

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
  def __init__(self, messageType, entry, start_flag = False, end_flag = False, size = 0):
    self.entry = entry
    self.messageType = messageType
    self.size = size
    self.start_flag = start_flag
    self.end_flag = end_flag

  def __str__(self):
    return "Message Type" + str(self.messageType) + "\n" + str(self.entryList)

messageType = [ "insertRequest", "insertResponse", "rebalanceCoherencyRequest", "rebalanceNonLocalRequest", "evictionRequest" ]


## Method encoding_cmp
  ## ----------------------------
  ## Compares two encoding lists of 1s and 0s.  Trailing 0s go before
  ## Trailing 1s
def encoding_cmp(enc1, enc2):
  # Handle empty encoding
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
      return encoding_cmp(enc1[1:],enc2[1:])
  if enc1[0] != enc2[0]:
    if enc1[0] == 0:
      return -1
    else:
      return 1

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

  # To compare during sorting by encoding for rebalancing
  def __lt__(self,other):
    return encoding_cmp(self.encoding, other.encoding) < 0

  def __gt__(self,other):
    return encoding_cmp(self.encoding, other.encoding) > 0

  def __eq__(self,other):
    return encoding_cmp(self.encoding, other.encoding) == 0

  def __le__(self,other):
    return encoding_cmp(self.encoding, other.encoding) <= 0

  def __ge__(self,other):
    return encoding_cmp(self.encoding, other.encoding) >= 0

  def __ne__(self,other):
    return encoding_cmp(self.encoding, other.encoding) != 0


class CacheModel(object):

  def __init__(self, table_size=None):
    self.max_size = table_size
    self.current_size = 0
    self.cache = []
    self.lru_tag = 0
    self.outgoing_messages = []
    self.sg_alpha = 0.5
    self.waiting_on_insert = (False, None, None)

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



  ## Internal Method evict 
  ## ---------------------
  ## Remove the num_eviction least recently used entries in the cache
  ## Send a message 
  def _evict(self, num_evictions):
    sorted_entries = sorted(self.cache, key =lambda x: x.lru)
    # Finding elements to evict could be much more intelligent than lru (locality missing)
    lru_entries = sorted_entries[:num_evictions]
    self.cache = [x for x in self.cache if not x in lru_entries]
    self.current_size = len(self.cache)
    for entry in lru_entries:
      self.outgoing_messages.append(OutgoingMessage(messageType[4], entry))
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
    level = 0
    while (level <= len(encoding)):
      next_index = self._index_of_encoding(encoding[:level])
      if next_index is not None:
        self.cache[next_index].subtree_size += 1
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
    left_child_index = self._index_of_encoding(encoding)
    return left_child_index

  ## Internal Method right_child
  ## ---------------------------
  ## Return the index of the right child of the entry at the provided index
  ## if no such child return None
  def _right_child(self, index):
    encoding = self._enc_copy(self.cache[index].encoding)
    encoding.append(1)
    right_child_index = self._index_of_encoding(encoding)
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

  ## Internal Method buid_balanced
  ## -----------------------------
  ## Return a balanced subtree cache provided with an ordered encoding list
  def _build_balanced(self, encoding, subtree_list):
    if subtree_list == []:
      return (0, [])
    mid_index = math.floor(len(subtree_list)/2)
    left = subtree_list[:mid_index]
    right = subtree_list[mid_index+1:]
    entry = CacheEntry(subtree_list[mid_index].cipher_text, encoding, subtree_list[mid_index].lru)
    r_size, r_entry = self._build_balanced(encoding + [1], right)
    l_size, l_entry = self._build_balanced(encoding + [0], left)

    # update entry metadata
    entry.subtree_size += l_size + r_size
    if r_entry != [] and l_entry != []:
      entry.has_one_child = False
      entry.is_leaf = False
    elif not(r_entry == [] and l_entry == []):
      entry.is_leaf = False

    return (entry.subtree_size, sorted([entry] + r_entry + l_entry))


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
    for i,v in enumerate(self.cache):
      if v.encoding == encoding:
        return i
    return None

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
    start_encoding = root_entry.encoding
    subtree_to_send = [x for x in self.cache if x.encoding[:len(start_encoding)]== start_encoding]
    subtree_to_send = sorted(subtree_to_send, key = lambda x: len(x.encoding))
    self.outgoing_messages.append(OutgoingMessage(messageType[2], subtree_to_send[0], start_flag = True))
    for entry in subtree_to_send[1:len(subtree_to_send)-1]:
      self.outgoing_messages.append(OutgoingMessage(messageType[2], entry))
    self.outgoing_messages.append(OutgoingMessage(messageType[2], subtree_to_send[-1], end_flag = True))


  ## Method resolve_rebalance_coherence
  ## ----------------------------------
  ## Used by a higher tier space to merge in a list of entries that have been rebalanced
  ## and delete any duplicates with now stale encodings 
  def resolve_rebalance_coherence(self, subtree):
    root_encoding = subtree[0].encoding
    # Delete any stale entries
    old_size = len(self.cache)
    self.cache = [x for x in self.cache if x.encoding[:len(root_encoding)] != root_encoding]
    mid_size = len(self.cache)
    # Merge in new entries
    self.merge(subtree) 
    self.current_size = len(self.cache)
    new_size = len(self.cache)
    # if (new_size < old_size):
    #   print("Old size:" + str(old_size))
    #   print("New size:" + str(new_size))
    #   print("Mid size:" + str(mid_size))
    #   print("Number of replacement encodings sent " + str(len(subtree))+ "\n")

  ## Internal Method rebalance_request
  ## ---------------------------------
  ## Send a request for the next level in the hierarchy to handle rebalancing of this node for you
  def _rebalance_request(self, index):
    root_entry = self.cache[index]
    start_encoding = root_entry.encoding
    # Need to do an eviction too 
    subtree_to_evict = [x for x in self.cache if x.encoding[:len(start_encoding)]== start_encoding]
    self.cache = [x for x in self.cache if not x in subtree_to_evict] # Evict entries
    self.current_size = len(self.cache)
    self.outgoing_messages.append(OutgoingMessage(messageType[3], root_entry, start_flag = True))
    for entry in subtree_to_evict[1:len(subtree_to_evict)-1]:
      self.outgoing_messages.append(OutgoingMessage(messageType[3], entry))
    self.outgoing_messages.append(OutgoingMessage(messageType[3], subtree_to_evict[-1], end_flag = True))


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
    incoming_entries.sort()
    filter(self._filter_cache_occupancy, incoming_entries)
    self.cache.extend(incoming_entries)
    self.cache.sort()
    self.current_size = len(self.cache)

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
      subtree_list = sorted(subtree_list)

      # Reorder entries, placing successive medians into the rebalanced list
      rebalanced_subtree = self._build_balanced(start_encoding, subtree_list)[1]

      # Add new encodings into the cache.  No problem with collisions 
      # because all possible new encodings have to be in the subtree that
      # was filtered out of the cache.  Solved by simple merge call
      self.merge(rebalanced_subtree)
      # Signal the higher levels of the hierarchy to maintain coherence (if necessary)
      if self.max_size is not None:
        index = self._index_of_encoding(start_encoding)
        self._rebalance_coherence(self.cache[index]) 
    else:
      # Evict this subtree and request that the next level of the hierarchy 
      # handle rebalancing
      self._rebalance_request(index)

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
        index = self._index_of_encoding(encoding[:level])
        if self._is_scapegoat_node(index):
          self._rebalance_node(index)
          return
        level -= 1
      #print("Insert should not register unbalanced if no scapegoat can be found") 
      #print(self.cache[self._index_of_encoding(encoding)])
      #print(encoding)
      #convert_cache_to_forest(self.cache)



  ## Method resolve_rebalance_request
  ##---------------------------------
  ## Used by a higher tier space to merge into its cache a list of entries and
  ## perform a rebalance starting at the node with the provided encoding
  ## Note subtree is ordered with the root at the head of the list
  def resolve_rebalance_request(self, subtree):
    root_encoding = subtree[0].encoding
    self.merge(subtree)
    root_index = self._index_of_encoding(root_encoding)
    assert(self._subtree_in_cache(root_index))
    index = self._index_of_encoding(root_encoding)
    self._rebalance_node(index)


  ## Internal Method handle_miss
  ## ---------------------------
  ## Called during inserts when the next entry to compare is in the encoding
  ## tree but not in this level of the cache.  Bring in as much of the subtree
  ## rooted at the entry associated with the provided index
  def _handle_miss(self, subtree_root, next_encoding, plaintext):
    if self.current_size == self.max_size:
      self._evict(1)
    self.waiting_on_insert = (True, subtree_root, plaintext)
    self.outgoing_messages.append(OutgoingMessage(messageType[0], next_encoding))


  ## Method miss_response
  ## --------------------
  ## Called by gateway or server to respond to misses (Assuming infinite storage gateway / 2 tiers)
  def resolve_insert_request(self, encoding):
    index = _index_of_encoding(encoding)
    return OutgoingMessage(messageType[1], self.cache[index])

  
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
      current_index = self._index_of_encoding([])
      current_entry = self.cache[current_index]

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
        index = self._index_of_encoding(new_entry_encoding)
        if index is not None:
          current_index = index
          current_entry = self.cache[current_index]
        else:
          self._handle_miss(current_entry, new_entry_encoding, plaintext)

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



