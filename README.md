# ReliableP2P
Building a reliable decentralized peer to peer file sharing platform with a database peer serving as a backup to all files shared.

Code references:
https://medium.com/@amannagpal4/how-to-create-your-own-decentralized-file-sharing-service-using-python-2e00005bdc4a

https://www.webcodegeeks.com/python/python-network-programming-tutorial/

Game references:

https://www.pythonforbeginners.com/games/

Protocol Keys:
    
    connect: 
        This is sent when a new node has entered the network. When the database server receives a message 
        containing connect, it knows to send out the peer list so that the new peer knows all the peers 
        in the network.

    disconnect:
        This will be sent when a node decides to leave the network. When a disconnect command is issued, the node first 
        attempts to reach all peers in peer list to notify them that it will no longer be available. If the node refuses 
        connection, it will be tried again, if it refuses connection again, it will be skipped and its peer_list will be 
        updated when another node joins the network. After this each peer will update their peer list removing the 
        disconnected node, and the disconnected node will terminate itself.
    
    update_peers:
        Sent by the database peer, this will be received by all peers in the network when a new peer joins notifying 
        them to update their list of active peers.

    get:
        Request made by peer in search of file. When a node receives a get request on the client side, if it has the 
        file the request is looking for, it will send it with a header titled file, if it does not have a file, then 
        it will send back its own address book to the peer titled map. When the peer that made the request receives 
        a file it will save it in its own specific directory titled port_<port no.>. When the peer that made the 
        request receives a map, it will merge the received hash map with its own to create a more up to date address 
        book keeping track of what peers have what file. This will increase speed in following searches as its map 
        of what nodes have what files is increased with every query. Therefore, the more queries a peer makes, the 
        faster it can find any file. The address book grows and the peer learns where to look as time goes on.
