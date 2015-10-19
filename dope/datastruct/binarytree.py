__author__ = 'lauril'
# Pretty printing from steve krenzel http://stevekrenzel.com/articles/printing-trees


class BSTree:
	def __init__(self,val):
		# None stands in for empty leaves
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


###############################################################
# These are the expected insert and search functions when the #
# values are comparable by the caller                         #
###############################################################

def insert(bst,val):
	if bst is None:
		 return Tree(val)
	else:
		if bst.data > val:
			new_l = insert(bst.l,val)
			bst.l = new_l
			return bst
		elif bst.data < val:
			new_r = insert(bst.r,val)
			bst.r = new_r
			return bst
		else:
			return bst


def search(bst,val):
	if bst is None:
		return False
	elif bst.data == val:
		return True
	elif bst.data > val:
		return search(bst.l,val)
	elif bst.data < val:
		return search(bst.r,val)



def size_tree(bst):
  if bst is None:
    return 0
  else:
    return size_tree(bst.r)+size_tree(bst.l)+1



##############################################################
# These functions define an API for use by a server to insert# 
# on and compare values in a  mOPE ciphertext tree 		     #
##############################################################


# Pre-order search of bst
def linear_search(bst,val):
	if bst is None:
		return False
	elif bst.data == val:
		return True 
	elif linear_search(bst.l,val):
		return True
	elif linear_search(bst.r,val):
		return True
	else:
		return False

# return the (enc,found). e is the mOPE encoding as a list of 1s and 0s
# this is None if there is no encoding.  Found is true iff val in bst
def get_encoding(bst,val):
	if bst is None:
		return (None,False)
	elif bst.data == val:
		return ([],True)
	else:
		(l_enc,l_found) = get_encoding(bst.l,val)
		(r_enc,r_found) = get_encoding(bst.r,val)
		if l_found:
			return ([0] + l_enc,True)
		elif r_found:
			return ([1] + r_enc,True)
		else:
			return (None, False)

# Provided an encoding return the value of the data at this location
# if there is no data in this position, or the value equals the data,
# put val here and return None. Also return the updated tree
def traverse_insert(bst,encoding,val):
	if encoding == []:
		if bst is None:
			return(None,BSTree(val))
		else:
			if val == bst.data:
				# Found the value
				return (None,bst)
			else:
				return (bst.data, bst)
	else:
		if bst is None:
			raise ValueError("Encoding points beyond this tree")
		elif encoding[0]==0: 
			# search left branch
			(data,new_l) = traverse_insert(bst.l,encoding[1:],val)
			bst.l = new_l
			return (data,bst)
		else:
			# search the right branch
			(data,new_r) = traverse_insert(bst.r,encoding[1:],val)
			bst.r = new_r
			return (data,bst)




