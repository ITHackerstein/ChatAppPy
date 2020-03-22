import struct
import os
import socket
import threading
from enum import IntEnum

"""
Message structure:
| type (1 byte) | [ args ]

-- type = 0 (CloseConnection), args = ['addr']
-- type = 1 (SendMsg), args = ['msg (max 4096 bytes)']

"""

HOST, PORT = 'localhost', 5555
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected_devices = []


class MsgTypes(IntEnum):
	CloseConnection = 0
	SendMsg = 1

class Device:
	def __init__(self, conn):
		self.conn = conn
		self.receive_data_t = threading.Thread(name="receive_data", target=self.receive_data)
		self.receive_data_t.start()

	def receive_data(self):
		while self.conn.fileno() != -1:
			data = self.conn.recv(4097)
			if not data:
				continue

			i = 0
			while i < len(data):
				if data[i] == MsgTypes.CloseConnection:
					print("[{}:{}] Connection closed!".format(*self.conn.getpeername()))
					self.conn.close()
					break
				elif data[i] == MsgTypes.SendMsg:
					i += 1
					msg = data[i:]
					i += len(msg)
					for device in connected_devices:
						if device.conn.getpeername() != self.conn.getpeername() and device.conn.fileno() != -1:
							device.conn.sendall(msg)
				else:
					print("Garbage received from {}: {}".format(self.conn.getpeername(), data))

def get_connections():
	while True:
		conn, addr = sock.accept()
		connected_devices.append(Device(conn))
		print("[{}:{}] Connection opened!".format(*conn.getpeername()))

sock.bind((HOST, PORT))
sock.listen()

print("Listening on {}:{} PID={}".format(HOST, PORT, os.getpid()))

connections_t = threading.Thread(name="get_connections", target=get_connections)
connections_t.start()
