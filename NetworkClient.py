
import socket
import errno
import time
import threading
import queue
from Crypto.PublicKey import RSA
import os

class Client:
    def __init__(self, host="127.0.0.1", port=50000):
        self.HOST = host
        self.PORT = int(port)
        self.iBuffer = queue.Queue()
        self.oBuffer = queue.Queue()

        self.running = True
        self.writing = True
        self.reading = True
        self.processing = True

        self.conn = None

        self.server_public_key_file = "server_public.pem"
        self.server_public_key = None
        self.client_public_key = None
        self.client_private_key = None
        self.client_private_key_file = "client_private.pem"
        self.client_public_key_file = "client_public.pem"

        # Create threads
        self.readThread = threading.Thread(target=self.read)
        self.writeThread = threading.Thread(target=self.write)

    def generate_keys(self):
        # check to see if a private & public key pair exist
        if not os.path.exists(self.client_private_key_file):
            self.client_private_key = RSA.generate(2048)
            self.client_public_key = self.client_private_key.public_key()
            # save the private key to file
            with open(self.client_private_key_file, "wb") as f:
                f.write(self.client_private_key.exportKey())
            # save the public key to file
            with open(self.client_public_key_file, "wb") as f:
                f.write(self.client_public_key.exportKey())
            print("Key pair generated and saved to files")
        else:
            with open(self.client_private_key_file, "rb") as f:
                self.client_private_key = RSA.importKey(f.read())

    def write(self):
        print("Write thread started")
        while self.writing:
            if not self.running and self.oBuffer.empty():
                self.writing = False
            if not self.oBuffer.empty():
                self.conn.sendall(self.oBuffer.get().encode("utf-8"))
                time.sleep(0.1)

    def read(self):
        print("Read thread started")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.conn:
            self.conn.connect((self.HOST, self.PORT))
            self.conn.setblocking(False)

            while self.reading:
                # Program has stopped running - self terminate and close the socket.
                if not self.running:
                    self.reading = False
                    break

                # attempt to read data from the socket:
                try:
                    data = self.conn.recv(1024)
                    if data:
                        message = data.decode("utf-8")
                        self.iBuffer.put(message)

                # Handle errors that come from the socket
                except socket.error as e:
                    err = e.args[0]
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                        time.sleep(0.1)
                    else:
                        self.running = False
                        self.conn.shutdown(socket.SHUT_RDWR)

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
        # check for or generate keys
        self.generate_keys()
        # start the reading, writing and ui threads
        self.readThread.start()
        self.writeThread.start()


if __name__ == "__main__":
    client = Client("127.0.0.1", 50001)
    client.process()
