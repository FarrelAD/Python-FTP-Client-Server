# Python FTP Client-Server

A simple FTP client and server built in Python using the `socket` module as the core networking tool. This implementation follows the **passive mode** FTP approach, where the client initiates all connections. Passive mode is commonly used because it is more firewall and NAT-friendly.

## Features 🪁

This custom FTP implementation includes several standard FTP commands and functionalities:

1. **USER** and **PASS** – Authentication with username and password.
2. **PWD** – Print the current working directory.
3. **LIST** – List files and directories in the server.
4. **RETR** – Download files from the server.
5. **STOR** – Upload files to the server.
6. **QUIT** – Close the connection.

## How It Works ⚒️

This DIY FTP server follows the standard FTP protocol specifications. It establishes two types of connections between the client and server:

1. **Control Connection** – Handles command transmission and responses between the client and server.
2. **Data Connection** – Used for transferring files and directory listings between the client and server.

Since this FTP implementation operates in **passive mode**, the client is responsible for initiating the data connection, making it more suitable for use behind firewalls and NAT configurations.

## Demo 🚗

https://github.com/user-attachments/assets/931ec438-29cc-4a33-98d9-0b69a3d2f7a5


## Notes 📝

This FTP server was developed and tested on a **Windows** environment. Cross-platform compatibility is not guaranteed due to potential limitations in Python's networking modules on different operating systems.

## Contributions 🫱🏻‍🫲🏻

Contributions are welcome! Feel free to submit issues, feature requests, or pull requests to improve this project. 😊

