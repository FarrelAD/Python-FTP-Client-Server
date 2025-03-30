from colorama import Fore
from enum import Enum
import os
import re
import socket
from typing import Tuple
import questionary


HOST                    = 'localhost'
PORT                    = 21
MAX_BUFFER_SIZE_CONTROL = 1024
MAX_BUFFER_SIZE_DATA    = 4096

client_socket           = None
data_socket             = None
is_connection_active    = False



class Command(Enum):
    LIST = "LIST"
    PWD  = "PWD"
    PASS = "PASS"
    PASV = "PASV"
    RETR = "RETR"
    STOR = "STOR"
    USER = "USER"
    QUIT = "QUIT"



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
        
        receive_control_response()
        
        is_authenticated = False
        response_status = "530"
        while is_authenticated == False and response_status == "530":
            is_authenticated, response_status = authenticate_user()
            questionary.press_any_key_to_continue("Press any key to Continue >").ask()
        
        if is_authenticated:
            run_communication()
    except ConnectionRefusedError:
        print(f"{Fore.RED}Error: Server is not available. Please try again later.{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}{Fore.RESET}")
    finally:
        client_socket.close()
        is_connection_active = False
    
    questionary.press_any_key_to_continue("Press any key to Continue >").ask()

def send_command(command: Command, arg: str = '') -> Tuple[str, str]:
    full_command = f"{command.name} {arg}\r\n"
    client_socket.sendall(full_command.encode())
    
    return receive_control_response()
    
def receive_control_response() -> Tuple[str, str]:
    response_status, response_msg = client_socket.recv(MAX_BUFFER_SIZE_CONTROL).decode().split(" ", 1)
    
    match response_status[0]:
        case "1": response_status_type = Fore.CYAN
        case "2": response_status_type = Fore.GREEN
        case "3": response_status_type = Fore.BLUE
        case "4": response_status_type = Fore.YELLOW
        case "5": response_status_type = Fore.RED
        case _  : response_status_type = Fore.WHITE
    
    print(f"Response:{response_status_type} {response_status} {response_msg}{Fore.RESET}")
    return response_status, response_msg

def parse_pasv_response(response):
    """Extract IP and port from the PASV response"""
    match = re.search(r"\((\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)", response)
    if match:
        ip = ".".join(match.groups()[:4])  # Convert (127,0,0,1) -> 127.0.0.1
        port = int(match.group(5)) * 256 + int(match.group(6))  # Convert (p1, p2) to integer
        return ip, port
    return None, None

def run_communication() -> None:
    while True:
        os.system('clear')
        
        answer = questionary.select(
            "Choose command",
            choices=[
                "1. Print working directory",
                "2. Change working directory",
                "3. List files and directories",
                "4. Create directory",
                "5. Remove directory",
                "6. Download file from the server",
                "7. Upload file to the server",
                "8. Delete file",
                "9. Close connection"
            ]
        ).ask()
        
        match answer:
            case "1. Print working directory":
                print_working_directory()
            case "3. List files and directories":
                list_directory()
            case "6. Download file from the server":
                download_file_from_server()
            case "7. Upload file to the server":
                upload_file_to_server()
            case "9. Close connection":
                close_connection()
                break
            case _:
                print(f"{Fore.YELLOW}Sorry, this command has not been implemented yet!{Fore.RESET}")
                
        questionary.press_any_key_to_continue("Press any key to Continue >").ask()

def open_data_connection() -> None:
    global data_socket
    
    _, response = send_command(Command.PASV)
    
    data_ip, data_port = parse_pasv_response(response)
    if not data_ip or not data_port:
        print(f"{Fore.RED}Failed to parse PASV response.{Fore.RESET}")
        return
    
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((data_ip, data_port))

def authenticate_user() -> Tuple[bool, str]:
    answers = questionary.form(
        input_username=questionary.text("Input username"),
        input_password=questionary.text("Input password")
    ).ask()
    
    response_user_command_status, _ = send_command(Command.USER, answers['input_username'])
    response_pass_command_status, _ = send_command(Command.PASS, answers['input_password'])
    
    if response_user_command_status != "331" or response_pass_command_status != "230":
        print(f"{Fore.RED}User failed to authenticated! Try again!{Fore.RESET}")
        return False, response_pass_command_status
    else:
        return True, response_pass_command_status

def print_working_directory() -> None:
    print("Send command to see current working directory")
    send_command(Command.PWD)

def list_directory() -> None:
    print("Send command to see files and directory in current working directory")
    
    open_data_connection()
    
    if data_socket == None:
        print(f"{Fore.RED}ERROR: Data connection can not be open{Fore.RESET}")
        return
    
    if data_socket.fileno() == -1:
        print(f"{Fore.RED}ERROR: Data connection is already closed{Fore.RESET}")
        return
    
    send_command(Command.LIST)
    
    directory_listing = data_socket.recv(MAX_BUFFER_SIZE_DATA).decode()
    print(directory_listing)
    
    data_socket.close()
    
    # Final response
    receive_control_response()

def download_file_from_server() -> None:
    file_name = questionary.text("Input file name").ask()
    
    open_data_connection()
    
    if data_socket == None:
        print(f"{Fore.RED}ERROR: Data connection can not be open{Fore.RESET}")
        return
    
    if data_socket.fileno() == -1:
        print(f"{Fore.RED}ERROR: Data connection is already closed{Fore.RESET}")
        return
    
    response_retr_command_status, _ = send_command(Command.RETR, file_name)
    
    if not response_retr_command_status == "150":
        client_socket.close()
        return
    
    
    new_file_name = questionary.text("Choose a new name for the downloaded file.").ask()
    
    with open(new_file_name, "wb") as file:
        while True:
            data = data_socket.recv(MAX_BUFFER_SIZE_DATA)
            if not data: break
            file.write(data)
    
    data_socket.close()
    
    # Final response
    receive_control_response()

def upload_file_to_server() -> None:
    file_path = questionary.text("Specify a file name to upload to the server (ABSOLUTE PATH)").ask()
    
    if not os.path.isfile(file_path):
        print(f"{Fore.RED}ERROR: File can not be found{Fore.RESET}")
        return
    
    file_name = os.path.basename(file_path)
    
    open_data_connection()
    
    if data_socket == None:
        print(f"{Fore.RED}ERROR: Data connection can not be open{Fore.RESET}")
        return
    
    if data_socket.fileno() == -1:
        print(f"{Fore.RED}ERROR: Data connection is already closed{Fore.RESET}")
        return
    
    response_status, _ = send_command(Command.STOR, file_name)
    
    if response_status != "150":
        return
    
    with open(file_path, "rb") as file:
        while chunk := file.read(MAX_BUFFER_SIZE_DATA):
            data_socket.sendall(chunk)
    
    data_socket.close()
        
    # Final response
    receive_control_response()

def close_connection() -> None:
    send_command(Command.QUIT)

def main() -> None:
    menu()

if __name__ == '__main__':
    main()