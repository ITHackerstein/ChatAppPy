import os
import sys
import threading
import socket
import curses
from enum import IntEnum
from msgtypes import MsgTypes

my_username = sys.argv[1] if len(sys.argv) >= 2 else input("Enter your username: ")
HOST = sys.argv[2] if len(sys.argv) >= 4 else input("Enter the address of the server: ")
PORT = int(sys.argv[3]) if len(sys.argv) >= 4 else int(input("Enter the port of the server: "))

curses.initscr()
curses.start_color()

curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

twidth, theight = os.get_terminal_size()

messages_w = curses.newwin(theight - 1, twidth, 0, 0)
input_w = curses.newwin(1, twidth, theight - 1, 0)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

messages = []

def send_username(username):
	sock.sendall(chr(MsgTypes.OpenConnection).encode() + chr(len(username)).encode() + username.encode())
	type_ = ord(sock.recv(1))
	assert type_ == MsgTypes.UsernameSet
	size = ord(sock.recv(1))
	final = sock.recv(size)
	return final.decode()

def readline(prompt=""):
	input_w.attron(curses.A_REVERSE)

	input_w.addstr(0, 0, " " * (twidth - 1))

	input_w.addstr(0, 0, prompt)
	input_w.refresh()

	line = input_w.getstr()

	input_w.clrtoeol()
	input_w.refresh()

	input_w.attroff(curses.A_REVERSE)
	return line.decode()

class Message:
	def __init__(self, from_, body):
		self.from_ = from_
		self.body = body

class SystemMessage:
	def __init__(self, type_, body):
		self.type_ = type_
		self.body = body

def print_messages():
	messages_w.move(0, 0)
	messages_w.clear()
	for i, msg in enumerate(messages):
		if type(msg) == SystemMessage:
			if msg.type_ == "Error":
				messages_w.attron(curses.color_pair(1))
				messages_w.addstr(msg.body + "\n")
				messages_w.attroff(curses.color_pair(1))
				continue


		messages_w.addstr("[ ")
		messages_w.attron(curses.color_pair(1))
		messages_w.addstr(msg.from_)
		messages_w.attroff(curses.color_pair(1))
		messages_w.addstr(" ] %s\n" % (msg.body))

		messages_w.refresh()

def receive_msg():
	while True:
		type_ = ord(sock.recv(1))

		if type_ == MsgTypes.RecvMsg:
			username_len = ord(sock.recv(1))
			username = sock.recv(username_len).decode()

			msg = sock.recv(1024).decode()
			messages.append(Message(username, msg))
			print_messages()

def parse_command(cmd):
	if cmd == "quit":
		sock.sendall(chr(MsgTypes.CloseConnection).encode())
		sys.exit(0)
	else:
		body = "'%s' is not a valid command! Type '/help' for a list" % (cmd)
		messages.append(SystemMessage("Error", body))
		print_messages()

		messages_w.refresh()

sock.connect((HOST, PORT))
my_username = send_username(my_username)

receive_msg_t = threading.Thread(name="receive_msg", target=receive_msg)
receive_msg_t.start()

while True:
	msg = readline(" %s > " % (my_username))
	if msg[0] == '/':
		parse_command(msg[1:])
	else:
		sock.sendall(chr(MsgTypes.SendMsg).encode() + msg.encode())
