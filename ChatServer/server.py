import socket
import select
import re
import threading
import sys

HEADER = 64
IP = socket.gethostbyname(socket.gethostname())
PORT = 1234
FORMAT = "utf-8"
MAX_CLIENTS = 64

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((IP, PORT))

user_list = {}
conn_list = {}

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")
    print(conn)
    connected = True
    try:
        while connected:
            client_message = conn.recv(1024).decode(FORMAT)
            while not client_message.endswith("\n"):
                client_message += conn.recv(1024).decode(FORMAT)
            print(f"[{addr}] {client_message[:-1]}")
            if (threading.active_count() - 1) >= MAX_CLIENTS:
                conn.sendall("BUSY\n".encode(FORMAT)) 
                connected = False
            elif re.match(r"HELLO-FROM", client_message):
                handshake = re.search(r"HELLO-FROM ([\w\.-]+)", client_message)
                client_username = handshake.group(1)
                if client_username in user_list.keys(): # Checks used username
                    conn.sendall("IN-USE\n".encode(FORMAT))
                    print(f"[{addr}] IN-USE")
                    connected = False
                else:
                    user_list[client_username] = conn
                    conn.sendall(f"HELLO {client_username}\n".encode(FORMAT))
                    print(f"[{addr}] HELLO {client_username}")
            elif client_message == "!quit\n":
                connected = False
                del user_list[client_username ]
                print(f"[DISCONNECTED] {addr} disconnected")
            elif re.match(r"WHO", client_message):
                who_response = "WHO-OK"
                for user, conns in user_list.items():
                    who_response += f" {user}"
                conn.sendall(f"{who_response}\n".encode(FORMAT))
                print(f"[{addr}] {who_response}")
            elif re.match(r"SEND", client_message):
                convo_match = re.search(r"SEND ([\w\.-]+) ([\w\s]+)", client_message)
                try:
                    recipient = convo_match.group(1)
                    sender = client_username
                    msg = convo_match.group(2)[:-1]
                    if recipient not in user_list.keys():
                        conn.sendall(f"UNKNOWN\n".encode(FORMAT))
                        print(f"[{addr}] UNKNOWN")
                    else:
                        r_conn = user_list[recipient]
                        r_conn.sendall(f"DELIVERY {sender} {msg}\n".encode(FORMAT))
                        conn.sendall(f"SEND-OK\n".encode(FORMAT))
                except Exception as ex:
                    connected = False
    except Exception as ex:
        print("We out")
        conn.close()
    conn.close()

def start():
    server_socket.listen()
    print(f"[LISTENING] Server is listening on IP: {IP} and PORT: {PORT}")
    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

print("[STARTING] server is starting...")
start()
