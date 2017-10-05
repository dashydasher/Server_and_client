# chat_server.py
 
import sys, socket, select, re

HOST = '' 
SOCKET_LIST = []
RECV_BUFFER = 4096 
PORT = 4321
USERS_DICT = {}

def chat_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
 
    # add server socket object to the list of readable connections
    SOCKET_LIST.append(server_socket)
 
    print("Server started on port " + str(PORT))
 
    while 1:

        # get the list sockets which are ready to be read through select
        # 4th arg, time_out  = 0 : poll and never block
        ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)
      
        for sock in ready_to_read:
            # a new connection request recieved
            if sock == server_socket: 
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)
                USERS_DICT[str(addr)] = "Guest" + str(len(USERS_DICT))

                print("Client " + str(addr) + " with nickname " + USERS_DICT[str(addr)] + " connected")
                send_message(sockfd, "[Server]: Connected to remote host with nickname " + USERS_DICT[str(addr)] + "\n")
                broadcast(server_socket, sockfd, "[Server]: " + USERS_DICT[str(addr)] + " connected\n")
             
            # a message from a client
            else:
                # receiving data from the socket.
                data = sock.recv(RECV_BUFFER).decode().strip()
                if data:
                    print(data)
                    # there is something in the socket
                    if data.startswith("//"):
                        # command in socket
                        if data[2:5] == "usr":
                            # usr command(//usr:newnick) - change nickname
                            if len(data[6:]) < 3 or len(data[6:]) > 20 or not re.match("^[A-Za-z0-9_-]*$", data[6:]):
                                send_message(sock, "Nickname must contain 3-20 letters or numbers\n")
                            elif data[6:] in USERS_DICT.values() or data[6:].lower() in "server":
                                send_message(sock, "Nickname already in use\n")
                            else:
                                send_message(sock, "Nickname changed to " + data[6:] + "\n")
                                broadcast(server_socket, sock, "[Server]: " + USERS_DICT[str(sock.getpeername())] + " changed nickname to " + data[6:] + "\n")
                                USERS_DICT[str(sock.getpeername())] = data[6:]
                        elif data[2:5] == "lst":
                            # lst command(//lst) - list all clients
                            msg = "List of connected users:\n"
                            for key, value in USERS_DICT.items():
                                msg += "\t" + value + "\n"
                            send_message(sock, msg)
                        else:
                            # invalid command
                            print("Invalid command: " + data)
                            send_message(sock, "Invalid command: " + data + "\n")
                    else:
                        # message in socket
                        broadcast(server_socket, sock, "[" + USERS_DICT[str(sock.getpeername())] + "]: " + data + "\n")
                else:
                    # remove the socket that's broken    
                    remove_user(sock)

                    # at this stage, no data means probably the connection has been broken
                    broadcast(server_socket, sock, "Client (%s, %s) is offline\n" % addr) 

    server_socket.close()






# broadcast chat messages to all connected clients
def broadcast (server_socket, sock, message):
    for socket in SOCKET_LIST:
        # send the message only to peer
        if socket != server_socket and socket != sock :
            try :
                socket.send(message.encode())
            except :
                # broken socket connection
                socket.close()
                # broken socket, remove it
                remove_user(sock)

# send message to specific user
def send_message (sock, message):
    try :
        sock.send(message.encode())
    except :
        # broken socket connection
        sock.close()
        # broken socket, remove it
        remove_user(sock)

# remove user from server
def remove_user (sock):
    print("Client " + str(sock.getpeername()) + " with nickname " + USERS_DICT[str(sock.getpeername())] + " disconnected")
    if sock in SOCKET_LIST:
        SOCKET_LIST.remove(sock)
    if str(sock.getpeername()) in USERS_DICT:
        USERS_DICT.pop(str(sock.getpeername()), None)

if __name__ == "__main__":

    sys.exit(chat_server())


