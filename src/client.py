from command import Command
import socket
import questionary


HOST = 'localhost'
PORT = 21

client_socket = None

def menu() -> None:
    answer = questionary.select(
        "Choose menu",
        choices=[
            "Start FTP client",
            ".2.",
            ".3."
        ]).ask()

    match answer:
        case 'Start FTP client':
            start()
        case _:
            print("You choose unknown menu! Program ended!")

def start() -> None:
    global client_socket
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.bind((HOST, PORT))

def send_command(command: Command, arg: str = None) -> None:
    global client_socket
    
    print(f"Sending command: {command} {'with argument: ' + arg if arg is not None else ''}")
    
    full_command = command.name + (arg or '')
    client_socket.sendall(full_command.encode() + b'\r\n')
    
    response = client_socket.recv(1024).decode()
    print(f"Response: {response}")
    return response

def main() -> None:
    menu()

if __name__ == '__main__':
    main()