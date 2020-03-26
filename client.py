import os
import sys
import struct
import threading
import socket
import curses
import time
from enum import IntEnum
from msgtypes import MsgTypes

my_username = sys.argv[1] if len(sys.argv) >= 2 else input("Enter your username: ")
HOST = sys.argv[2] if len(sys.argv) >= 4 else input("Enter the address of the server: ")
PORT = int(sys.argv[3]) if len(sys.argv) >= 4 else int(input("Enter the port of the server: "))

curses.initscr()
curses.start_color()

curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)

twidth, theight = os.get_terminal_size()

messages_w = curses.newpad(theight * 4, twidth)
input_w = curses.newwin(1, twidth, theight - 1, 0)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

HELP_MSG = """This is the list of commands available:
-- /users: returns the number of users connected.
-- /userslist: returns a list of the users connected.
"""

scroll_amt = 0

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

def draw_message(from_, body):
	global scroll_amt

	messages_w.addstr("%s [ " % (time.strftime("%H:%M:%S")))
	attr = curses.color_pair(0)
	if from_ == my_username:
		attr = curses.color_pair(1)
	messages_w.addstr(from_, attr)
	messages_w.addstr(" ] %s\n" % (body))

	cy = messages_w.getyx()[0]

	if cy > theight - 1:
		scroll_amt = cy - theight + 1

	messages_w.refresh(scroll_amt, 0, 0, 0, theight - 2, twidth - 1)

def draw_system_message(type_, body):
	global scroll_amt

	messages_w.addstr(time.strftime("%H:%M:%S") + " ")
	attr = curses.color_pair(0)
	if type_ == "Error":
		attr = curses.color_pair(1)
	elif type_ == "Info":
		attr = curses.color_pair(2)
	elif type_ == "CmdOutput":
		attr = curses.color_pair(3)
	messages_w.addstr(body, attr)

	cy = messages_w.getyx()[0]
	if cy > theight - 1:
		scroll_amt = cy - theight + 1

	messages_w.refresh(scroll_amt, 0, 0, 0, theight - 2, twidth - 1)

def receive_msg():
	while True:
		type_ = ord(sock.recv(1))

		if type_ == MsgTypes.RecvMsg:
			username_len = ord(sock.recv(1))
			username = sock.recv(username_len).decode()

			msg = sock.recv(1024).decode()
			draw_message(username, msg)
		elif type_ == MsgTypes.Notification:
			content_len = struct.unpack("H", sock.recv(2))[0]
			content = sock.recv(content_len).decode()

			draw_system_message("Info", content)
		elif type_ == MsgTypes.CmdOutput:
			cmd_type_size = ord(sock.recv(1))
			cmd_type = sock.recv(cmd_type_size).decode()

			if cmd_type == "NUsers":
				n_users = ord(sock.recv(1))
				draw_system_message("CmdOutput", "%d / 255 users connected.\n" % (n_users))
			elif cmd_type == "UsersList":
				n_users = ord(sock.recv(1))

				msg_body = "List of users connected: \n"

				for i in range(n_users):
					username_size = ord(sock.recv(1))
					username = sock.recv(username_size).decode()

					msg_body += "- %s\n" % (username)
				draw_system_message("CmdOutput", msg_body)
		else:
			continue

def parse_command(cmd):
	if cmd == "quit":
		sock.sendall(chr(MsgTypes.CloseConnection).encode())
		sys.exit(0)
	elif cmd == "users":
		cmd_type = "NUsers"
		cmd_len = chr(len(cmd_type)).encode()
		sock.sendall(chr(MsgTypes.SendCmd).encode() + cmd_len + cmd_type.encode())
	elif cmd == "userslist":
		cmd_type = "UsersList"
		cmd_len = chr(len(cmd_type)).encode()
		sock.sendall(chr(MsgTypes.SendCmd).encode() + cmd_len + cmd_type.encode())
	elif cmd == "help":
		draw_system_message("CmdOutput", HELP_MSG)
	else:
		body = "'%s' is not a valid command! Type '/help' for a list\n" % (cmd)
		draw_system_message("Error", body)

sock.connect((HOST, PORT))
my_username = send_username(my_username)

receive_msg_t = threading.Thread(name="receive_msg", target=receive_msg)
receive_msg_t.start()

while True:
	msg = readline(" %s > " % (my_username))
	if not msg:
		continue

	if msg[0] == '/':
		parse_command(msg[1:])
	else:
		sock.sendall(chr(MsgTypes.SendMsg).encode() + msg.encode())
