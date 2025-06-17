from enum import Enum

class MessageType(str, Enum):
    JOIN = "join"
    LEAVE = "leave"
    TURN = "turn"
    READY = "ready_to_start"
    WAITING = "waiting"
    MESSAGE = "message"
    ERROR = "error"
    THINKING = "thinking"