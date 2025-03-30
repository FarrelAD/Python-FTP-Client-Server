from colorama import Fore
from command import Command
import os
import platform
import random
import select
import socket
import stat
import threading
import time
from typing import Tuple
import questionary

if platform.system() == "Windows":
    import win32security # type: ignore

    def get_username(full_path: str) -> str:
        try:
            sid = win32security.GetFileSecurity(full_path, win32security.OWNER_SECURITY_INFORMATION).GetSecurityDescriptorOwner()
            return win32security.LookupAccountSid(None, sid)[0].ljust(10)
        except:
            return "UNKNOWN   "
    
    def get_group_name(full_path: str) -> str:
        try:
            sid = win32security.GetFileSecurity(full_path, win32security.GROUP_SECURITY_INFORMATION).GetSecurityDescriptorGroup()
            return win32security.LookupAccountSid(None, sid)[0].ljust(10)
        except:
            return "UNKNOWN   "
else:
    import grp
    import pwd
    
    def get_username(uid) -> str:
        return pwd.getpwuid(uid).pw_name.ljust(10)
    
    def get_group_name(gid) -> str:
        return grp.getgrgid(gid).gr_name.ljust(10)


HOST = '0.0.0.0'
PORT = 21

MAX_BUFFER_SIZE_CONTROL = 1024
MAX_BUFFER_SIZE_DATA    = 4096

AUTHORIZED_USER = {
    "karl": "karl123",
    "rose": "rose666"
}
MAX_ATTEMPTS_LOGIN = 3

CURRENT_DIR = os.getcwd()

server_socket = None
server_running = False

data_conn = None


