import socket
import threading
import sys
import os
from random import seed, randint

ENCODING = 'utf-8'

my_host = 'localhost' # IP of the computer hosting peer to peer server, local host for the scope of this class
connected = False

db_files = []

# host for the always on database peer, will be public IP if deployed
database_peer_host = 'localhost'
database_peer_port = 9000  # port for the always on database peer

# peerList only contains database peer to start with
peer_list = []
address_book = {}  # hash map with index as file name and a list of IPs and ports

# Server side
class Server(threading.Thread):

    def __init__(self, my_host, my_port):
        threading.Thread.__init__(self, name="server")
        self.host = my_host
        self.port = my_port

    def listen(self):
        global peer_list
        global db_files
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
                done = False
                while not done:
                    data = connection.recv(1024)
                    full_message = full_message + data.decode(ENCODING)
                    if not data or len(data) < 1024:
                        print("{}: {}".format(
                            client_address, full_message.strip()))
                        # Only for database peer connection case when a new peer joins network
                        # Contains 'connect port_number'
                        msg = full_message.split()
                        done = True

                        # if the server receives a connection request from a client for the peer list
                        if(msg[0] == 'connect'):
                            # if not in list, append node to list
                            if(not ('localhost', int(msg[1])) in peer_list):
                                # Send back list of files in network to connected peer
                                connection.send((str(db_files)).encode(ENCODING))

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
                        elif(msg[0] == 'get'):
                            # Send back file if exists else send back map
                            print('Received get request')
                            # Check if file exists
                            if self.port == database_peer_port:
                                # filename = os.getcwd() + '/db/' + msg[1]
                                filename = 'db/' + msg[1]
                            else:
                                # filename = os.getcwd() + '/port_' + self.port + '/' + msg[1]
                                filename = 'port_' + str(self.port) + '/' + msg[1]

                            print('filename: ' + filename)
                            try:
                                f = open(filename, 'rb')
                            except FileNotFoundError:
                                print('Requested file was not found. Sending back map.')
                                res = 'map\n\n' + str(address_book)
                                connection.send(res.encode(ENCODING))
                            else:
                                # if()
                                # file_map = {(filename, [(self.host, int(msg[2]))])}
                                # update_address_book(file_map)
                                # Send back file
                                response_body_raw = f.read()
                                f.close()
                                response_body = 'file\n\n'
                                response_body = response_body.encode() + response_body_raw
                                # print(response_body)
                                connection.send(response_body)
                                print('File sent.')
                            
                        elif(msg[0] == 'map'):
                            # Send back map
                            print('Sending map')
                            res = 'map\n\n' + str(address_book)
                            #{(key1, [value1, value2]), (key2, [value3])}
                            connection.send(res.encode(ENCODING))

                        else:
                            print(full_message)
                            message = 'Command could not be executed'
                            print(message)
                            connection.send(('Invalid command.').encode(ENCODING))

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

    def __init__(self, my_friends_host, my_friends_port, my_host, my_port):
        threading.Thread.__init__(self, name="client")
        self.host = my_friends_host
        self.port = my_friends_port
        self.my_port = my_port
        self.my_host = my_host

    def run(self):
        global db_files
        global peer_list
        global address_book
        global database_peer_host
        global database_peer_port
        global connected

        while True:
            print(address_book)
            message = input("Enter command: ")
            if(not connected and message != 'connect'):
                print('Please connect to the network first by typing \'connect\'')
                continue
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
                connected = False
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
                connected = True

                # Receives db files
                data = s.recv(1024)
                res = data
                while(len(data) != 0):
                    data = s.recv(1024)
                    res += data

                files_str = res.decode(ENCODING)
                files_str = files_str.strip('[]\'').split('\', \'')
                for dbfile in files_str:
                    db_files.append(dbfile)

                # print(files_str)
                print('db: ' + str(db_files))

                s.close()
            elif(message.split(' ')[0] == 'secure-get'): # Get ran on certain secure and trusted port. To be used with applications such as banking, trust this distributor wont alter files
                secure_port = message.split(' ')[2] # Stores secure port number
                secure_filename = message.split(' ')[1] # stores secure filename
                message = 'get ' + secure_filename + ' ' + str(self.my_port)
                if(not secure_filename in db_files):
                    print('Invalid file ' + secure_filename + ' requested. Please try again.')
                    continue
                
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect(self.host, secure_port)
                except socket.error as e:
                    print('Error connecting to peer: ' + str(e))
                    s.close()
                    continue
                print('Requesting data: ' + message)
                s.send(message.encode(ENCODING))
                
                res = s.recv(1024)
                rec_data = res
                while(len(res) != 0):
                    res = s.recv(1024)
                    rec_data += res

                s.close()

                split_data = rec_data.split()
                if(split_data[0].decode(ENCODING) == 'file'): # file was received
                    print('Writing to file')
                    # Update current map to reflect that I have the file as well as the peer I got it from
                    file_map = {}
                    file_map[secure_filename] = [(self.my_host, self.my_port)]
                    update_address_book(file_map)
                    # Store the file
                    write_to_file(rec_data, secure_filename, self.my_port)
                else:
                    print('Received response: ' + str(rec_data))
                
            elif(message.split(' ')[0] == 'get'):
                
                file_not_received = True

                print('In get')
                message = message + ' ' + str(self.my_port)
                filename = message.split(' ')[1]
                if(not filename in db_files):
                    print('Invalid file ' + filename + ' requested. Please try again.')
                    continue
                done = False
                peers_to_query = peer_list.copy()
                peers_to_query.remove((database_peer_host, database_peer_port)) # database peer removed, should be force queried last since it is a back up option
                peers_to_query.remove((self.my_host, self.my_port)) # remove self
                while (len(peers_to_query) > 0 and not done):
                    print('In while loop')
                    # Check if file exists in hash map
                    # If the map contains the filename and also the peer itself is not the only peer in the list for that file
                    not_only_self = filename in address_book.keys() and not (len(address_book[filename]) == 1 and address_book[filename][0] == (self.my_host, self.my_port))

                    if(not_only_self):
                        # If it exists, make a list of peers that have that file
                        print('File is in map')
                        peers_to_query = address_book[filename]
                        if((self.my_host, self.my_port) in peers_to_query):
                            peers_to_query.remove((self.my_host, self.my_port)) # remove self
                        # Request randomly until file is received or list is exhausted
                        while(peers_to_query): # while peers to query is not empty
                            index = randint(0, len(peers_to_query) - 1) # pick an index in the list as a peer to query
                            peer_pair = peers_to_query[index] # get host-port pair from list
                            del peers_to_query[index]
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            # For other requests to specific peers
                            try: # make a request to a peer
                                s.connect(peer_pair)
                            except socket.error as e:  # to handle connection refused case
                                print("Error connecting to peer: " + str(e))
                                s.close()
                                continue
                            print('Requesting: ' + message)
                            s.send(message.encode(ENCODING))
                            print('Sent request to pair: ' + str(peer_pair))

                            res = s.recv(1024)
                            rec_data = res
                            while(len(res) != 0):
                                res = s.recv(1024)
                                rec_data += res

                            split_data = rec_data.split()
                            if(split_data[0].decode(ENCODING) == 'file'): # file was received
                                print('Writing to file')
                                # Update current map to reflect that I have the file as well as the peer I got it from
                                file_map = {}
                                file_map[filename] = [(self.my_host, self.my_port)]
                                update_address_book(file_map)
                                # Store the file
                                write_to_file(rec_data, filename, self.my_port)
                                file_not_received = False
                            else:
                                print('Received response: ' + str(rec_data))

                            s.close()
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            try: # make a request to a peer
                                s.connect(peer_pair)
                            except socket.error as e:  # to handle connection refused case
                                print("Error connecting to peer: " + str(e))
                                s.close()
                                continue

                            # Request Address Book from peer
                            req = 'map ' + str(self.my_port)
                            print('Requesting map')
                            s.send(req.encode(ENCODING))
                            print('Sent request')

                            # Whenever we receive the file, also recieve the address book and merge
                            # as a secondary request in the same connection.
                            res2 = s.recv(1024)
                            rec_data2 = res2
                            while(len(res2) != 0):
                                res2 = s.recv(1024)
                                rec_data2 += res2
                            rec_data2 = rec_data2.decode(ENCODING)
                            if(rec_data2.split('\n')[0] == 'map'): # file was received
                                # Parse the received map and update our address book
                                map_to_parse = rec_data2[rec_data2.index('\n\n') + 2:]
                                print('Received map: ' + map_to_parse)
                                returned_map = parse_map(map_to_parse)
                                print('Parsed map: ' + str(returned_map))
                                update_address_book(returned_map)
                                
                            s.close()
                            done = True
                            break

                        # Also, query database peer at the end.
                        # Only want file from database, hashmap here will be way out of date due to the way the address book is designed to update
                        if(not done):
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            # For other requests to specific peers
                            try: # make a request to a peer
                                s.connect((database_peer_host, database_peer_port))
                            except socket.error as e:  # to handle connection refused case
                                print("Error connecting to database: " + str(e))
                                s.close()
                                done = True
                                continue
                            print('Requesting: ' + message)
                            s.send(message.encode(ENCODING))
                            print('Sent request')

                            res = s.recv(1024)
                            rec_data = res
                            while(len(res) != 0):
                                res = s.recv(1024)
                                rec_data += res

                            split_data = rec_data.split()
                            if(split_data[0].decode(ENCODING) == 'file'): # file was received
                                file_map = {}
                                file_map[filename] = [(self.my_host, self.my_port)]
                                update_address_book(file_map)
                                # Store the file
                                write_to_file(rec_data, filename, self.my_port)
                                file_not_received = False
                            else:
                                print('Received response: ' + str(rec_data))
                            
                        done = True
                    else:
                        # If it doesn't exist, query a random peer from that list and request 
                        # the file in the same manner. Update address book. Go to top of loop if not found.
                        index = randint(0, len(peers_to_query) - 1)
                        peer_pair = peers_to_query[index] # get host-port pair from list
                        del peers_to_query[index] # Remove from peers to query list to avoid duplicate queries of the same peer
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        
                        # For other requests to specific peers
                        try: # make a request to a peer
                            s.connect(peer_pair)
                            
                        except socket.error as e:  # to handle connection refused case
                            print("Error connecting to peer: " + str(e))
                            s.close()
                            continue
                        print('Requesting: ' + message)
                        s.send(message.encode(ENCODING))
                        print('Sent request to peer: ' + str(peer_pair))

                        res = s.recv(1024)
                        rec_data = res
                        while(len(res) != 0):
                            res = s.recv(1024)
                            rec_data += res

                        split_data = rec_data.split()
                        if(split_data[0].decode(ENCODING) == 'file'): # file was received
                            print('Writing to file')
                            # Update current map to reflect that I have the file as well as the peer I got it from
                            file_map = {}
                            file_map[filename] = [(self.my_host, self.my_port)]
                            update_address_book(file_map)
                            # Store the file
                            write_to_file(rec_data, filename, self.my_port)
                            file_not_received = False

                            s.close()
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            try: # make a request to a peer
                                s.connect(peer_pair)
                            except socket.error as e:  # to handle connection refused case
                                print("Error connecting to peer: " + str(e))
                                s.close()
                                done = True
                                continue
                            
                            # Request Address Book from peer
                            req = 'map ' + str(self.my_port)
                            print('Requesting map')
                            s.send(req.encode(ENCODING))
                            print('Sent request')

                            # Whenever we receive the file, also recieve the address book and merge
                            # as a secondary request in the same connection.
                            res2 = s.recv(1024)
                            rec_data2 = res2
                            while(len(res2) != 0):
                                res2 = s.recv(1024)
                                rec_data2 += res2
                            rec_data2 = rec_data2.decode(ENCODING)
                            
                            if(rec_data2.split('\n')[0] == 'map'): # file was received
                                # Parse the received map and update our address book
                                map_to_parse = rec_data2[rec_data2.index('\n\n') + 2:]
                                
                                # Print received map here for debugging
                                print('Received map: ' + map_to_parse)

                                returned_map = parse_map(map_to_parse)
                                print('Parsed map: ' + str(returned_map))
                                update_address_book(returned_map)
                            
                            s.close()
                            done = True
                        elif(split_data[0].decode(ENCODING) == 'map'):
                            # Parse the received map and update our address book
                            decoded_string = rec_data.decode(ENCODING)
                            map_to_parse = decoded_string[decoded_string.index('\n\n') + 2:]

                            # Print received map here for debugging
                            print('Received map: ' + map_to_parse)

                            returned_map = parse_map(map_to_parse)
                            print('Parsed map: ' + str(returned_map))
                            update_address_book(returned_map)
                        else:
                            # Invalid request
                            print('Received Response: ' + str(rec_data))
                    
                # If peers_to_query is empty, try querying database peer
                if(len(peers_to_query) == 0 and not done):
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    
                    # For other requests to specific peers
                    try: # make a request to a peer
                        s.connect((database_peer_host, database_peer_port))
                    except socket.error as e:  # to handle connection refused case
                        print("Error connecting to database: " + str(e))
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

                    split_data = rec_data.split()
                    
                    if(split_data[0].decode(ENCODING) == 'file'): # file was received
                        # Store the file
                        print('Writing to file')
                        # Update current map to reflect that I have the file as well as the peer I got it from
                        file_map = {}
                        file_map[filename] = [(self.my_host, self.my_port)]
                        update_address_book(file_map)
                        write_to_file(rec_data, filename, self.my_port)
                        file_not_received = False
                    else:
                        print('Received response: ' + str(rec_data))

                    done = True

                if(file_not_received):
                    print('All peers busy. Try again later.')
            else:
                print ("Invalid command, try connect, disconnect, or get")

            


