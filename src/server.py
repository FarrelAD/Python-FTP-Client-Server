import questionary
import os
import select
import socket
import threading


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
    command = client_socket.recv(1024).decode().strip()
    
    print(f"Received command: {command}")

def main() -> None:
    menu()

if __name__ == '__main__':
    main()