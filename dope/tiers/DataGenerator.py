__author__ = 'lauril & wdaviau'

import random
from ..parsers import parseNOAAFile


class DataGenerator(object):
    '''
    data generator class
    '''

    def __init__(self, distribution='NOAA_temp', bounds =[-100, 100], datatype=int):
        self.distribution = distribution
        self.bounds = bounds
        self.data_type = datatype
        random.seed()
        # For use collecting data from a preloaded timeseries
        self.current = 0
        self.timeseries = []
        if (distribution == 'NOAA_temp'):
            self.timeseries = parseNOAAFile('parsers/CRNS0101-05-2008-KY_' + 
                                            'Bowling_Green_21_NNE.txt', 9)

    def get_next(self):
        if self.distribution == 'random' :
            self.current += 1
            if self.current == 1001:
                return -9999
            return random.randint(self.bounds[0], self.bounds[1])
        elif self.distribution == 'increasing':
            self.current += 1
            if self.current == 1001:
                return -9999
            return self.current
        elif self.distribution == 'uniform':
            return random.uniform(self.bounds[0], self.bounds[1])
        elif self.distribution == 'NOAA_temp':
            #add reading new file if the old is over
            self.current += 1
            return self.timeseries[self.current %  ( len(self.timeseries) -1)]
        else:
            print("Only Random and Uniform distributions implemented")
            return None


