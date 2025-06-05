import os
import hashlib

USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.txt')

def get_users():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            for line in f:
                if ':' in line:
                    user, pwd = line.strip().split(':', 1)
                    users[user] = pwd
    return users

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    users = get_users()
    return username in users and users[username] == hash_password(password)

def register_user(username, password):
    users = get_users()
    if username in users:
        return False
    with open(USERS_FILE, 'a') as f:
        f.write(f"{username}:{hash_password(password)}\n")
    return True 