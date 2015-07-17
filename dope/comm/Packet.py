__author__ = 'lauril'


class Packet(object):
    '''
    packet object
    '''

    def __init__(self):
        self.size = 20 #size in bytes
        self.header = ''
        self.data = ''

