from colorama import Fore
from command import Command
import os
import select
import socket
import threading
import questionary


HOST = 'localhost'
PORT = 21

server_socket = None
server_running = False


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
            "Start FTP server",
            ".2.",
            ".3."
        ]).ask()

    match answer:
        case 'Start FTP server':
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
    
    while True:
        client_command = client_socket.recv(1024).decode().strip()
        
        print(f"Received command: {client_command}")
        
        command_start = client_command.split()[0]
        
        match command_start:
            case Command.USER.name:
                handle_user_command(client_socket)
            case Command.PASS.name:
                handle_pass_command(client_socket)
            case Command.PASV.name:
                passive_mode()
            case Command.LIST.name:
                listing_directory()
            case Command.RETR.name:
                retrieving_file()
            case Command.QUIT.name:
                close_client_connection(client_socket)
                break
            case _:
                client_socket.sendall(b"502 Command not implemented\r\n")

def handle_user_command(client_socket: socket.socket) -> None:
    client_socket.sendall(b"331 User name okay, need password.")

def handle_pass_command(client_socket: socket.socket) -> None:
    client_socket.sendall(b"230 User logged in, proceed.")

def authenticate() -> None:
    pass

def passive_mode() -> None:
    pass

def listing_directory() -> None:
    pass

def retrieving_file() -> None:
    pass

def uploading_file() -> None:
    pass

def close_client_connection(client_socket: socket.socket) -> None:
    print(f"{Fore.RED}Connection closed with {client_socket.getpeername()}{Fore.RESET}")
    client_socket.sendall(b"221 Good bye.")
    client_socket.close()



def main() -> None:
    menu()

if __name__ == '__main__':
    main()