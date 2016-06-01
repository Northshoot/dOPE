__author__ = 'lauril & wdaviau'

import random
import sys
from ..parsers import parseNOAAFile


class DataGenerator(object):
    '''
    data generator class
    '''

    def __init__(self, distribution='NOAA_temp', data_file = None,
                 bounds =[ -100, 100], datatype=int ):
        self.distribution = distribution
        self.bounds = bounds
        self.data_type = datatype
        random.seed()
        # For use collecting data from a preloaded timeseries
        self.current = 0
        self.timeseries = []
        self.data_file = data_file
        self.noaa_len = 0
        if (distribution == 'NOAA_temp'):
            self.timeseries = parseNOAAFile(self.data_file, 9)
            self.noaa_len = len(self.timeseries)

    @property
    def is_last(self):
        return self.current == 100

    def get_next(self):
        if self.distribution == 'random':
            if self.is_last:
                return None
            self.current += 1
            return random.randint(self.bounds[0], self.bounds[1])
        elif self.distribution == 'increasing':
            if self.is_last:
                return None
            self.current += 1
            return self.current
        elif self.distribution == 'uniform':
            return random.uniform(self.bounds[0], self.bounds[1])
        elif self.distribution == 'NOAA_temp':
            if self.is_last:
                return None
            else:
                data = self.timeseries[self.current]
                self.current += 1
            return data
        else:
            sys.exit("Only Random and Uniform distributions implemented")



