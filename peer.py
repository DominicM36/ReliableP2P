import socket
import threading

ENCODING = 'utf-8'

my_host = 'localhost'

# host for the always on database peer, will be public IP if deployed
database_peer_host = 'localhost'
database_peer_port = 8000  # port for the always on database peer

# peerList only contains database peer to start with
peer_list = []
directory = {}  # hash map with index as file name and a list of IPs and ports

# Server side


class Server(threading.Thread):

    def __init__(self, my_host, my_port):
        threading.Thread.__init__(self, name="messenger_receiver")
        self.host = my_host
        self.port = my_port

    def listen(self):
        global peer_list
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, self.port))
        sock.listen(10)
        while True:
            connection, client_address = sock.accept()  # store client IP as client address
            print("Accepted connection from: " + str(client_address))
            try:
                full_message = ""
                done = 0
                while done == 0:
                    #print("Test message")
                    data = connection.recv(1024)
                    full_message = full_message + data.decode(ENCODING)
                    #print("Test message 2")
                    if not data or len(data) < 1024:
                        print("{}: {}".format(
                            client_address, full_message.strip()))
                        # Only for database peer connection case when a new peer joins network
                        # Contains 'connect port_number'
                        msg = full_message.split()
                        done = 1

                        # if the server receives a connection request from a client for the peer list
                        if(msg[0] == 'connect'):
                            # if not in list, append node to list
                            if(not ('localhost', int(msg[1])) in peer_list):
                                peer_list.append(('localhost', int(msg[1])))
                                # notify all peers in list
                                for peer in peer_list:
                                    if peer[1] != self.port:
                                        peer_socket = socket.socket(
                                            socket.AF_INET, socket.SOCK_STREAM)
                                        peer_socket.connect((peer[0], peer[1]))
                                        message_to_send = "update_peers\n" + \
                                            str(peer_list)
                                        peer_socket.send(
                                            message_to_send.encode())
                                        peer_socket.close()
                        elif (msg[0] == 'update_peers'):
                            # Update peer list
                            print("Updating peer list")
                            list_of_strings = full_message.strip().split('\n')[1].strip('][').strip(')(').split('), (') #split into ('host', port)
                            new_peer_list = []
                            for item in list_of_strings:
                                pair = item.split(', ')
                                new_peer_list.append((pair[0].strip('\''), int(pair[1])))
                            peer_list = new_peer_list.copy() # peer list is now updated
                        else:
                            print(full_message)
                            message = 'Command could not be executed'
                            print(message)

                        # print(peer_list)
                        break
            except Exception as e:
                print("Exception: " + e)
            finally:
                # connection.shutdown(2)
                connection.close()

    def run(self):
        self.listen()

# Client side


class Client(threading.Thread):

    def __init__(self, my_friends_host, my_friends_port, my_port):
        threading.Thread.__init__(self, name="messenger_sender")
        self.host = my_friends_host
        self.port = my_friends_port
        self.my_port = my_port

    def run(self):
        while True:
            message = input("Enter command: ")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))

            if(message == 'connect'):
                message = message + ' ' + str(self.my_port)

            print('Requesting: ' + message)
            s.send(message.encode(ENCODING))
            print('Sent request')
            s.close()


def main():
    my_port = int(input("Enter my port: "))
    database_peer_port = int(input("Enter database peer port: "))
    peer_list.append((database_peer_host, database_peer_port))
    server = Server(my_host, my_port)
    client = Client(database_peer_host, database_peer_port, my_port)
    threads = [server.start(), client.start()]
    # send a message to database peer requesting all the peers in the list
    # connect my_port

    # Send a message to all peers to update their peer lists


if __name__ == '__main__':
    main()
