import sys

from app.chat.session import ChatSession

def main():
    chat = ChatSession()
    chat.start()

if __name__ == "__main__":
    main()
