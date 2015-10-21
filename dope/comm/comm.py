__author__ = 'lauril'
from .packet import Packet


class Communicator(object):
    '''
    Communicator containing bidirectional communication channel(s) with other communicators
    '''

    def __init__(self):
        self.sent = None
        self.received = None
        return

    # Connect comm to this communicator object for bidirectional communication (source & destination)
    def connect(self, comm):
        self.connected_comm = comm
        return

    # Return true if channel is free and packet is sent, False if channel is busy
    def send(self, data, call_type):
        packet = Packet(data, call_type)
        if self.sent:
            return False
        self.sent = packet
        self.connected_comm.received = packet
        return True

    def read(self):
        if not self.received:
            return None
        else:
            packet = self.received
            self.received = None
            self.connected_comm.sent = None
            return packet
