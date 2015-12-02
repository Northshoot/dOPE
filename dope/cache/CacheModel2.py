# A Cache model using WL tree compression and representing
# tree as two tables

def decrypt(cipher):
  # Dummy decryption
  return cipher

def encrypt(plaintext):
  # Dummy encryption
  return plaintext



class CacheModel:

  def __init__(self,cTable_size,sTable_size):
    self.structure_table = StructureTable(sTable_size)
    self.cipher_table = CipherTable(cTable_size)
    self.root_label = None
    self.init_label = 1

  def insert(self,plaintext):
    # Start at root
    if self.root_label is None:
      self.structure_table.add(None, self.init_label)
      self.root_label = self.init_label

    # Traverse tree to insert new encoding
    current_label = self.root_label
    new_label = None
    while(True):
      current_pt = decrypt(self.cipher_table.entries[current_label])
      if plaintext == current_pt:
        # Repeat found insert finished 
        break
      elif plaintext > current_pt:
        next_label = self.structure_table.lookup_right_child(current_label)
        if (next_label is None):
          new_label = self.structure_table.compute_new_label(current_label)
          self.structure_table.add_right(current_label, new_label)
      else:
        next_label = self.structure_table.lookup_left_child(current_label)
        if (next_label is None):
          new_label = self.structure_table.compute_new_label(current_label)
          self.structure_table.add_left(current_label, new_label)
      if next_label is None:
        # Reached leaf in encoding tree
        assert(new_label is not None)
        self.cipher_table.add(new_label, encrypt(plaintext))
        break
    
    # Work up the tree to detect any possible rebalancing that needs to happen
    

    # Need some way to encode L/R in children of label in structure table (not hard in table, curious about in compressed label)
    # If we run into a compressed label we need to decompress it to complete the traversal

    # If ciphertext not in cipher table we have a cache miss and need to retrieve from gateway
    # ( Not handling yet ) assuming structure table might grow too large for sensor to handle we will need to handle structural cache misses
    # For each miss we are going to need to trust that gateway is coherent (enforce coherency on mutation or automatically)

  def handle_rebalance(self):
    pass

  def handle_miss(self):
    pass


class CipherTable:
  def __init__(self, max_size):
    self.entries = {}
    self.max_size = max_size
    self.size = 0

  # Return true if entry was added, return false if table already full
  def add(self, label, cipher):
    if self.size < self.max_size:
      self.entries[label] = cipher
      self.size += 1
      return True
    else:
      return False

  # Return true if entry existed and was deleted
  def evict_by_label(self, label):
    if self.entries.has_key(label):
      del self.entries[label] 
      self.size -= 1
      return True 
    else:
      return False


class StructureTable:
  def __init__(self, max_size = 1000000000):
    self.entries = {}
    self.max_size = max_size
    self.size = 0

  # Need to update to allow difference in adding left and right
  def add_right(self, parent_label, child_label):
    if parent_label is None:
      self.entries[child_label] = []
    self.entries[parent_label].append(child_label)
    self.size += 1

  def add_left(self, parent_label, child_label):
    if parent_label is None:
      self.entries[child_label] = []
    self.entries[parent_label].append(child_label)
    self.size += 1

  # Return None if node does not exist in tree
  def lookup_left_child(self, parent_label):
    pass

  # Return None if node does not exist in tree
  def lookup_right_child(self, parent_label):
    pass 

  def compute_new_label(self, parent_label):
    pass


  
