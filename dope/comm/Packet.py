__author__ = 'lauril'


class Packet(object):
    '''
    packet object
    '''
    def __init__(self,data,call_type):
        self.call_type = call_type
        self.data = data



