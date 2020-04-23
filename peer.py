import socket
import threading
import sys
import os
from random import seed, randint

ENCODING = 'utf-8'

my_host = 'localhost'

# host for the always on database peer, will be public IP if deployed
database_peer_host = 'localhost'
database_peer_port = 9000  # port for the always on database peer

# peerList only contains database peer to start with
peer_list = []
address_book = {}  # hash map with index as file name and a list of IPs and ports

# Server side
class Server(threading.Thread):

    def __init__(self, my_host, my_port):
        threading.Thread.__init__(self, name="messenger_receiver")
        self.host = my_host
        self.port = my_port

    def listen(self):
        global peer_list
        global database_peer_host
        global database_peer_port
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
                                        try:
                                            peer_socket.connect((peer[0], peer[1]))
                                        except socket.error as e:
                                            print('Connection refused by peer')
                                            peer_socket.close()
                                            continue
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
                        # disconnect request received by all peers
                        elif (msg[0] == 'disconnect'):
                            if('localhost', int(msg[1]) in peer_list):
                                print('Node ' + str(msg[1]) + ' disconnected')
                                peer_list.remove(('localhost', int(msg[1])))
                                print(peer_list)
                            else:
                                print('Disconnecting node not in network')
                        else:
                            print(full_message)
                            message = 'Command could not be executed'
                            print(message)

                        # print(peer_list)
                        break
            except Exception as e:
                print("Exception: " + str(e))
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
        global peer_list
        global address_book
        global database_peer_host
        global database_peer_port
        while True:
            message = input("Enter command: ")
            # Current peer leaving network
            if (message == 'disconnect'):
                message = message + ' ' + str(self.my_port)
                refused_peers = []  # List of peers that refused connection request
                for peer in peer_list:  # loop through all peers
                    print('Connecting to peer: ' + str(peer[1]))
                    if(peer[1] == self.my_port):
                        continue
                    try:
                        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        peer_socket.connect((peer[0], peer[1]))
                        print('Requesting: ' + message)
                        peer_socket.send(message.encode(ENCODING))
                        print('Sent request')
                        peer_socket.close()
                    except socket.error as e:
                        refused_peers.append(peer)  # add refused peer to list
                        print('Connection refused by: ' + peer + ' , trying again later...')

                for rpeer in refused_peers:
                    try:
                        refused_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        refused_socket.connect((rpeer[0], rpeer[1]))
                        print('Requesting: ' + message)
                        refused_socket.send(message.encode(ENCODING))
                        print('Sent request')
                        refused_socket.close()
                    except socket.error as e:
                        print('Connection refused by: ' + peer + ' a second time, ignoring')

                print("Leaving network...\n")
                # sys.exit()
                os.system('kill %d' % os.getpid()) #program kills itself
            elif(message == 'connect'):
                message = message + ' ' + str(self.my_port)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # For other requests to specific peers
                try:
                    s.connect((self.host, self.port))
                except socket.error as e:  # to handle connection refused case
                    print("Error connecting to peer: " + e)
                    s.close()
                    continue
                print('Requesting: ' + message)
                s.send(message.encode(ENCODING))
                print('Sent request')
                s.close()
            elif(message.split(' ')[0] == 'get'):
                message = message + ' ' + str(self.my_port)
                filename = message.split(' ')[1]
                done = False
                peers_to_query = peer_list.copy()
                peers_to_query.remove((database_peer_host, database_peer_port)) # database peer removed, should be force queried last since it is a back up option
                while (not done):
                    # Check if file exists in hash map
                    if(filename in address_book.keys()):
                        # If it exists, make a list of peers that have that file
                        peers_to_query = address_book[filename]
                        # Request randomly until file is received or list is exhausted
                        while(peers_to_query): # while peers to query is not empty
                            index = randint(0, len(peers_to_query) - 1) # pick an index in the list as a peer to query
                            peer_port = peers_to_query[index] # get port from list
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            # For other requests to specific peers
                            try: # make a request to a peer
                                s.connect((self.host, peer_port))
                            except socket.error as e:  # to handle connection refused case
                                print("Error connecting to peer: " + e)
                                s.close()
                                continue
                            print('Requesting: ' + message)
                            s.send(message.encode(ENCODING))
                            print('Sent request')

                            res = s.recv(1024)
                            rec_data = res
                            while(len(res) != 0):
                                res = s.recv(1024)
                                rec_data += res

                            rec_data = rec_data.decode(ENCODING)
                            if(rec_data.split(' ')[0] == 'file'): # file was received
                                # Store the file
                                to_write = rec_data[rec_data.index('\n\n') + 2:].encode(ENCODING) # get actual file data and then store it  
                                store_path = os.getcwd() + '/port_' + self.my_port + '/' + filename
                                try:
                                    file_pointer = open(store_path, 'wb')
                                except:
                                    print('Could not open file for download')
                                
                                if(file_pointer):
                                    file_pointer.write(to_write) # Encode the file to write the bytes when downloaded.
                            else:
                                print('Received response: ' + rec_data)

                            # Request Address Book from peer
                            req = 'map ' + str(self.my_port)
                            print('Requesting map')
                            s.send(message.encode(ENCODING))
                            print('Sent request')

                            res2 = s.recv(1024)
                            rec_data2 = res2
                            while(len(res2) != 0):
                                res2 = s.recv(1024)
                                rec_data2 += res2
                            rec_data2 = rec_data2.decode(ENCODING)
                            if(rec_data2.split(' ')[0] == 'map'): # file was received
                                # Parse the received map and update our address book
                                print('Received map: ' + rec_data2)
                                
                            s.close()
                            # Whenever we receive the file, also recieve the address book and merge
                            # as a secondary request in the same connection. Also, query database 
                            # peer at the end.
                        print()
                    else:
                        # If it doesn't exist, query a random peer from that list and request 
                        # the file in the same manner. Update address book. Go to top of loop if not found.
                        print()
                    
                    # If peers_to_query is empty, try querying database peer
                    print()
            else:
                print ("Invalid command, try connect, disconnect, or get")

def main():
    global database_peer_host
    global database_peer_port
    global peer_list
    global address_book
    my_port = int(input("Enter my port: "))
    database_peer_port = int(input("Enter database peer port: "))
    peer_list.append((database_peer_host, database_peer_port))
    
    # Database directory is 'db'
    # Create directory for this port
    path = 'port_' + str(my_port) # stores directory in form port_9000  
    try:
        os.mkdir(path)
    except Exception as e:
        # situation when directory already exists
        print ("Directory already exists for port: " + str(my_port))

    server = Server(my_host, my_port)
    client = Client(database_peer_host, database_peer_port, my_port)
    threads = [server.start(), client.start()]
    # print (threads) # display thread array

def update_address_book(peer_map, peer_port):
    global address_book
    for file_name in peer_map:
        if file_name in address_book.keys():
            # Update list of items
            if not peer_port in address_book[file_name]:
                # Add peer to address book
                address_book[file_name].append(peer_port)
        else:
            # File name doesn't exist in address book
            address_book[file_name] = [peer_port]

def parse_map(msg):
    # Parsing received address book from peer
    # Format: {(key1, [value 1, value2]), (key2, [value3])}
    print()

if __name__ == '__main__':
    main()
