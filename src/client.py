from colorama import Fore
from command import Command
import os
import socket
import questionary


HOST = 'localhost'
PORT = 21

client_socket = None
is_connection_active = False

def menu() -> None:
    while True:
        os.system('clear')
        
        if is_connection_active:
            connection_status = f"{Fore.GREEN}Active {client_socket.getpeername()}{Fore.RESET}"
        else:
            connection_status = Fore.RED + "Not Active" + Fore.RESET
        
        print(f"Connection status: {connection_status}")
        
        answer = questionary.select(
            "Choose menu",
            choices=[
                "Start FTP client",
                "Exit"
            ]).ask()

        match answer:
            case "Start FTP client":
                start()
            case "Exit":
                print(f"{Fore.GREEN}Bye{Fore.RESET}")
                break

def start() -> None:
    global client_socket, is_connection_active
    
    answers = questionary.form(
        input_host=questionary.text("Input server address"),
        input_port=questionary.text("Input server port")
    ).ask()
    
    HOST = answers['input_host']
    PORT = int(answers['input_port'])
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        
        is_connection_active = True
        
        response = client_socket.recv(1024).decode()
        print(f"{Fore.GREEN}Response: {response}{Fore.RESET}")
        
        authenticate_user()
        questionary.press_any_key_to_continue("Press any key to Continue >").ask()
        run_communication()
    except ConnectionRefusedError:
        print(f"{Fore.RED}Error: Server is not available. Please try again later.{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}{Fore.RESET}")
    finally:
        client_socket.close()
        is_connection_active = False
    
    questionary.press_any_key_to_continue("Press any key to Continue >").ask()

def send_command(command: Command, arg: str = '') -> None:
    full_command = f"{command.name} {arg}"
    client_socket.sendall(full_command.encode() + b'\r\n')
    
    response = client_socket.recv(1024).decode()
    print(f"Response: {response}")
    return response

def run_communication() -> None:
    while True:
        os.system('clear')
        
        answer = questionary.select(
            "Choose command",
            choices=[
                "Send file",
                "Print working directory",
                "Change working directory",
                "List files and directories",
                "Create directory",
                "Remove directory",
                "Download file from the server",
                "Upload file to the server"
                "Delete file",
                "Exit"
            ]
        ).ask()
        
        match answer:
            case "Exit":
                close_connection()
                break

def authenticate_user() -> None:
    answers = questionary.form(
        input_username=questionary.text("Input username"),
        input_password=questionary.text("Input password")
    ).ask()
    
    send_command(Command.USER, answers['input_username'])
    send_command(Command.PASS, answers['input_password'])

def close_connection() -> None:
    send_command(Command.QUIT)

def main() -> None:
    menu()

if __name__ == '__main__':
    main()