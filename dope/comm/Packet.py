__author__ = 'lauril'


class Packet(object):
    '''
    packet object
    '''
    def __init__(self, data , call_type):
        self.call_type = call_type
        self.data = data

    def __str__(self):
        return self.call_type + ": " + str(self.data)



