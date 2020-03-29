import os
import sys
import struct
import socket
import threading
from enum import IntEnum
from msgtypes import MsgTypes
from random import randint

MAX_DEVICES = 255

if len(sys.argv) >= 3:
	HOST = sys.argv[1]
	try:
		PORT = int(sys.argv[2])
	except:
		print("Invalid port '%s'!" % (sys.argv[2]))
		sys.exit(1)
else:
	HOST = input("Enter the address: ")
	while True:
		try:
			PORT = int(input("Enter the port: "))
			break
		except:
			print("Invalid port!")


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected_devices = []
n_devices = 0

class Device:
	def __init__(self, conn):
		self.conn = conn
		self.username = ""
		self.connected = True
		self.receive_data_t = threading.Thread(name="receive_data", target=self.receive_data)
		self.receive_data_t.start()

	def receive_data(self):
		global n_devices

		while self.connected:
			type_ = ord(self.conn.recv(1))

			if type_ == MsgTypes.CloseConnection:
				self.connected = False
				print("[{}:{}] Connection closed!".format(*self.conn.getpeername()))
				self.conn.close()


				for device in connected_devices:
					if not device.connected:
						continue

					content = "%s left the chat!\n" % (self.username)
					packed_length = struct.pack("H", len(content))
					device.conn.sendall(chr(MsgTypes.Notification).encode() + packed_length + content.encode())
					n_devices -= 1
			elif type_ == MsgTypes.OpenConnection:
				username_len = ord(self.conn.recv(1))
				username = self.conn.recv(username_len).decode()

				self.username = "%s#%04d" % (username, randint(0, 9999))
				self.connected = True
				self.conn.sendall(chr(MsgTypes.UsernameSet).encode() + chr(len(self.username)).encode() + self.username.encode())
				for device in connected_devices:
					if not device.connected:
						continue

					content = "%s joined the chat!\n" % (self.username)
					packed_length = struct.pack("H", len(content))
					device.conn.sendall(chr(MsgTypes.Notification).encode() + packed_length + content.encode())

				print("[{}:{}] Connected with username {}".format(*self.conn.getpeername(), self.username))
				n_devices += 1
			elif type_ == MsgTypes.SendMsg:
				msg = self.conn.recv(1024)
				if not self.username:
					continue

				for device in connected_devices:
					if device.connected:
						device.conn.sendall(chr(MsgTypes.RecvMsg).encode() + chr(len(self.username)).encode() + self.username.encode() + msg)
			elif type_ == MsgTypes.SendCmd:
				cmd_size = ord(self.conn.recv(1))
				cmd = self.conn.recv(cmd_size).decode()

				if cmd == "NUsers":
					self.conn.sendall(chr(MsgTypes.CmdOutput).encode() + chr(cmd_size).encode() + cmd.encode() + chr(n_devices).encode())
				elif cmd == "UsersList":
					msg = b""
					for device in connected_devices:
						if not device.connected:
							continue

						msg += chr(len(device.username)).encode()
						msg += device.username.encode()
					self.conn.sendall(chr(MsgTypes.CmdOutput).encode() + chr(cmd_size).encode() + cmd.encode() + chr(n_devices).encode() + msg)
			else:
				pass


def get_connections():
	while True:
		conn, addr = sock.accept()
		if n_devices >= MAX_DEVICES:
			conn.close()
		connected_devices.append(Device(conn))

sock.bind((HOST, PORT))
sock.listen()

print("Listening on {}:{} PID={}".format(HOST, PORT, os.getpid()))

connections_t = threading.Thread(name="get_connections", target=get_connections)
connections_t.start()
