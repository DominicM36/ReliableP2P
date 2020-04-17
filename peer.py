import socket
import threading
 
ENCODING = 'utf-8'

my_host = 'localhost'

database_peer_host = 'localhost' # host for the always on database peer, will be public IP if deployed
database_peer_port = 8000 # port for the always on database peer

peer_list = [{database_peer_host, database_peer_port}] # peerList only contains database peer to start with
directory = {} # hash map with index as file name and a list of IPs and ports

# Server side
class Server(threading.Thread):
 
    def __init__(self, my_host, my_port):
        threading.Thread.__init__(self, name="messenger_receiver")
        self.host = my_host
        self.port = my_port
 
    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, self.port))
        sock.listen(10)
        while True:
            connection, client_address = sock.accept() #store client IP as client address
            try:
                full_message = ""
                while True:
                    data = connection.recv(1024)
                    
                    # Only for database peer connection case when a new peer joins network
                    msg = data.decode(ENCODING).split() # Contains 'connect port_number'
                    if(msg[0] == 'connect'): # if the server receives a connection request from a client for the peer list
                        peer_list.push({client_address, msg[1]})
                        connection.sendall(peer_list.encode(ENCODING)) # send all of the peer list to the client to keep it updated
                        break
                    
                    # full_message = full_message + data.decode(ENCODING)
                    # if not data:
                    #     print("{}: {}".format(client_address, full_message.strip()))
                    #     break
            finally:
                #connection.shutdown(2)
                connection.close()
 
    def run(self):
        self.listen()
 
# Client side 
class Client(threading.Thread):
 
    def __init__(self, my_friends_host, my_friends_port):
        threading.Thread.__init__(self, name="messenger_sender")
        self.host = my_friends_host
        self.port = my_friends_port
 
    def run(self):
        while True:
            message = input("")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.sendall(message.encode(ENCODING))

            data = s.recv(1024)
            rec = data # chunk received
            while(len(rec) != 0):
                rec = s.recv(1024)
                data += rec #append next chunk to data

            print('Client received data:\n') #data received in JSON format to be decoded and used
            print(data.decode())

            #s.shutdown(2)
            s.close()
 
 
def main():
    my_port = int(input("which is my port? "))
    server = Server(my_host, my_port)
    client = Client(database_peer_host, database_peer_port)
    threads = [server.start(), client.start()]
    # send a message to database peer requesting all the peers in the list
    # connect my_port
    
    # Send a message to all peers to update their peer lists
 
 
if __name__ == '__main__':
    main()