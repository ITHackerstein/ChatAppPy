from enum import IntEnum


class MsgTypes(IntEnum):
	CloseConnection = 0
	OpenConnection = 1
	UsernameSet = 2
	SendMsg = 3
	RecvMsg = 4