def update_address_book(peer_map):
    global address_book
    for file_name in peer_map:
        if file_name in address_book.keys():
            # Update list of items
            for peer in peer_map[file_name]:
                if not peer in address_book[file_name]:
                    address_book[file_name].append(peer)
        else:
            # File name doesn't exist in address book
            address_book[file_name] = peer_map[file_name]


def parse_map(msg):
    # Taking in a message, parse out the important values in order to create a datastructure to return.
    # Parsing received address book from peer
    # Format: {'key1': [('ip1', port1), ('ip2', port2)], 'key2': [('ip3', port3)]}
    map_to_return = {} # map with form {filename, list of pairs}

    if(msg == "{}"):
        print("Empty map returned")
        # Return empty map before trying to parse
        return map_to_return 
    
    parse = msg.strip('{}()]') # Remove braces and parenthesis at the end of string
    map_values = parse.split('], ') #split into a list of chunks. These chunks are seperated by the difference in keys

    for i in map_values:
        
        current_keys = i.split(': [') # seperate the key and the list of pairs in the string
        # i = i.strip(']')
        key = current_keys[0].strip('\'')
        print("current key is " + key)
        string_list = current_keys[1]
        print(string_list)
        
        pair_as_strings = string_list.strip('()').split('), (')
        
        list_of_pairs = [] # Used to push a pair to this list
        
        for pair in pair_as_strings:
            pair_details = pair.split(', ') # get actual values from the pairs
            
            # Create values for each component of the pair
            pair_part_1 = pair_details[0].strip('\'')
            pair_part_2 = int(pair_details[1])

            # Create a pair to push to the list using previously found details
            pair_to_add = (pair_part_1, pair_part_2)

            print("Pair to be added: " + str(pair_to_add))

            # Add the pair to the list using append
            list_of_pairs.append(pair_to_add)

        map_to_return[key] = list_of_pairs # set the list of nodes to key of filename
    
    return map_to_return 