def get_local_ip() -> str:
    """Returns the local IP address of the server."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


def user_input_listener() -> None:
    global server_running, server_socket
    
    while True:
        try:
            user_input = input()
            if user_input.lower() == 'h':
                print("Help Menu:\n- Press 'h' for help\n- Press 'q' to quit")
        except EOFError:
            break


def menu() -> None:
    answer = questionary.select(
        "Choose menu",
        choices=[
            "1. Start FTP server",
            "2. Exit"
        ]).ask()

    match answer:
        case "1. Start FTP server":
            start()
        case _:
            print("You choose unknown menu! Program ended!")

def start():
    global server_running, server_socket
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
        
    print(f"FTP server listening on {HOST}:{PORT}\n")
    
    server_running = True
    input_thread = threading.Thread(target=user_input_listener, daemon=True)
    input_thread.start()
    
    try:
        while True:
            readable, _, _ = select.select([server_socket], [], [], 1)
            if server_socket in readable:
                client_socket, addr = server_socket.accept()
                print(f"Connection from {addr}")
                
                handle_client(client_socket)
    except KeyboardInterrupt:
        print("\nServer is shutting down gracefully...")
        server_running = False
    finally:
        server_socket.close()
        
def handle_client(client_socket: socket.socket) -> None:
    client_socket.sendall(b"220 Service ready for new user.\r\n")
    
    username = None
    
    attempts_login = 0
    while True:
        if client_socket.fileno() == -1:
            print(f"{Fore.RED}Connection already closed!{Fore.RESET}")
            break
        
        client_request = client_socket.recv(MAX_BUFFER_SIZE_CONTROL)
        client_command = client_request.decode().strip()
        
        print(f"Received command: {client_command}")
        command_start, command_arg = (client_command.split(maxsplit=1) + [""])[:2]
        
        match command_start:
            case Command.USER.name:
                username, attempts_login = handle_user_command(client_socket, command_arg, attempts_login)
            case Command.PASS.name:
                handle_pass_command(client_socket, username, command_arg)
            case Command.PASV.name:
                handle_pasv_command(client_socket)
            case Command.PWD.name:
                handle_pwd_command(client_socket)
            case Command.LIST.name:
                handle_list_command(client_socket)
            case Command.RETR.name:
                handle_retr_command(client_socket, command_arg)
            case Command.QUIT.name:
                handle_quit_command(client_socket)
                break
            case _:
                client_socket.sendall(b"502 Command not implemented\r\n")

def handle_user_command(client_socket: socket.socket, input_username: str, attempts_login: int) -> Tuple[str | None, int]:
    attempts_login += 1
    
    if attempts_login > MAX_ATTEMPTS_LOGIN:
        client_socket.sendall(b"421 Too many failed login attempts. Connection closed.\r\n")
        client_socket.close()
        return None, attempts_login
    
    if input_username in AUTHORIZED_USER:
        response = "331 User name okay, need password.\r\n"
        username = input_username
    else:
        response = "530 Invalid username.\r\n"
        username = None
    client_socket.sendall(response.encode())
    
    return username, attempts_login

def handle_pass_command(client_socket: socket.socket, username: str, input_password: str) -> None:
    if username is None:
        client_socket.sendall(b"530 No username provided.\r\n")
        return
        
    if AUTHORIZED_USER[username] == input_password:
        response = "230 User logged in, proceed.\r\n"
    else:
        response = "530 Incorrect password.\r\n"
    client_socket.sendall(response.encode())

def handle_pasv_command(client_socket: socket.socket) -> None:
    global data_conn
    
    DATA_PORT = random.randint(49512, 65535)
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.bind((HOST, DATA_PORT))
    data_socket.listen(1)
    
    response = get_pasv_response(get_local_ip(), DATA_PORT)
    client_socket.sendall(response.encode())
    
    data_conn, data_addr = data_socket.accept()
    print(f"Data connection established with {data_addr}")
    
def get_pasv_response(ip: str, port: int) -> str:
    """Format the PASV response with the IP and port"""
    p1, p2 = port // 256, port % 256
    ip_parts = ip.split(".")
    return f"227 Entering Passive Mode ({','.join(ip_parts)},{p1},{p2})\r\n"

def handle_pwd_command(client_socket: socket.socket) -> None:
    response = f"257 {CURRENT_DIR} is current directory\r\n"
    client_socket.sendall(response.encode())

def handle_list_command(client_socket: socket.socket) -> None:
    print("Client requested directory listing.")
    
    items = os.listdir(CURRENT_DIR)
    result = []

    for item in items:
        full_path = os.path.join(CURRENT_DIR, item)
        file_stat = os.stat(full_path)

        permissions = stat.filemode(file_stat.st_mode)
        num_links = str(file_stat.st_nlink).rjust(3)

        if platform.system() == "Windows":
            owner = get_username(full_path)
            group = get_group_name(full_path)
        else:
            owner = get_username(file_stat.st_uid)
            group = get_group_name(file_stat.st_gid)

        file_size = str(file_stat.st_size).rjust(10)
        last_modified = time.strftime("%b %d %H:%M", time.localtime(file_stat.st_mtime)).rjust(12)
        filename = item.ljust(20)

        result.append(f"{permissions} {num_links} {owner} {group} {file_size} {last_modified} {filename}")
    
    string_result = "\r\n".join(result) + "\r\n"
    
    client_socket.sendall(b"150 Opening data connection\r\n")
    data_conn.sendall(string_result.encode())
    
    data_conn.close()
    client_socket.sendall(b"226 Closing data connection\r\n")

def handle_retr_command(client_socket: socket.socket, filename: str) -> None:
    print("The client requested to retrieve the file.")
    
    if os.path.isfile(f"{CURRENT_DIR}+/{filename}"):
        client_socket.sendall(b"550 File not found or access denied.\r\n")
        return
    
    try:
        client_socket.send(b"150 Opening data connection for file transfer.\r\n")

        with open(filename, "rb") as file:
            while chunk := file.read(MAX_BUFFER_SIZE_DATA):
                data_conn.sendall(chunk)

        data_conn.close()

        client_socket.sendall(b"226 Transfer complete.\r\n")
    except Exception as e:
        client_socket.sendall(b"550 File transfer failed.\r\n")
        print(f"Error sending file: {e}")

def uploading_file() -> None:
    pass

def handle_quit_command(client_socket: socket.socket) -> None:
    print(f"{Fore.RED}Connection closed with {client_socket.getpeername()}{Fore.RESET}")
    client_socket.sendall(b"221 Good bye.")
    client_socket.close()



def main() -> None:
    menu()

if __name__ == '__main__':
    main()