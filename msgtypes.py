from enum import IntEnum

"""
Message structure:
| type (1 byte) | [ args ]

-- type = 0 (CloseConnection)
-- type = 1 (OpenConnection), args = ['username: (1 byte 'size', 'size' bytes username)]
-- type = 2 (UsernameSet), args = ['username: (1 byte 'size', 'size' bytes username)]
-- type = 3 (SendMsg), args = ['msg (max 1024 bytes)']
-- type = 4 (RecvMsg), args = ['username: (1 byte 'size', 'size' bytes username)', 'msg (max 1024 bytes)']
-- type = 5 (Notification), args = ['content: (2 byte 'size', 'size' content)']

"""

class MsgTypes(IntEnum):
	CloseConnection = 0
	OpenConnection = 1
	UsernameSet = 2
	SendMsg = 3
	RecvMsg = 4
	Notification = 5
