__author__ = 'wDaviau'
# Pretty printing from steve krenzel http://stevekrenzel.com/articles/printing-trees
from math import log, floor


# A scape goat tree without support for deletions
class SGNode:
  def __init__(self,val):
      self.l = None
      self.r = None
      self.data = val

  def __str__(self,depth = 0):
    ret = ""
        # Print right branch
    if self.r != None:
      ret += self.r.__str__(depth + 1)

        # Print own value
    ret += "\n" + ("    "*depth) + str(self.data)

        # Print left branch
    if self.l != None:
      ret += self.l.__str__(depth + 1)
    return ret

class SGTree:
  def __init__(self,val,alpha=0.5):
    # None stands in for empty leaves
    self.root = SGNode(val)
    self.size = 1
    self.alpha = alpha

  def __str__(self):
    return self.root.__str__()

  def balanced_h(self):
    return floor(log(self.size,(1/self.alpha)))
    


###############################################################
# These are the expected insert and search functions when the #
# values are comparable by the caller                         #
###############################################################

def search(node,val):
  if node == None:
    return False
  elif node.data == val:
    return True
  elif node.data > val:
    return search(bst.l,val)
  elif node.data < val:
    return search(bst.r,val)


# Determine the size of the tree with node as the root
def size(node):
  if node == None:
    return 0
  else:
    return size(node.r)+size(node.l)+1 

# Determine if this node has an imbalance between left and right children
def is_scapegoat(sgtree,node):
  max_size = sgtree.alpha * size(node)
  if size(node.l) > max_size or size(node.r) > max_size:
    return True
  else:
    return False


# Helper function taking an unbalanced sgtree node and building a sorted list of data
def _build_list(node):
  if node == None:
    return []
  else:
    return _build_list(node.l) + [node.data] + _build_list(node.r)


# Helper function taking a sorted list and returning the root of a 
# balanced tree
def _build_tree(sorted_list):
  if len(sorted_list) == 0:
    return None
  elif len(sorted_list) == 1:
    return SGNode(sorted_list[0])
  else:
    mid_index = floor(len(sorted_list)/2)
    left = sorted_list[:mid_index]
    right = sorted_list[mid_index+1:]
    node = SGNode(sorted_list[mid_index])
    node.l = _build_tree(left)
    node.r = _build_tree(right)
    return node

# Rebalance tree with node as root
def rebalance(node):
  sorted_list = _build_list(node)
  node = _build_tree(sorted_list)
  return node

# Helper function returns flag indicating a rebalance is needed and the new tree
def _insert(sgtree,node,val,depth):
  if node == None:
    sgtree.size += 1
    if (depth > sgtree.balanced_h() ):
      return (True,SGNode(val))
    else:
      return (False,SGNode(val))
  else:
    if node.data > val:
      (unbalanced,new_l) = _insert(sgtree,node.l,val,depth+1)
      node.l = new_l
      if unbalanced:
        # Check if this is a scapegoat node
        if is_scapegoat(sgtree,node):
          # Rebalance scapegoat node for a balanced tree
          return (False,rebalance(node))
        else:
          # Scapegoat node is further up the tree
          return (True,node)

      return (False,node)
    elif node.data < val:
      (unbalanced,new_r) = _insert(sgtree,node.r,val,depth+1)
      node.r = new_r
      if unbalanced:
        # Check if this is a scapegoat node
        if is_scapegoat(sgtree,node):
          # Rebalance scapegoat node for a balanced tree
          return (False,rebalance(node))
        else:
          # Scapegoat node is further up the tree
          return (True,node)

      return (False,node)
    else:
      return (False,node)


def insert(sgtree,val):
  new_root = _insert(sgtree,sgtree.root,val,0)[1]
  sgtree.root = new_root

 


##############################################################
# These functions define an API for use by a server to insert# 
# on and compare values in a  mOPE ciphertext tree           #
##############################################################

# Pre-order search of bst
def linear_search(node,val):
  if node == None:
    return False
  elif node.data == val:
    return True 
  elif linear_search(node.l,val):
    return True
  elif linear_search(node.r,val):
    return True
  else:
    return False

# return the (enc,found). e is the mOPE encoding as a list of 1s and 0s
# this is None if there is no encoding.  Found is true iff val in bst
def get_encoding(node,val):
  if node == None:
    return (None,False)
  elif node.data == val:
    return ([],True)
  else:
    (l_enc,l_found) = get_encoding(node.l,val)
    (r_enc,r_found) = get_encoding(node.r,val)
    if l_found:
      return ([0] + l_enc,True)
    elif r_found:
      return ([1] + r_enc,True)
    else:
      return (None, False)


# Provided an encoding return the value of the data at this location
# if there is no data in this position, or the value equals the data,
# put val here and return None. Also return the updated tree
def _traverse_insert(sgtree,node,encoding,val,depth):
  if encoding == []:

    if node == None:
      sgtree.size += 1
      if (depth > sgtree.balanced_h() ):
        return (True,None,SGNode(val))
      else:
        return (False,None,SGNode(val))
      
    else:
      if val == node.data:
        # Found the value, Tree must still be balanced
        return (False,None,SGNode(val))
      else:
        return (False,node.data,node)


  else:

    if node == None:
      raise ValueError("Encoding points beyond this tree")

    #Search the Left Branch
    elif encoding[0]==0: 
      (unbalanced,data,new_l) = _traverse_insert(sgtree,node.l,encoding[1:],val,depth+1)
      node.l = new_l
      # If insert successful check for rebalancing
      if data == None:
        if unbalanced:
          # Check if this is a scapegoat node
          if is_scapegoat(node):
            return(False,None,rebalance(node))
          return(True,None,node)
      return (False,data,node)

    #Search the Right Branch
    else:
      (unbalanced,data,new_r) = _traverse_insert(sgtree,node.r,encoding[1:],val,depth+1)
      node.r = new_r
      # If insert successful check for rebalancing
      if data == None:
        if unbalanced:
          # Check if this is a scapegoat node
          if is_scapegoat(node):
            return(False,None,rebalance(node))
          return(True,None,node)
      return (False,data,node)

def traverse_insert(sgtree,encoding,val):
  data,new_root = _traverse_insert(sgtree,sgtree.root,encoding,val,0)[1:]
  sgtree.root = new_root
  return data,new_root
