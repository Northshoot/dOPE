__author__ = 'lauril'

class DatraStructureModel(object):
    '''
    Parent class unifying access to the data structures
    '''
    def __init__(self):
        pass


    def insert(self):
        pass

    def search(self):
        pass


class mOPE_encoding(object):
	'''
	Parent class providing interface to all datastructure encodings
	'''
	def __init__(self,encd_list):
		self.encd_list = encd_list

	def cmp(self,other_encoding):
		pass
