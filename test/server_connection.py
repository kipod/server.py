""" TCP client connection.
"""
import json
import socket

from server.defs import Result
from server.game_config import CONFIG


class ServerConnection(object):
    """ Connection object.
    """

    ACTION_HEADER = 4
    RESULT_HEADER = 4
    MSGLEN_HEADER = 4
    RECEIVE_CHUNK_SIZE = 1024

    def __init__(self, host=CONFIG.SERVER_ADDR, port=CONFIG.SERVER_PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if host and port:
            self.connect(host, port)

    def connect(self, host, port):
        self.sock.connect((host, port))

    def close(self):
        self.sock.close()

    def send(self, message):
        total_sent = 0
        msg_len = len(message)
        while total_sent < msg_len:
            sent = self.sock.send(message[total_sent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            total_sent += sent

    def receive(self, msg_len):
        chunks = []
        bytes_recd = 0
        while bytes_recd < msg_len:
            chunk = self.sock.recv(min(msg_len - bytes_recd, self.RECEIVE_CHUNK_SIZE))
            if chunk == b'':
                raise RuntimeError("Socket connection broken")
            chunks.append(chunk)
            bytes_recd += len(chunk)
        return b''.join(chunks)

    def send_action(self, action: int, data=None, is_raw=False, wait_for_response=True):
        """ Sends action command.
        """
        self.send(action.to_bytes(self.ACTION_HEADER, byteorder='little'))
        if data is not None:
            if is_raw:
                message = data
            else:
                message = json.dumps(data, sort_keys=True, indent=4)
            self.send(len(message).to_bytes(self.MSGLEN_HEADER, byteorder='little'))
            self.send(message.encode('utf-8'))

        if wait_for_response:
            return self.read_response()
        else:
            return None, None

    def read_response(self):
        """ Returns action result with message as string.
        """
        data = self.receive(self.RESULT_HEADER)
        result = Result(int.from_bytes(data[:self.RESULT_HEADER], byteorder='little'))
        data = self.receive(self.MSGLEN_HEADER)
        msg_len = int.from_bytes(data[:self.MSGLEN_HEADER], byteorder='little')
        message = ''
        if msg_len != 0:
            data = self.receive(msg_len)
            message = data[:msg_len].decode('utf-8')
        return result, message
