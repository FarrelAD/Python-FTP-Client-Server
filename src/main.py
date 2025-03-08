import socket
import os
import threading
import random

class FTPServer:
    def __init__(self, host='127.0.0.1', port=21):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"FTP server listening on {self.host}:{self.port}")

    def start(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        logged_in = False
        passive_port = None

        while True:
            command = client_socket.recv(1024).decode().strip()
            if not command:
                break
            print(f"Received command: {command}")
            
            if command.startswith("USER"):
                client_socket.sendall(b"331 Username ok, need password\r\n")
            elif command.startswith("PASS"):
                logged_in = True
                client_socket.sendall(b"230 Login successful\r\n")
            elif command == "PASV":
                if logged_in:
                    passive_port = self._open_passive_port()
                    client_socket.sendall(f"227 Entering Passive Mode (127,0,0,1,{passive_port // 256},{passive_port % 256})\r\n".encode())
                    self._listen_on_passive_port(passive_port)
                else:
                    client_socket.sendall(b"530 Not logged in\r\n")
            elif command == "LIST":
                if logged_in:
                    data_socket = self._connect_passive(passive_port)
                    data_socket.sendall(b"file1.txt\r\nfile2.txt\r\n")
                    data_socket.close()
                    client_socket.sendall(b"150 Here comes the directory listing\r\n")
                    client_socket.sendall(b"226 Directory send OK\r\n")
                else:
                    client_socket.sendall(b"530 Not logged in\r\n")
            elif command.startswith("RETR"):
                filename = command.split(' ')[1]
                if logged_in and os.path.exists(filename):
                    data_socket = self._connect_passive(passive_port)
                    with open(filename, 'rb') as f:
                        data_socket.sendall(f.read())
                    data_socket.close()
                    client_socket.sendall(b"150 Opening data connection\r\n")
                    client_socket.sendall(b"226 Transfer complete\r\n")
                else:
                    client_socket.sendall(b"550 File not found\r\n")
            else:
                client_socket.sendall(b"502 Command not implemented\r\n")

        client_socket.close()

    def _open_passive_port(self):
        return random.randint(1024, 65535)

    def _listen_on_passive_port(self, passive_port):
        """ Listen on the passive port and wait for client connection. """
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.bind(('127.0.0.1', passive_port))
        data_socket.listen(1)
        print(f"Listening on passive port {passive_port}")
        data_socket.accept()

    def _connect_passive(self, passive_port):
        """ Used by the client to connect to the server's passive port. """
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.connect(('127.0.0.1', passive_port))
        return data_socket

if __name__ == '__main__':
    ftp_server = FTPServer()
    ftp_server.start()