def write_to_file(data, filename, port):
    to_write = data[data.index(('\n\n').encode()) + 2:] # get actual file data and then store it  
    # store_path = os.getcwd() + '/port_' + port + '/' + filename
    store_path = 'port_' + str(port) + '/' + filename
    try:
        if(os.path.exists(store_path)):
            os.chmod(store_path, 0o755)
        file_pointer = open(store_path, 'wb')
    except:
        print('Could not open file for download')
        file_pointer = None
                            
    if(file_pointer):
        file_pointer.write(to_write) # Encode the file to write the bytes when downloaded.
        os.chmod(store_path, 0o555)
        file_pointer.close()


def main():
    global my_host
    global database_peer_host
    global database_peer_port
    global peer_list
    global address_book
    global db_files
    my_port = int(input("Enter my port: "))
    database_peer_port = int(input("Enter database peer port: "))
    peer_list.append((database_peer_host, database_peer_port))
    if(my_port == database_peer_port):
        # Get list of files in db
        db_files = [f for f in os.listdir('db/') if os.path.isfile(os.path.join('db/', f)) and f[0] != '.']
        # for f in db_files:
        #     if(f[0] == '.'):
        #         db_files.remove(f)
        print('Database files: ' + str(db_files))
    
    else:
        # Database directory is 'db'
        # Create directory for this port
        path = 'port_' + str(my_port) # stores directory in form port_9000  
        try:
            os.mkdir(path)
            # os.chmod(path, 0o500)
        except Exception as e:
            # situation when directory already exists
            print ("Directory already exists for port: " + str(my_port))

    server = Server(my_host, my_port)
    client = Client(database_peer_host, database_peer_port, my_host, my_port)
    threads = [server.start(), client.start()]
    # print (threads) # display thread array


if __name__ == '__main__':
    main()
