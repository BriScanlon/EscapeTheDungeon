import errno
import socket
import threading
import queue
import time
import os
from Crypto.PublicKey import RSA

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
        self.client_public_key_file = None

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
            self.server_private_key = RSA.generate(2048)
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

    def hasClient(self):
        return self.client

    def write(self):
        print("Write thread started")
        while self.writing:
            if not self.running and self.oBuffer.empty():
                self.writing = False
            if not self.oBuffer.empty():
                try:
                    self.conn.sendall(self.oBuffer.get().encode("utf-8"))
                    #message = self.oBuffer.get()
                    #encrypted_message = self.client_public_key.encrypt(message, 32)[0]
                    #self.conn.sendall(encrypted_message)
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
                        data = self.conn.recv(1024)

                        # Decode the message and put it into the incoming message buffer to be processed
                        if data:
                            message = data.decode("utf-8")
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

    def process(self):
        # start the reading, writing and ui threads
        self.readThread.start()
        self.writeThread.start()


if __name__=="__main__":
    server = Server("127.0.0.1", 50001)
    server.process()
    