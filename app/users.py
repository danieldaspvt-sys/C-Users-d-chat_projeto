users = {}

def register_user(username):
    if username in users:
        return False
    users[username] = {
        "username": username
    }
    return True

def user_exists(username):
    return username in users