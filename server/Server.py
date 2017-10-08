"""
Game server
"""
import socket
import sys

SERVER_PORT = 1973

class Server(object):
    """
    TCP/IP simple server (https://pymotw.com/2/socket/tcp.html)
    """
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        """ starts server
        """
        server_address = ('localhost', SERVER_PORT)
        print >>sys.stderr, 'starting up on %s port %s' % server_address
        self.socket.bind(server_address)
        # Listen for incoming connections
        self.socket.listen(1)
        while True:
            # Wait for a connection
            print >>sys.stderr, 'waiting for a connection'
            connection, client_address = self.socket.accept()
            try:
                print >>sys.stderr, 'connection from', client_address

                # Receive the data in small chunks and retransmit it
                while True:
                    data = connection.recv(16)
                    print >>sys.stderr, 'received "%s"' % data
                    if data:
                        print >>sys.stderr, 'sending data back to the client'
                        connection.sendall(data)
                    else:
                        print >>sys.stderr, 'no more data from', client_address
                        break
                    
            finally:
                # Clean up the connection
                connection.close()

if __name__ == '__main__':
    server = Server()
    server.start()
