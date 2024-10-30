import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def add_user(email, password):
    hashed_password = generate_password_hash(password)  # Hash the password
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        return False  # User already exists
    finally:
        conn.close()
    return True

def get_user(email):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)
