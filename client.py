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

messages_w = curses.newpad(theight, twidth - 1)
input_w = curses.newpad(1, twidth)
scrollbar_w = curses.newwin(theight - 1, 1, 0, twidth - 1)

input_w.keypad(True)
input_w.bkgdset(" ", curses.A_REVERSE)
input_w.clrtoeol()
curses.noecho()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

HELP_MSG = """This is the list of commands available:
-- /users: returns the number of users connected.
-- /userslist: returns a list of the users connected.
"""

scroll_amt = 0
max_scroll_amt = 0

def clamp(n, min_, max_):
	return max(min(n, max_), min_)

def send_username(username):
	sock.sendall(chr(MsgTypes.OpenConnection).encode() + chr(len(username)).encode() + username.encode())
	type_ = ord(sock.recv(1))
	assert type_ == MsgTypes.UsernameSet
	size = ord(sock.recv(1))
	final = sock.recv(size)
	return final.decode()

def refresh_messages():
	global scroll_amt
	global max_scroll_amt

	sh = scrollbar_w.getmaxyx()[0]
	if max_scroll_amt == 0:
		start = 1
		count = sh - 2
	else:
		count = clamp(round((sh - 2) * sh / messages_w.getyx()[0]), 1, sh - 2)
		start = clamp(round((sh - count - 2) / max_scroll_amt * scroll_amt + 1), 1, sh - 1)

	scrollbar_w.move(0, 0)
	scrollbar_w.clrtobot()
	scrollbar_w.addstr(start - 1, 0, "\u25b2")
	scrollbar_w.addstr(start, 0, "\u2591" * count, curses.A_REVERSE)
	scrollbar_w.insstr(start + count, 0, "\u25bc")
	scrollbar_w.refresh()
	messages_w.refresh(scroll_amt, 0, 0, 0, theight - 2, twidth - 2)

def readline(prompt=""):
	global scroll_amt
	global max_scroll_amt

	input_w.move(0, 0)
	input_w.clrtoeol()
	input_w.addstr(0, 0, prompt)
	input_w.refresh(0, 0, theight - 1, 0, theight - 1, twidth - 1)

	line = []
	cursor_position = 0
	hscroll = 0
	while True:
		c = input_w.getkey()
		if c == '\n':
			break

		old_cp = input_w.getyx()[1]

		if c == '\x08': # Backspace
			if len(line) > 0 and cursor_position > 0:
				line.pop(cursor_position - 1)
				input_w.delch(0, input_w.getyx()[1] - 1)
				cursor_position -= 1
		elif c == "KEY_B1" or c == "KEY_LEFT": # Left Arrow
			if cursor_position > 0:
				cursor_position -= 1
				input_w.move(0, input_w.getyx()[1] - 1)
		elif c == "KEY_A2" or c == "KEY_UP": # Up Arrow
			if scroll_amt > 0:
				scroll_amt -= 1
				refresh_messages()
		elif c == "KEY_B3" or c == "KEY_RIGHT": # Right Arrow
			if cursor_position < len(line):
				cursor_position += 1
				input_w.move(0, input_w.getyx()[1] + 1)
		elif c == "KEY_C2" or c == "KEY_DOWN": # Down Arrow
			if scroll_amt < max_scroll_amt:
				scroll_amt += 1
				refresh_messages()
		elif c == "KEY_A3" or c == "KEY_PPAGE": # Page Up
			scroll_amt = 0
			refresh_messages()
		elif c == "KEY_C3" or c == "KEY_NPAGE": # Pade Down
			scroll_amt = max_scroll_amt
			refresh_messages()
		elif len(c) > 1:
			continue
		elif ord(c) not in range(32, 127):
			continue
		else:
			cp = input_w.getyx()[1]
			size = input_w.getmaxyx()[1]
			if cp + len(line) - cursor_position + 1 >= size:
				input_w.resize(1, size + twidth)

			input_w.insch(c)
			print(cp + len(line) - cursor_position + 1)
			input_w.move(0, cp + len(line) - cursor_position + 1)
			input_w.clrtoeol()
			input_w.move(0, cp + 1)

			line.insert(cursor_position, c)
			cursor_position += 1

		new_cp = input_w.getyx()[1]

		diff = new_cp // twidth - old_cp // twidth

		if diff < 0:
			hscroll -= 1
		elif diff > 0:
			hscroll += 1

		input_w.refresh(0, hscroll * twidth, theight - 1, 0, theight - 1, twidth - 1)

	return "".join(line)

def _draw_message(from_, body):
	global scroll_amt
	global max_scroll_amt

	messages_w.addstr("%s [ " % (time.strftime("%H:%M:%S")))
	attr = curses.color_pair(0)
	if from_ == my_username:
		attr = curses.color_pair(1)
	messages_w.addstr(from_, attr)
	messages_w.addstr(" ] %s\n" % (body))

	max_scroll_amt = 0
	scroll_amt = 0
	cy = messages_w.getyx()[0]
	if cy > theight - 1:
		max_scroll_amt = cy - theight + 1
		scroll_amt = cy - theight + 1

	refresh_messages()

def _draw_system_message(type_, body):
	global scroll_amt
	global max_scroll_amt

	messages_w.addstr(time.strftime("%H:%M:%S") + " ")
	attr = curses.color_pair(0)
	if type_ == "Error":
		attr = curses.color_pair(1)
	elif type_ == "Info":
		attr = curses.color_pair(2)
	elif type_ == "CmdOutput":
		attr = curses.color_pair(3)
	messages_w.addstr(body, attr)

	max_scroll_amt = 0
	scroll_amt = 0
	cy = messages_w.getyx()[0]
	if cy > theight - 1:
		max_scroll_amt = cy - theight + 1
		scroll_amt = cy - theight + 1

	refresh_messages()

def draw_message(from_, body):
	while True:
		try:
			_draw_message(from_, body)
			break
		except:
			old_size = messages_w.getmaxyx()
			messages_w.resize(old_size[0] + 1, old_size[1])
			old_cursor = messages_w.getyx()[0]
			messages_w.move(old_cursor, 0)

def draw_system_message(type_, body):
	while True:
		try:
			_draw_system_message(type_, body)
			break
		except:
			old_size = messages_w.getmaxyx()
			messages_w.resize(old_size[0] + 1, old_size[1])
			old_cursor = messages_w.getyx()[0]
			messages_.w.move(old_cursor, 0)

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
	global scroll_amt

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
	elif cmd == "clear":
		messages_w.move(0, 0)
		messages_w.clear()
		draw_system_message("CmdOutput", "Chat cleared!\n")
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
