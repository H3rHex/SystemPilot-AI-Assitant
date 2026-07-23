import sys

from dotenv import load_dotenv
from app.chat.session import ChatSession

def main():
    load_dotenv()
    chat = ChatSession()
    chat.start()

if __name__ == "__main__":
    main()
