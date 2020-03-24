import struct
import os
import socket
import threading
from enum import IntEnum
from msgtypes import MsgTypes
from random import randint

HOST, PORT = "localhost", 5555
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected_devices = []

class Device:
	def __init__(self, conn):
		self.conn = conn
		self.username = ""
		self.receive_data_t = threading.Thread(name="receive_data", target=self.receive_data)
		self.receive_data_t.start()

	def receive_data(self):
		while self.conn.fileno() != -1:
			type_ = ord(self.conn.recv(1))

			if type_ == MsgTypes.CloseConnection:
				print("[{}:{}] Connection closed!".format(*self.conn.getpeername()))
				self.conn.close()
			elif type_ == MsgTypes.OpenConnection:
				username_len = ord(self.conn.recv(1))
				username = self.conn.recv(username_len).decode()

				self.username = "%s#%04d" % (username, randint(0, 9999))
				self.conn.sendall(chr(MsgTypes.UsernameSet).encode() + chr(len(self.username)).encode() + self.username.encode())

				print("[{}:{}] Connected with username {}".format(*self.conn.getpeername(), self.username))
			elif type_ == MsgTypes.SendMsg:
				msg = self.conn.recv(1024)
				if not self.username:
					continue

				for device in connected_devices:
					device.conn.sendall(chr(MsgTypes.RecvMsg).encode() + chr(len(self.username)).encode() + self.username.encode() + msg)
			else:
				pass


def get_connections():
	while True:
		conn, addr = sock.accept()
		connected_devices.append(Device(conn))

sock.bind((HOST, PORT))
sock.listen()

print("Listening on {}:{} PID={}".format(HOST, PORT, os.getpid()))

connections_t = threading.Thread(name="get_connections", target=get_connections)
connections_t.start()
