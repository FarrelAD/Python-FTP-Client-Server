from enum import Enum

class Command(Enum):
    USER = "USER"
    PASS = "PASS"
    PASV = "PASV"
    PWD  = "PWD"
    LIST = "LIST"
    RETR = "RETR"
    QUIT = "QUIT"