import errno
import socket
import threading
import queue
import time
import os

import pickle
from Crypto.PublicKey import RSA

from base64 import b64encode, b64decode
from Crypto.Cipher import ChaCha20


class Server:
    def __init__(self, host="127.0.0.1", port=50000):
        self.HOST = host
        self.PORT = port
        self.iBuffer = queue.Queue()
        self.oBuffer = queue.Queue()

        self.running = True
        self.writing = True
        self.reading = True
        self.processing = True

        # single connection and address variables - single client only
        self.conn = None
        self.addr = None
        self.client = False

        # initialise the public private key pair
        self.server_public_key_file = "server_public.pem"
        self.server_private_key_file = "server_private.pem"
        self.server_public_key = None
        self.server_private_key = None
        self.client_public_key = None
        self.client_public_key_file = "client_public.pem"

        self.cipher_key = b"12345678901234561234567890123456"
        self.cipher = ChaCha20.new(key=self.cipher_key)

        # Create threads
        self.readThread = threading.Thread(target=self.read)
        self.writeThread = threading.Thread(target=self.write)

    def get_ip(self):
        hostname, aliases, ips = socket.gethostbyname_ex(socket.gethostname())
        return ips

    def generate_keys(self):
        print("Checking if keys exist...")
        # check to see if a private & public key pair exist
        if not os.path.exists(self.server_private_key_file):
            self.server_private_key = RSA.generate(4096)
            self.server_public_key = self.server_private_key.public_key()
            # save the private key to file
            with open(self.server_private_key_file, "wb") as f:
                f.write(self.server_private_key.exportKey())
            # save the public key to file
            with open(self.server_public_key_file, "wb") as f:
                f.write(self.server_public_key.exportKey())
            print("Key pair generated and saved to files")
        else:
            with open(self.server_private_key_file, "rb") as f:
                self.server_private_key = RSA.importKey(f.read())
            with open(self.client_public_key_file, "rb") as f:
                self.client_public_key = RSA.importKey(f.read())

    def hasClient(self):
        return self.client

    def write(self):
        print("Write thread started")
        while self.writing:
            if not self.running and self.oBuffer.empty():
                self.writing = False
            if not self.oBuffer.empty():
                try:
                    # self.conn.sendall(self.oBuffer.get().encode("utf-8"))
                    message = self.oBuffer.get()
                    plaintext = bytes(message, "utf-8")
                    self.cipher = ChaCha20.new(key=self.cipher_key)
                    nonce = b64encode(self.cipher.nonce).decode("utf-8")
                    ciphertext = self.cipher.encrypt(plaintext)
                    ct = b64encode(ciphertext).decode("utf-8")
                    to_send = {"nonce": nonce, "ciphertext": ct}
                    serialized_dict = pickle.dumps(to_send)
                    self.conn.sendall(serialized_dict)
                    time.sleep(0.1)
                except socket.error as e:
                    pass


    def read(self):
        print("Read thread started")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Socket binding to actual IP address/Port combination
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.HOST, self.PORT))

            # Set socket to listen for incoming connections, then block waiting for a connection
            s.listen()
            self.conn, self.addr = s.accept()
            self.client = True
            # When a client connection is accepted
            with self.conn:
                self.conn.setblocking(False)
                print(f"Connected by {self.addr}")

                while self.reading:
                    # Program has stopped running - self terminate and close the socket.
                    if not self.running:
                        self.reading = False
                        break

                    # attempt to read data from the socket:
                    try:
                        messageDump = self.conn.recv(2048)
                        if messageDump:
                            message = pickle.loads(messageDump)
                            nonce = b64decode(message["nonce"])
                            ciphertext = b64decode(message["ciphertext"])
                            self.cipher = ChaCha20.new(key=self.cipher_key, nonce=nonce)
                            plaintext = self.cipher.decrypt(ciphertext)
                            message = plaintext.decode("utf-8")
                            self.iBuffer.put(message)

                    # Handle errors that come from the socket
                    except socket.error as e:
                        err = e.args[0]
                        # No data on socket, but socket still exists - wait and retry
                        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                            time.sleep(0.1)
                        else:
                            # an actual error has occurred, shut down the program as our sole client is now disconnected
                            self.running = False
                            self.conn.shutdown(socket.SHUT_RDWR)

    def process(self):
        # check IP address
        ip = self.get_ip()
        print(f"Escape the dungeon Server IP Address(s) is: {ip}\nUse this to connect from your Escape the dungeon Client\n")
        # check for or generate keys
        self.generate_keys()
        # start the reading and writing threads
        self.readThread.start()
        self.writeThread.start()

    def getMessage(self):
        if not self.iBuffer.empty():
            return self.iBuffer.get()
        else:
            return None

    def pushMessage(self, message):
        self.oBuffer.put(message)

    def quit(self):
        self.running = False
        self.readThread.join()
        self.writeThread.join()


if __name__=="__main__":
    server = Server("127.0.0.1", 50001)
    server.process()
    