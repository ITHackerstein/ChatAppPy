# Chat App

## Description

This is a basic chat app in Python. It can manage a maximum of 255 devices connected and it uses the ```socket``` Python library.
The client part uses the ```curses``` Python library to manage three different windows that are the messages window, the input window and the scrollbar window.

## Required modules
To run the 'client.py' script you must install ```curses``` or if you are on Windows ```windows-curses```.

## Usage

### Server

```
$ python server.py [<address> <port>]
```

The server will be listening at 'address:port'. If you want to kill the server you have to do it manually with 'taskkill' or the Task Manager if you are on Windows or with the 'kill' command if you are on Linux.

### Client

```
$ python client.py [<username> [<address> <port>]]
```

The client will connect to 'address:port'.
Here's what you can do in the client:
- Normal typing: the keys will be typed.
- Up/Down arrow: scroll the messages window.
- Left/Right arrow: move the input cursor.
- Page Up/Down key: reach the top/bottom of the messages list.
- Home/End key: move the input cursor to the far left/far right.

You can type also some commands. Try typing '/help' for a list of commands you can send.