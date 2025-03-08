import socket

class FTPClient:
    def __init__(self, host='127.0.0.1', port=21):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

    def send_command(self, command):
        print(f"Sending command: {command}")
        self.client_socket.sendall(command.encode() + b'\r\n')
        response = self.client_socket.recv(1024).decode()
        print(f"Response: {response}")
        return response

    def login(self, username, password):
        self.send_command(f"USER {username}")
        self.send_command(f"PASS {password}")

    def enter_passive_mode(self):
        response = self.send_command("PASV")
        if "227" in response:
            passive_port = self._parse_passive_port(response)
            print(f"Passive mode entered. Using port {passive_port}")
            return passive_port
        else:
            return None

    def _parse_passive_port(self, response):
        parts = response.split('(')[1].split(')')[0].split(',')
        return int(parts[4]) * 256 + int(parts[5])

    def list_files(self, passive_port):
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.connect(('127.0.0.1', passive_port))
        self.send_command("LIST")
        data = data_socket.recv(1024).decode()
        print("Files on server:")
        print(data)
        data_socket.close()

    def retrieve_file(self, filename, passive_port):
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.connect(('127.0.0.1', passive_port))
        self.send_command(f"RETR {filename}")
        with open(f"downloaded_{filename}", 'wb') as f:
            data = data_socket.recv(1024)
            while data:
                f.write(data)
                data = data_socket.recv(1024)
        print(f"File {filename} downloaded successfully.")
        data_socket.close()

if __name__ == '__main__':
    ftp_client = FTPClient()

    ftp_client.login("user", "password")

    passive_port = ftp_client.enter_passive_mode()
    if passive_port:
        ftp_client.list_files(passive_port)

        ftp_client.retrieve_file("index.php", passive_port)
    else:
        print('Something wrong!')
