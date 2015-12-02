__author__ = 'lauril'


class CacheModel(object):
    '''
    parent class for caching
    '''
    def __init__(self, table_size):
      self.max_size = table_size
      self.current_size = 0
      self.cache = []

    def insert(self, v_insert):
      if self.cache == []:
        self.cache = CacheEntry(plaintext_data, [])

      else:
        # Start at root 
        current_index = 0
        current_entry = self.cache[0]

        # Traverse tree encoded in cache
        while (not current_entry.is_leaf):
          if current_entry.plaintext_data == v_insert:
            return  # Found the value no further steps needed
          else: 
            (found, index) = _search_for_encoding()
            if found:
              current_index = index
              current_entry = self.cache[current_index]
            else:
              raise "Cache miss"

        # Traversed up to leaf node
        if current_entry.plaintext_data == v_insert:
          return # Found the value no further steps needed
        if self.current_size == self.max_size
          raise "Cache full need to evict"
        _cachetable_add(current_index, v_insert)

    def evict(self):
      pass

    def _search_for_encoding(self, current_cache_index, next_encoding):
      current_encoding = self.cache[current_cache_index]  
      start_level = len(current_encoding)

      # Search up to next tree level for next encoding
      while (len(current_encoding) < start_level + 2):
        current_cache_index += 1
        current_encoding = self.cache[current_cache_index]
        if current_encoding = next_encoding:
          return (True, current_cache_index)

      # No encoding found
      return(False, -1)

    # Insert v_insert value into a fresh cache entry that is 
    # the child of cache[parent_idx]
    def _cachetable_add(self, parent_idx, v_insert):


class CacheEntry(object):
  '''
  Table containing cache entries
  '''
  def __init__(self, plaintext_data, encoding)
    self.plaintext_data = plaintext_data
    self.encoding = encoding
    self.subtree_size = 0
    self.is_leaf = True


class CacheEntries(object):