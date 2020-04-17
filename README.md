# ReliableP2P
Building a reliable decentralized peer to peer file sharing platform with a database peer serving as a backup to all files shared.

Code references:
https://medium.com/@amannagpal4/how-to-create-your-own-decentralized-file-sharing-service-using-python-2e00005bdc4a
https://www.webcodegeeks.com/python/python-network-programming-tutorial/

Protocol Keys:
    connect: 
        This is sent when a new node has entered the       
        network. When the database server receives a message containing connect, it knows to send out the peer list so that the new peer knows all the peers in the network.

    update_peers:
        Sent by the database peer, this will be received by all peers in the network when a new peer joins notifying them to update their list of active peers.