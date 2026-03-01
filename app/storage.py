import os

HISTORY_FILE = "chat_history.txt"

messages = []

def load_messages():
    global messages
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            messages = f.read().splitlines()
    else:
        messages = []
    return messages

def save_message(message):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")