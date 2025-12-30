import sqlite3
import random
import string
import bcrypt
from core.database import init_db, add_user, get_user

def generate_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def seed_data():
    print("Initializing database...")
    init_db()

    # 1. Root Admin
    print("Creating Root Admin...")
    if not get_user("root"):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw("root123".encode('utf-8'), salt)
        add_user("root", hashed.decode('utf-8'), "RootAdmin", 1)
        print("Root Admin created: root / root123")
    else:
        print("Root Admin already exists.")

    # 2. Admins (2)
    print("Creating Admins...")
    for i in range(1, 3):
        username = f"admin{i}"
        if not get_user(username):
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(f"admin{i}".encode('utf-8'), salt)
            add_user(username, hashed.decode('utf-8'), "Admin", 1)
            print(f"Admin created: {username} / {username}")
        else:
            print(f"Admin {username} already exists.")

    # 3. Doctors (15)
    print("Creating Doctors...")
    for i in range(1, 16):
        username = f"doc{i}"
        if not get_user(username):
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(f"doc{i}".encode('utf-8'), salt)
            # Approve first 10, leave 5 pending
            is_approved = 1 if i <= 10 else 0
            add_user(username, hashed.decode('utf-8'), "Doctor", is_approved)
            print(f"Doctor created: {username} / {username} (Approved: {is_approved})")
        else:
            print(f"Doctor {username} already exists.")

    # 4. Users (100)
    print("Creating Users...")
    for i in range(1, 101):
        username = f"user{i}_{generate_random_string(4)}"
        if not get_user(username):
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw("user123".encode('utf-8'), salt)
            # Approve first 90, leave 10 pending
            is_approved = 1 if i <= 90 else 0
            add_user(username, hashed.decode('utf-8'), "User", is_approved)
            # Print only every 10th user to avoid clutter
            if i % 10 == 0:
                print(f"User created: {username} / user123 (Approved: {is_approved})")
        else:
            print(f"User {username} already exists.")

    print("Seeding complete.")

if __name__ == "__main__":
    seed_data()
