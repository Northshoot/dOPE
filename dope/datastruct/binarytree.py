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
	if bst == None:
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
	if bst == None:
		return False
	elif bst.data == val:
		return True
	elif bst.data > val:
		return search(bst.l,val)
	elif bst.data < val:
		return search(bst.r,val)


##############################################################
# These functions define an API for use by a server to insert# 
# on and compare values in a  mOPE ciphertext tree 		     #
##############################################################


# Pre-order search of bst
def linear_search(bst,val):
	if bst == None:
		return False
	elif bst.data == val:
		return True 
	elif linear_search(bst.l,val):
		return True
	elif linear_search(bst.r,val):
		return True
	else:
		return False

# return the mOPE encoding as a list of 1s and 0s
# return None if there is no encoding
def get_encoding(bst,val):

