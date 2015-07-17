__author__ = 'lauril'


class DataGenerator(object):
    '''
    data generator class
    '''

    def __init__(self, distribution='random', range=[-100, 100], datatype=int):
        self.distribution = distribution
        self.range = range
        self.data_type = datatype


    def get_next(self):
        '''
        return the next value
        :return:
        '''
        pass

    def get_random(self):
        pass

    def get_uniform(self):
        pass
