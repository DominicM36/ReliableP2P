# ReliableP2P
Building a reliable decentralized peer to peer file sharing platform with a database peer serving as a backup to all files shared.

Code references:
https://medium.com/@amannagpal4/how-to-create-your-own-decentralized-file-sharing-service-using-python-2e00005bdc4a

https://www.webcodegeeks.com/python/python-network-programming-tutorial/

Game references:
https://www.pythonforbeginners.com/games/

MP3 References:
https://file-examples.com/index.php/sample-audio-files/sample-mp3-download/ 

https://qoret.com/outkast-hey-ya/ 

unclutter: 
    Each peer creates their own directory to store their files that they receive from the peer to peer
    file transfers ensuring that each file exists only to them unless requested. Unclutter is an 
    executable script to recursively remove the directories created for each peer.


How to run the code for the first time: 
    
    chmod 755 unclutter
    ./unclutter
    python3 peer.py

Getting Started:
    This project only runs locally currently. To run the code, you need to open multiple terminals and
    run `python3 peer.py` on them. One of these terminals will be the 'always-on' database peer on which you
    will set port number and the database port number to be the same. On the other 'peers', you will set 
    unique port numbers but the same database port number as the database peer. The database peer can be 
    left alone after this and can be minimized as no commands will be entered there. We recommend running
    at least 4 peers side by side to understand and test the workings in detail.
    
    The first command needed to be sent for each peer will be connect. After which any of the commands 
    outlined below can be used for various use cases.

Protocol Keys:
    
    connect: 
        This is sent when a new node has entered the network. When the database server receives a message 
        containing connect, it knows to send out the peer list so that the new peer knows all the peers 
        in the network. The database peer will also send out a list of all the trusted files so the node
        will not be able to query a file that the database peer does not know about from another peer.
        This will increase the security of the network, preventing nodes from sharing files "Behind
        the back" of the database peer.

    disconnect:
        This will be sent when a node decides to leave the network. When a disconnect command is issued, the node first 
        attempts to reach all peers in peer list to notify them that it will no longer be available. If the node refuses 
        connection, it will be tried again, if it refuses connection again, it will be skipped and its peer_list will be 
        updated when another node joins the network. After this each peer will update their peer list removing the 
        disconnected node, and the disconnected node will terminate itself.
    
    get:
        Request made by peer in search of file. When a node receives a get request on the client side, if it has the 
        file the request is looking for, it will send it with a header titled file, if it does not have a file, then 
        it will send back its own address book to the peer titled map. When the peer that made the request receives 
        a file it will save it in its own specific directory titled port_<port no.>. When the peer that made the 
        request receives a map, it will merge the received hash map with its own to create a more up to date address 
        book keeping track of what peers have what file. This will increase speed in following searches as its map 
        of what nodes have what files is increased with every query. Therefore, the more queries a peer makes, the 
        faster it can find any file. The address book grows and the peer learns where to look as time goes on.

    secure-get:
        This request acts similar to get, but with a specific port to retreive the file from. This would be used in 
        the case where a user would like to download a secure app from a trusted source, i.e. banking apps. Offering a
        trusted peer in the network and a way to directly access them for the application needed will help handle the 
        issue of security within a peer to peer network. The trusted peers can be given their role by the creator of
        the network, offering an admins approval. The addition of trusted peers makes the app more secure and safe
        for downloading files.

    list:
        This request prints out a list of files available for download within the network.

    address-book:
        This request will print out the peers address_book, allowing the user to see what 
        files it knows the locations of presented in a clean and readable format.

    seeding:
        This request will print out all the files the user has in its directory.

    Requests not made by user:
        map:
            Map is a request made by the peers and not by the user, when a peer receives a "map" request, it will
            send back its address book for the peer that requested an update. This is used to keep all the peers
            actively making requests up to date with which peers have which files, making their query faster the next
            time around. It benefits the user to make multiple get requests.
        
        update_peers:
            Sent by the database peer, this will be received by all peers in the network when a new peer joins notifying them to update their list of active peers.
