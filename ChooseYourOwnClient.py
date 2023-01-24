# All of the processing code has now been pulled into this file - the network code remains in the other file Abstract...

from NetworkClient import Client
import threading

class abstractClient:
    def __init__(self, host="127.0.0.1", port=50000):
        self.client = Client(host, port)
        self.uiThread = threading.Thread(target=self.ui)
        self.running = True

    # Simple UI thread
    def ui(self):
        # Handle incoming messages from the server - at the moment that is simply "display them to the user"
        while self.running:
            message = self.client.getMessage()
            if message:
                print(message)

    def process(self):
        # Start the UI thread and start the network components
        self.uiThread.start()
        self.client.process()
        try:
            while self.running:
                message = input("Please enter a command: ")
                self.client.pushMessage(message)

                if message == "Quit":
                    self.running = False
        except:
            print("Error occurred...")
        # stop the network components and the UI thread
        self.client.quit()
        self.uiThread.join()

if __name__ == "__main__":
    game_running = True
    while game_running:
        user_input = input("Enter the IP Address of the Escape the Dungeon Server: ")
        if user_input.lower() == "quit":
            print("Quiting Game.")
            game_running = False
            break
        client = abstractClient(user_input, 50001)
        client.process()
