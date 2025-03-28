from enum import Enum

class Command(Enum):
    USER = "USER"
    PASS = "PASS"
    PASV = "PASV"
    LIST = "LIST"
    RETR = "RETR"
    QUIT = "QUIT"