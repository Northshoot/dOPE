__author__ = 'lauril & wdaviau'

import random



class DataGenerator(object):
    '''
    data generator class
    '''

    def __init__(self, distribution='random', bounds =[-100, 100], datatype=int):
        self.distribution = distribution
        self.bounds = bounds
        self.data_type = datatype
        random.seed()


    def get_next(self):
        if self.distribution == 'random' and self.data_type == int:
            return random.randint(self.bounds[0],self.bounds[1])
        elif self.distribution == 'uniform' and self.datatype == float:
            return random.uniform(self.bounds[0],self.bounds[1])
        else:
            print("Only Random and Uniform distributions implemented")
            return None


