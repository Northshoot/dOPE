__author__ = 'lauril & wdaviau'

import random
from parsers.parseWeatherData import parseNOAAFile


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
            self.timeseries = parseNOAAFile('parsers/CRNH0203-2015-NY_Ithaca_13_E.txt',10)

    def get_next(self):
        if self.distribution == 'random' :
            return random.randint(self.bounds[0], self.bounds[1])
        elif self.distribution == 'increasing':
            self.current += 1
            return self.current
        elif self.distribution == 'uniform':
            return random.uniform(self.bounds[0], self.bounds[1])
        elif self.distribution == 'NOAA_temp':
            self.current += 1
            return self.timeseries[self.current %  ( len(self.timeseries) -1)]
        else:
            print("Only Random and Uniform distributions implemented")
            return None


