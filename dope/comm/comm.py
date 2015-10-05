__author__ = 'lauril'

from packet import Packet


class Communicator(object):
	'''
	Communicator containing bidirectional communication channel(s) with other communicators
	'''
	def __init__(self):
		self.sent = None
		self.received = None
		return

	# Connect comm to this communicator object for bidirectional communication (source & destination)	
	def connect(self,comm):
		self.connected_comm = comm
		return

	def send(self, data, call_type):
		packet = Packet(data,call_type)
		if self.transmitted != None:
			print("Communication channel is busy")
			return
		self.transmitted = packet
		self.connected_comm.received = packet
		return

	def read(self):
		if self.received == None:
			print("Communication channel is empty")
			return None
		else:
			packet = self.received
			self.received = None
			self.connected_comm.transmitted = None
			return packet







