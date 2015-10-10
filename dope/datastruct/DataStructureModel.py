__author__ = 'lauril'

class DatraStructureModel(object):
    '''
    Parent class unifying access to the data structures
    '''
    def __init__(self):
        pass

    def insert(self,bst,val):
        pass

    def search(self,bst,val):
        pass

    def linear_search(self,bst,val):
    	pass

    def get_encoding(self,bst,val):
    	pass

    def traverse_insert(self,bst,encoding,val):
    	pass

class mOPE_encoding(object):
	'''
	Parent class providing interface to all datastructure encodings
	'''
	def __init__(self,encd_list):
		self.encd_list = encd_list

	def cmp(self,other_encoding):
		pass
