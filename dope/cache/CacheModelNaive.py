

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

  # Used for both fresh inserts and picking up on inserts after cache misses
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
      current_plaintext = decrypt(current_entry.cipher)
      if current_plaintext == new_plaintext:
        return # Found the value no further steps needed

      new_entry_encoding.append(0 if current_plaintext > new_plaintext else 1)
      if self.current_size == self.max_size
        _evict(1)

      _cachetable_add(current_index, new_plaintext, new_entry_encoding)


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

  def _evict(self, int num_evictions):
    sorted_entries = sorted(self.cache, lambda x: x.lru)
    # Finding elements to evict could be much more intelligent than lru (locality missing)
    lru_entries = sorted_entries[:num_evictions]
    self.cache = [x for x in self.cache if not x in lru_entries]

  def _find_add_idx(self, current_index, level):
    for idx, entry in enumerate(self.cache[current_index:]):
      if len(entry.encoding) > level
        return idx - 1
    return len(self.cache)

  def _cachetable_add(current_index, new_plaintext, new_entry_encoding):
    add_idx = _find_add_idx(current_index, len(new_entry_encoding))
    self.cache.insert(add_idx, CacheEntry(new_plaintext, new_entry_encoding, self.lru_tag))
    self.lru_tag += 1
    self.current_size += 1

  def rebalance(self):
    
  def handle_miss(self):
    _evict( min(self.current_size, subtree_size))

  # For higher tiers, merge new entries to existing cache
  def merge(self, incoming_entries):


class CacheEntry(object):
  '''
  One entry in a cache table
  '''
  def __init__(self, plaintext_data, encoding, lru_tag):
    self.cipher_text = encrypt(plaintext_data)
    self.encoding = encoding
    self.subtree_size = 0
    self.is_leaf = True
    self.lru = lru_tag

  def __str__(self):
    selfstr = "-------------\n" + str(self.plaintext_data) + "\n" + str(self.encoding) + "\n" + str(self.subtree_size) + "\n";
    if self.is_leaf:
      selfstr+= "LEAF\n"

    selfstr+= "-------------\n"
    return selfstr
