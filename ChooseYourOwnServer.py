from NetworkServer import Server
from Book import Book
from Page import Page
from Option import Option
import time


class ChooseYourOwnServer:
    def __init__(self, host="127.0.0.1", port=50000):
        self.server = Server(host, port)

        # Variables dealing with state management and state functionality
        self.book = Book()
        self.running = True

    def constructBook(self, title=None):
        if not title:
            page1 = Page(1, """Page 1
            =================Escape the Dungeon!===================
            You awake.  Finally.  With a sense of increasing dread and fear, you cannot remember anything
            that came before this moment.  All you know is that you are lying on a cool, dry stone floor.
            You sit up and look around.  Your in a square room around 5 metres square.  The floor is made of well
            fitting, smooth flagstones. The walls are of large stone blocks, the same material as the floor.
            There is a crude, wooden table in the middle of the room with a number of objects on it.
            There appear to be two exits, one in front of you, which you guess at being towards the north and one to
            left of you, maybe towards the east.
            """)
            page2 = Page(2, """Page 2
            =================The Crude Table===================
            
            """)
            page3 = Page(3, "The Third page")

            page1.add_option(Option(2, "Examine the table, move to page 2"))
            page1.add_option(Option(3, "Go through the north door, move to page 3"))
            page1.add_option(Option(4, "Go through the east door, move to page 4"))
            page2.add_option(Option(3, "Move to the third page"))
            page3.add_option(Option(1, "Move to the first page"))


            self.book.add_page(page1)
            self.book.add_page(page2)
            self.book.add_page(page3)
        else:
            page1 = Page(1, "The first page")
            page2 = Page(2, "The second page")
            page3 = Page(3, "The Third page")

            page1.add_option(Option(2, "Move to the second page"))
            page1.add_option(Option(3, "Move to the third page"))
            page2.add_option(Option(3, "Move to the third page"))
            page3.add_option(Option(1, "Move to the first page"))

            self.book.add_page(page1)
            self.book.add_page(page2)
            self.book.add_page(page3)

    def process(self):
        self.server.process()
        self.constructBook()

        # Termination condition to handle the program shutting down

        while not self.server.hasClient():
            time.sleep(1)

        while self.running:
            # only attempt to process a message if there is a message in the incoming message buffer
            self.server.pushMessage(self.book.read_current_page())
            validChoice = False

            while not validChoice:
                message = self.server.getMessage()
                if message:
                    if message == "Quit":
                        message = "Acknowledge quitting"
                        self.running = False
                        validChoice = True

                    try:
                        value = int(message)
                        if self.book.option_exists(value):
                            validChoice = True
                            message = self.book.action_option(str(value))
                    except ValueError:
                        message = "Error, input must be an integer"
                    self.server.pushMessage(message)

        self.server.quit()


if __name__=="__main__":
    server = ChooseYourOwnServer("127.0.0.1", 50001)
    server.process()
